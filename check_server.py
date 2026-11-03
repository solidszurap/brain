"""
Quick checks of Ember's server (a few seconds, no network, no LLM, nothing real
touched): the real server on a random local port, with a fake mind, fake logins,
a FileStore in a temporary folder, and a small fake Supabase for SupabaseStore and
SupabaseAuth. Run after changing server/ or web/:

    python check_server.py
"""
import json
import logging
import os
import re
import socket
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import uvicorn

from mind import llm
from server.app import CAPPED, FAILED, UNREACHABLE, create_app
from server.auth import NotInvited, NotLoggedIn, SupabaseAuth
from server.store import FileStore, SupabaseStore

logging.getLogger("ember").setLevel(logging.CRITICAL)
failed = []


def check(name, ok, detail=""):
    print(("  ok    " if ok else "  FAIL  ") + name + (f"  ({detail})" if detail and not ok else ""))
    if not ok:
        failed.append(name)


def free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


def serve(app):
    port = free_port()
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="critical"))
    threading.Thread(target=server.run, daemon=True).start()
    for _ in range(200):
        if server.started:
            break
        time.sleep(0.02)
    return f"http://127.0.0.1:{port}", server


def call(base, path, token=None, body=None, header=True):
    h = {"Content-Type": "application/json"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    if body is not None and header:
        h["X-Ember"] = "1"
    req = urllib.request.Request(base + path, data=json.dumps(body).encode() if body is not None else None,
                                 headers=h, method="POST" if body is not None else "GET")
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status, json.loads(r.read() or b"null")
    except urllib.error.HTTPError as e:
        return e.code, None


def wait(cond, timeout=6.0):
    end = time.time() + timeout
    while time.time() < end:
        if cond():
            return True
        time.sleep(0.03)
    return False


# ------------------------------------------------------------------ fakes
class FakeAuth:
    mode = "online"
    users = {"tok-a": {"id": "user-a", "email": "a@x.hu"}, "tok-b": {"id": "user-b", "email": "b@x.hu"}}

    def user(self, token):
        if token == "tok-x":
            raise NotInvited("x@x.hu")
        if token not in self.users:
            raise NotLoggedIn()
        return self.users[token]


class FakeCfg:
    provider, usable, problem, last_usage = "fake", True, None, None

    def describe(self):
        return "fake mind"


class FakeMind:
    def __init__(self):
        self.fail, self.retryable, self.calls = 0, True, 0

    def __call__(self, cfg, system, user, json_mode=False):
        self.calls += 1
        if self.fail > 0:
            self.fail -= 1
            raise llm.LLMError("fake trouble", retryable=self.retryable)
        cfg.last_usage = (3000, 200)
        m = re.search(r'Their latest message: "(.*)"', user)
        if not m:
            return json.dumps({"reply": "Hello again.", "face": "happy"})
        said = m.group(1)
        return json.dumps({"reply": f"I heard: {said}", "face": "curious",
                           "remember": [{"kind": "about", "note": said[:60], "quote": said}]})


T = [1_800_000_000.0]
clock = lambda: T[0]
tmp = tempfile.mkdtemp(prefix="ember_check_")
store = FileStore(os.path.join(tmp, "users"))
mind = FakeMind()
base, srv = serve(create_app(store, FakeAuth(), FakeCfg(), call=mind, clock=clock,
                             retry_delay=0.01, retry_every=0.3))


def state(tok, v=1):
    return call(base, f"/state?v={v}", tok)[1]


def ember_lines(tok):
    return [l["text"] for l in state(tok, 0)["talk"] if l["who"] == "ember"]


print("Who may use it")
check("no login: refused", call(base, "/state")[0] == 401)
check("not on the invite list: refused", call(base, "/state", "tok-x")[0] == 403)
check("a POST without Ember's header: refused", call(base, "/talk", "tok-a", {"text": "hi"}, header=False)[0] == 403)
check("the window, manifest and service worker are served",
      all(urllib.request.urlopen(base + p).status == 200 for p in ("/", "/manifest.webmanifest", "/sw.js", "/privacy")))
check("config says online", call(base, "/config")[1]["mode"] == "online")

print("Each person has their own Ember")
state("tok-a")
check("a first visit gets a greeting", wait(lambda: ember_lines("tok-a") == ["Hello again."]))
call(base, "/talk", "tok-a", {"text": "I love drawing"})
check("you talk, it answers from what you said", wait(lambda: "I heard: I love drawing" in ember_lines("tok-a")))
check("...and remembers it, with your words", call(base, "/memory", "tok-a")[1]["count"] == 1)
check("another person's Ember knows nothing of it",
      call(base, "/memory", "tok-b")[1]["count"] == 0 and "I love drawing" not in json.dumps(state("tok-b", 0)))
check("it's saved: self and every line", wait(lambda: os.path.exists(os.path.join(tmp, "users", "user-a", "ember.json"))
                                              and len(store.lines("user-a")) >= 3))
check("usage is counted per day", store.calls_today("user-a", time.strftime("%Y-%m-%d", time.gmtime(T[0]))) >= 2)

print("Real time")
n = len(ember_lines("tok-a"))
T[0] += 2 * 3600
check("two hours away, then back: it greets you", (state("tok-a") or True) and wait(lambda: len(ember_lines("tok-a")) == n + 1))
check("a poll a second later is no new greeting", (state("tok-a") or True) and not wait(lambda: len(ember_lines("tok-a")) > n + 1, 0.5))

print("When the mind is busy or down")
mind.fail, mind.retryable = 3, True
call(base, "/talk", "tok-a", {"text": "are you there"})
check("it says honestly that its mind can't be reached", wait(lambda: ember_lines("tok-a")[-1] == UNREACHABLE))
T[0] += 1
check("...and answers once the mind is back", wait(lambda: ember_lines("tok-a")[-1] == "I heard: are you there"))
check("...saying 'can't be reached' only once", ember_lines("tok-a").count(UNREACHABLE) == 1)
mind.fail, mind.retryable = 1, False
call(base, "/talk", "tok-a", {"text": "something odd"})
check("a mind error that won't go away: it says so, no fake answer", wait(lambda: ember_lines("tok-a")[-1] == FAILED))

print("Experiments still work through the server")
for s in ("I code for hours", "I want to make a game"):
    call(base, "/talk", "tok-a", {"text": s})
wait(lambda: "I heard: I want to make a game" in ember_lines("tok-a"))
st = state("tok-a", 0)
check("enough memories to suggest", st["can_suggest"], str(st["memories"]))

print("The daily limit")
store2 = FileStore(os.path.join(tmp, "users2"))
base2, srv2 = serve(create_app(store2, FakeAuth(), FakeCfg(), call=FakeMind(), clock=clock, daily_cap=2,
                               retry_delay=0.01, retry_every=0.3))
call(base2, "/state?v=1", "tok-b")
for s in ("one", "two", "three"):
    call(base2, "/talk", "tok-b", {"text": s})
lines2 = lambda: [l["text"] for l in call(base2, "/state", "tok-b")[1]["talk"] if l["who"] == "ember"]
check("past the limit it says so instead of thinking", wait(lambda: lines2()[-1:] == [CAPPED]), str(lines2()))
srv2.should_exit = True

print("Your data")
status, data = call(base, "/me/export", "tok-a")
check("download everything: self and the whole conversation",
      status == 200 and data["ember"]["memories"] and len(data["conversation"]) >= 6)
check("deleting needs Ember's header", call(base, "/me/delete", "tok-a", {}, header=False)[0] == 403)
check("delete my Ember", call(base, "/me/delete", "tok-a", {})[0] == 200)
check("...afterwards a fresh Ember, remembering nothing", call(base, "/memory", "tok-a")[1]["count"] == 0)
check("...and on this computer the old one is archived, not destroyed",
      any("deleted_user-a" in d for d in os.listdir(os.path.join(tmp, "users", "archive"))))
srv.should_exit = True

print("After a restart, unanswered words get answered")
store3 = FileStore(os.path.join(tmp, "users3"))
from mind.core import Ember
e = Ember(now=T[0])
e.hear(T[0], "hello before the restart")
store3.save_self("user-b", e.to_dict())
base3, srv3 = serve(create_app(store3, FakeAuth(), FakeCfg(), call=FakeMind(), clock=clock,
                               retry_delay=0.01, retry_every=0.3))
check("it answers what was left unanswered",
      wait(lambda: any(l["text"] == "I heard: hello before the restart" for l in call(base3, "/state", "tok-b")[1]["talk"])))
srv3.should_exit = True


# ------------------------------------------------------------------ fake Supabase
class Fake(BaseHTTPRequestHandler):
    tables = {"embers": [], "lines": [], "usage": []}
    keys = {"embers": ("user_id",), "usage": ("user_id", "day")}
    deleted_users = []

    def log_message(self, *a):
        pass

    def _send(self, code, body=None):
        raw = json.dumps(body).encode() if body is not None else b""
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def _parse(self):
        u = urllib.parse.urlparse(self.path)
        q = dict(urllib.parse.parse_qsl(u.query))
        return u.path, q

    def _match(self, rows, q):
        f = {k: v[3:] for k, v in q.items() if v.startswith("eq.")}
        return [r for r in rows if all(str(r.get(k)) == v for k, v in f.items())]

    def do_GET(self):
        path, q = self._parse()
        if path == "/auth/v1/user":
            tok = self.headers.get("Authorization", "")[7:]
            return self._send(200, {"id": "sb-1", "email": "Me@X.hu"}) if tok == "good" else self._send(401, {})
        if self.headers.get("apikey") != "service":
            return self._send(401, {})
        rows = self._match(self.tables[path.split("/")[-1]], q)
        if "order" in q:
            rows = sorted(rows, key=lambda r: r[q["order"].split(".")[0]])
        rows = rows[int(q.get("offset", 0)):][:int(q.get("limit", 10 ** 9))]
        if "select" in q and q["select"] != "*":
            rows = [{k: r.get(k) for k in q["select"].split(",")} for r in rows]
        self._send(200, rows)

    def do_POST(self):
        path, q = self._parse()
        table = path.split("/")[-1]
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        for row in body if isinstance(body, list) else [body]:
            rows = self.tables[table]
            key = self.keys.get(table)
            old = [r for r in rows if key and all(r.get(k) == row.get(k) for k in key)]
            if old and "merge-duplicates" in self.headers.get("Prefer", ""):
                old[0].update(row)
            else:
                rows.append(dict(row))
        self._send(201)

    def do_DELETE(self):
        path, q = self._parse()
        if path.startswith("/auth/v1/admin/users/"):
            self.deleted_users.append(path.rsplit("/", 1)[1])
            return self._send(200, {})
        table = path.split("/")[-1]
        keep = [r for r in self.tables[table] if r not in self._match(self.tables[table], q)]
        self.tables[table][:] = keep
        self._send(204)


print("SupabaseStore and SupabaseAuth (against a fake Supabase)")
fs = ThreadingHTTPServer(("127.0.0.1", 0), Fake)
threading.Thread(target=fs.serve_forever, daemon=True).start()
url = f"http://127.0.0.1:{fs.server_address[1]}"
sb = SupabaseStore(url, "service")
check("nothing there at first", sb.load_self("u1") is None)
sb.save_self("u1", {"memories": [1]})
sb.save_self("u1", {"memories": [1, 2]})
check("saving twice updates the one row", sb.load_self("u1") == {"memories": [1, 2]} and len(Fake.tables["embers"]) == 1)
sb.append_lines("u1", [{"t": 2.0, "who": "ember", "text": "b", "exps": ["x1"]}, {"t": 1.0, "who": "you", "text": "a"}])
check("lines come back in order, extras intact",
      sb.lines("u1") == [{"t": 1.0, "who": "you", "text": "a"}, {"t": 2.0, "who": "ember", "text": "b", "exps": ["x1"]}])
sb.add_call("u1", "2026-11-03", 3000, 200)
sb.add_call("u1", "2026-11-03", 1000, 100)
check("usage adds up per day", sb.calls_today("u1", "2026-11-03") == 2 and Fake.tables["usage"][0]["tokens_in"] == 4000)
check("all users listed", sb.all_uids() == ["u1"])
check("export has everything", sb.export("u1")["ember"] == {"memories": [1, 2]} and len(sb.export("u1")["conversation"]) == 2)
sb.delete_user("u1")
check("delete removes every row and the login", not any(Fake.tables.values()) and Fake.deleted_users == ["u1"])
auth = SupabaseAuth(url, "anon", allowed="me@x.hu, friend@x.hu")
check("a valid login on the invite list is let in (email case ignored)", auth.user("good")["id"] == "sb-1")
try:
    SupabaseAuth(url, "anon", allowed="friend@x.hu").user("good")
    check("someone not invited is refused", False)
except NotInvited:
    check("someone not invited is refused", True)
try:
    auth.user("bad")
    check("a bad token is refused", False)
except NotLoggedIn:
    check("a bad token is refused", True)
check("invite list * lets everyone in", SupabaseAuth(url, "anon", allowed="*").user("good")["email"] == "me@x.hu")
fs.shutdown()

print()
print("All checks passed." if not failed else f"{len(failed)} FAILED: {failed}")
sys.stdout.flush()
os._exit(1 if failed else 0)                   # the servers' threads don't need a clean shutdown
