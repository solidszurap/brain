"""
Quick checks of Ember's server (a few seconds, no network, no LLM, nothing real
touched): the real server on a random local port, with a fake mind, fake logins,
a FileStore in a temporary folder, and a small fake Supabase for SupabaseStore and
SupabaseAuth. Run after changing server/ or web/:

    python check_server.py
"""
import calendar
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
from server.app import CAPPED, FAILED, PLUS_ENDED, PLUS_ON, UNREACHABLE, create_app
from server.auth import LocalAuth, NotInvited, NotLoggedIn, SupabaseAuth
from server.store import FileStore, StoreError, SupabaseStore

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
        self.fail, self.retryable, self.calls, self.garble = 0, True, 0, 0

    def __call__(self, cfg, system, user, json_mode=False):
        self.calls += 1
        self.last = user
        if self.fail > 0:
            self.fail -= 1
            raise llm.LLMError("fake trouble", retryable=self.retryable)
        if self.garble > 0:                        # an answer that isn't readable JSON
            self.garble -= 1
            return '{"reply": "oops, "broken'
        cfg.last_usage = (3000, 200)
        if "Look back on it honestly" in user:
            return json.dumps({"reply": "Looking back: " + re.search(r"What actually happened: (.*)", user).group(1)[:80]})
        if "Our month" in user:
            return json.dumps({"reply": "A month of small steps."})
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
                             retry_delay=0.01, retry_every=0.3, plus_emails=("a@x.hu", "b@x.hu")))


def state(tok, v=1):
    return call(base, f"/state?v={v}", tok)[1]


def ember_lines(tok):
    return [l["text"] for l in state(tok, 0)["talk"] if l["who"] == "ember"]


print("Who may use it")
check("no login: refused", call(base, "/state")[0] == 401)
check("not on the invite list: refused", call(base, "/state", "tok-x")[0] == 403)
check("a POST without Ember's header: refused", call(base, "/talk", "tok-a", {"text": "hi"}, header=False)[0] == 403)
check("the window, manifest and service worker are served",
      all(urllib.request.urlopen(base + p).status == 200 for p in ("/", "/home", "/manifest.webmanifest", "/sw.js", "/privacy", "/terms")))
check("config says online", call(base, "/config")[1]["mode"] == "online")

print("The website")
def get_page(path, accept="text/html"):
    try:
        with urllib.request.urlopen(urllib.request.Request(base + path, headers={"Accept": accept})) as r:
            return r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()
site = {p: get_page(p) for p in ("/home", "/features", "/pricing", "/faq", "/about", "/privacy", "/terms")}
check("every page of the website is served, with the header and footer put in",
      all(st == 200 and 'class="nav"' in html and 'class="foot"' in html and "<!--#" not in html for st, html in site.values()))
check("...and the header marks the page you're on", 'href="/pricing" aria-current="page"' in site["/pricing"][1]
      and 'aria-current' not in site["/faq"][1].split('href="/pricing"')[1][:20])
check("the styles, the script and the screenshots are served",
      all(urllib.request.urlopen(base + p).status == 200 for p in ("/site.css", "/site.js", "/img/shot-talk.webp", "/img/og.png")))
def ranged(path, rng):
    with urllib.request.urlopen(urllib.request.Request(base + path, headers={"Range": rng})) as r:
        return r.status, r.headers.get("Content-Range") or "", r.headers.get("Content-Type"), len(r.read())
st, cr, ct, n = ranged("/img/ember-demo.mp4", "bytes=0-99")
check("the front page's demo video is served in pieces when asked (iPhones only play video that way)",
      st == 206 and n == 100 and cr.startswith("bytes 0-99/") and ct == "video/mp4", f"{st} {cr} {ct} {n}")
check("...and the front page shows it, with its poster",
      'src="/img/ember-demo.mp4"' in site["/home"][1] and urllib.request.urlopen(base + "/img/ember-demo-poster.webp").status == 200)
check("a picture that isn't there, or a path outside the folder: not found",
      get_page("/img/nope.webp", "*/*")[0] == 404 and get_page("/img/..%5Cserver%5Capp.py", "*/*")[0] == 404)
check("a page that isn't there: the website's own page, for a browser", get_page("/nowhere")[0] == 404
      and "This page isn't here" in get_page("/nowhere")[1])
check("...and the usual short answer for anything else", get_page("/nowhere", "application/json") == (404, '{"detail":"Not Found"}'))
check("a sitemap with every page, and robots.txt pointing to it",
      all(f"https://yourember.app{p}<" in get_page("/sitemap.xml", "*/*")[1] for p in site)
      and "Sitemap: https://yourember.app/sitemap.xml" in get_page("/robots.txt", "*/*")[1])
front = get_page("/")[1]
check("online, the window is marked so in its first line, and sends a stranger to the front page before it draws anything",
      '<html lang="en" data-mode="online">' in front
      and front.index('location.replace("/home")') < front.index("<style>") < front.index("<body"))
local_dir = os.path.join(tmp, "local")
basel, _ = serve(create_app(FileStore(local_dir, fixed=local_dir), LocalAuth(), FakeCfg(), call=FakeMind(), clock=clock))
local_page = urllib.request.urlopen(basel + "/").read().decode()
check("...but Ember on this computer has no front page: its window isn't marked",
      '<html lang="en">' in local_page and 'data-mode="online">' not in local_page)
check("...nor Cloudflare's visit counter: nothing from this computer is counted",
      "cloudflareinsights" not in local_page and "cloudflareinsights" not in urllib.request.urlopen(base + "/home").read().decode())
basea, _ = serve(create_app(FileStore(os.path.join(tmp, "analytics")), FakeAuth(), FakeCfg(), call=FakeMind(), clock=clock,
                            analytics_token="tok123"))
pages = {p: urllib.request.urlopen(basea + p).read().decode() for p in ("/", "/home", "/pricing", "/privacy")}
check("online, every page (the app and the website) counts visits with Cloudflare Web Analytics, once",
      all(h.count('data-cf-beacon=\'{"token": "tok123"}\'') == 1 and h.index("cloudflareinsights") < h.index("</body>")
          for h in pages.values()), [p for p, h in pages.items() if "tok123" not in h])
check("...and the privacy page says so", "Cloudflare Web Analytics" in pages["/privacy"])

print("Each person has their own Ember")
state("tok-a")
check("a first visit gets a greeting", wait(lambda: ember_lines("tok-a") == ["Hello again."]))
call(base, "/talk", "tok-a", {"text": "I love drawing"})
check("you talk, it answers from what you said", wait(lambda: "I heard: I love drawing" in ember_lines("tok-a")))
check("...and remembers it, with your words", call(base, "/memory", "tok-a")[1]["count"] == 1)
check("a brand-new person can ask for ideas right away", call(base, "/experiment/suggest", "tok-b", {})[1]["ok"]
      and wait(lambda: all(x["starter"] for x in state("tok-b", 0)["suggestions"]) and state("tok-b", 0)["suggestions"]))
check("another person's Ember knows nothing of it",
      call(base, "/memory", "tok-b")[1]["count"] == 0 and "I love drawing" not in json.dumps(state("tok-b", 0)))
check("it's saved: self and every line", wait(lambda: os.path.exists(os.path.join(tmp, "users", "user-a", "ember.json"))
                                              and len(store.lines("user-a")) >= 3))
check("usage is counted per day", store.calls_today("user-a", time.strftime("%Y-%m-%d", time.gmtime(T[0]))) >= 2)

print("Real time")
n = len(ember_lines("tok-a"))
T[0] += 2 * 3600
check("two hours away, then back: it lights up, but doesn't write", (state("tok-a") or True)
      and not wait(lambda: len(ember_lines("tok-a")) > n, 0.5))
T[0] += 8 * 3600
check("ten hours away, then back: it greets you", (state("tok-a") or True) and wait(lambda: len(ember_lines("tok-a")) == n + 1))
check("a poll a second later is no new greeting", (state("tok-a") or True) and not wait(lambda: len(ember_lines("tok-a")) > n + 1, 0.5))

print("Our month: a note when a new month begins")
TM = [calendar.timegm((2027, 1, 20, 9, 0, 0))]
basem, _ = serve(create_app(FileStore(os.path.join(tmp, "months")), FakeAuth(), FakeCfg(), call=FakeMind(),
                            clock=lambda: TM[0], plus_emails=("a@x.hu",)))
mlines = lambda: [l["text"] for l in call(basem, "/state?v=0", "tok-a")[1]["talk"] if l["who"] == "ember"]
for k in range(2):                                   # two days you talked with it in January
    TM[0] += k * 86400
    call(basem, "/talk", "tok-a", {"text": f"day {k}"})
    wait(lambda: any(f"day {k}" in x for x in mlines()))
n_lines = len(mlines())
TM[0] = calendar.timegm((2027, 2, 1, 10, 0, 0))
st = call(basem, "/state?v=1", "tok-a")[1]
check("the first visit in February brings its note on January, kept on its page",
      wait(lambda: (call(basem, "/memory", "tok-a")[1].get("months") or [{}])[0].get("text") == "A month of small steps.")
      and call(basem, "/memory", "tok-a")[1]["months"][0]["name"] == "January 2027")
check("...instead of a greeting, and never as a chat line", not wait(lambda: len(mlines()) > n_lines, 0.5))
check("...and the window hears it's there", call(basem, "/state?v=0", "tok-a")[1]["month_latest"] == "2027-01")
TM[0] += 12 * 3600
call(basem, "/state?v=1", "tok-a")
check("...once", len(call(basem, "/memory", "tok-a")[1]["months"]) == 1)

print("Deleting a chat or a goal")
dstore = FileStore(os.path.join(tmp, "deleting"))
based, _ = serve(create_app(dstore, FakeAuth(), FakeCfg(), call=FakeMind(), clock=clock, plus_emails=("a@x.hu",)))
ng = call(based, "/goal/new", "tok-a", {"title": "Swim", "days": 14, "steps": ["Find a pool"]})[1]
call(based, "/talk", "tok-a", {"text": "the pool opens at 7", "chat": ng["chat"]})
wait(lambda: any(l.get("chat") == ng["chat"] and l["who"] == "ember" for l in dstore.lines("user-a")))
check("(the goal's chat has lines in the store)", any(l.get("chat") == ng["chat"] for l in dstore.lines("user-a")))
ng2 = call(based, "/goal/new", "tok-a", {"title": "Read", "days": 14, "steps": ["One page"]})[1]
check("deleting a goal: it's gone, its chat stays", call(based, "/goal/delete", "tok-a", {"id": ng2["id"]})[1]["ok"]
      and not any(g["id"] == ng2["id"] for g in call(based, "/goals", "tok-a")[1]["goals"])
      and any(c["id"] == ng2["chat"] for c in call(based, "/state?v=0", "tok-a")[1]["chats"]))
dr = call(based, "/chat/delete", "tok-a", {"id": ng["chat"]})
check("deleting a chat: gone from the window, its goal too, and its lines from the store",
      dr[0] == 200 and dr[1]["ok"] and dr[1]["chat"] != ng["chat"]
      and not any(c["id"] == ng["chat"] for c in call(based, "/state?v=0", "tok-a")[1]["chats"])
      and not any(g["id"] == ng["id"] for g in call(based, "/goals", "tok-a")[1]["goals"])
      and not any(l.get("chat") == ng["chat"] for l in dstore.lines("user-a")))
check("...on this computer they're kept in archive/ (never destroy a life)",
      any("deleted_chat_" in n for n in os.listdir(os.path.join(tmp, "deleting", "user-a", "archive"))))
check("...an unknown chat is a 404", call(based, "/chat/delete", "tok-a", {"id": "c999"})[0] == 404)
check("...and only with Ember's header", call(based, "/chat/delete", "tok-a", {"id": "c1"}, header=False)[0] == 403)

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
mind.garble = 1
call(base, "/talk", "tok-a", {"text": "garbled once"})
check("an answer it can't read: it asks its mind again", wait(lambda: ember_lines("tok-a")[-1] == "I heard: garbled once"))
mind.garble = 2
call(base, "/talk", "tok-a", {"text": "garbled twice"})
check("...twice: it says so, no template answer", wait(lambda: ember_lines("tok-a")[-1] == FAILED))

print("Experiments still work through the server")
for s in ("I code for hours", "I want to make a game"):
    call(base, "/talk", "tok-a", {"text": s})
wait(lambda: "I heard: I want to make a game" in ember_lines("tok-a"))
st = state("tok-a", 0)
check("enough memories to build ideas on them", st["knows_enough"], str(st["memories"]))
cid = call(base, "/chat/new", "tok-a", {})[1]["id"]
check("a new chat", cid == "c2" and state("tok-a", 0)["chat"] == "c2" and not state("tok-a", 0)["talk"])
call(base, "/talk", "tok-a", {"text": "what should I work on", "chat": cid})
check("Ember answers in that chat", wait(lambda: "I heard: what should I work on" in ember_lines("tok-a"))
      and "This is your chat" in mind.last)
check("...and the first chat doesn't show it", "I heard: what should I work on" not in
      [l["text"] for l in call(base, "/state?v=0&chat=c1", "tok-a")[1]["talk"]])
check("the chat list has both, latest first", [c["id"] for c in state("tok-a", 0)["chats"]] == ["c2", "c1"])
st = state("tok-a", 0)
check("the window gets its mood and energy, for its look", all(k in st for k in ("mood", "energy", "valence", "feel"))
      and "energy" in st["face"])
check("renaming a chat", call(base, "/chat/rename", "tok-a", {"id": "c2", "title": "What to work on"})[1]["ok"]
      and state("tok-a", 0)["chats"][0]["title"] == "What to work on")
check("choosing how often it checks up, when and on which days",
      call(base, "/checkups", "tok-a", {"every": "daily", "at": "07:15", "days": [0, 2, 4]})[1]["ok"]
      and state("tok-a", 0)["checkups"] == {"every": "daily", "at": "07:15", "days": [0, 2, 4]}
      and not call(base, "/checkups", "tok-a", {"every": "hourly"})[1]["ok"])
check("...a window from before (a whole hour) still works", call(base, "/checkups", "tok-a", {"every": "daily", "hour": 9})[1][
    "ok"] and state("tok-a", 0)["checkups"]["at"] == "09:00")
call(base, "/checkups", "tok-a", {"every": "daily", "at": "18:00", "days": list(range(7))})
st = state("tok-a", 0)
check("the window gets its level and look", st["level"]["level"] >= 1 and st["look"]["color"] == "amber")
lk = call(base, "/looks", "tok-a")[1]
check("the catalog of looks, with what unlocks when", [p["id"] for p in lk["parts"]] ==
      ["color", "wear", "eyes", "cheeks", "sparks", "glow"] and lk["level"]["level"] == st["level"]["level"])
check("a locked look is refused", not call(base, "/look", "tok-a", {"part": "wear", "value": "crown"})[1]["ok"])
check("an unlocked one is put on", call(base, "/look", "tok-a", {"part": "color", "value": "amber"})[1]["ok"])

print("Goals of their own")
ng = call(base, "/goal/new", "tok-a", {"title": "Run 5 km", "days": 60, "steps": ["Walk 20 min"]})[1]
gl = call(base, "/goals", "tok-a")[1]["goals"]
g = next((x for x in gl if x["id"] == ng.get("id")), None)
check("make a goal yourself: it's on your goals list, in phases", ng["ok"] and g and g["status"] == "active"
      and g["phase_info"]["count"] == 5 and g["today_step"]["text"] == "Walk 20 min" and g["chat"] == ng["chat"])
nh = call(base, "/goal/new", "tok-a", {"title": "Tidy the flat", "n": 4, "unit": "hours"})[1]
gh = next((x for x in call(base, "/goals", "tok-a")[1]["goals"] if x["id"] == nh.get("id")), None)
check("a goal of 4 hours", nh["ok"] and gh and gh["days"] == round(4 / 24, 4) and gh["length"] == "4 hours"
      and gh["more"] == "1 more hour", str(gh and (gh["days"], gh.get("length"))))
check("...it can be dropped", call(base, "/experiment/end", "tok-a", {"id": nh["id"], "how": "dropped"})[1]["ok"])
n0 = len(call(base, f"/state?v=0&chat={ng['chat']}", "tok-a")[1]["talk"])
check("today's check", call(base, "/goal/check", "tok-a", {"id": ng["id"], "how": "done", "words": "nice"})[1]["ok"])
check("...and Ember answers in the goal's chat", wait(lambda: len(call(base, f"/state?v=0&chat={ng['chat']}", "tok-a")[1][
    "talk"]) >= n0 + 2))
check("a check that isn't one of the three is refused", not call(base, "/goal/check", "tok-a",
                                                                 {"id": ng["id"], "how": "maybe"})[1]["ok"])
check("add your own step", call(base, "/goal/step", "tok-a", {"id": ng["id"], "text": "Stretch"})[1]["ok"])
check("on to the next phase, with Ember's look back", call(base, "/goal/phase", "tok-a", {"id": ng["id"]})[1]["ok"]
      and wait(lambda: next(x for x in call(base, "/goals", "tok-a")[1]["goals"] if x["id"] == ng["id"])["phase"] == 1))
pw = call(base, "/goal/new", "tok-a", {"title": "Get a girlfriend", "with_ember": True})[1]
check("plan a goal with Ember: a new chat where it talks it through", pw["ok"] and wait(lambda: any(
    "I heard: I'd like to plan a goal with you: Get a girlfriend" in l["text"]
    for l in call(base, f"/state?v=0&chat={pw['chat']}", "tok-a")[1]["talk"])))
call(base, "/experiment/suggest", "tok-a", {})
check("asked for ideas, it suggests experiments", wait(lambda: state("tok-a", 0)["suggestions"]))
xid = state("tok-a", 0)["suggestions"][0]["id"]
check("you pick one", call(base, "/experiment/pick", "tok-a", {"id": xid})[1]["ok"])
T[0] += 8 * 86400
state("tok-a")
check("when its days are up, it asks: finish or keep going",
      wait(lambda: any(l.get("timeup") == xid for l in state("tok-a", 0)["talk"])))
check("3 more days", call(base, "/experiment/extend", "tok-a", {"id": xid})[1]["ok"] and state("tok-a", 0)["experiment"]["days"] == 11)
check("finish it", call(base, "/experiment/end", "tok-a", {"id": xid, "how": "done"})[1]["ok"])
check("...and it looks back on what actually happened, on its own line",
      wait(lambda: any(l.get("review") == xid and l["text"].startswith("Looking back: 0 daily checks")
                       for l in state("tok-a", 0)["talk"])))
check("...with the facts kept for the window", state("tok-a", 0)["exps"][xid]["facts"]["sessions"] == 0)

print("Ember checks up on you, even while you're away")
app5 = create_app(FileStore(os.path.join(tmp, "users5")), FakeAuth(), FakeCfg(), call=FakeMind(), clock=clock,
                  checkup_every=0.1)
base5, srv5 = serve(app5)
call(base5, "/state?v=0", "tok-a")
u5 = next(iter(app5.state.users.cache.values()))
with u5.lock:
    u5.ember.followups.append({"chat": "c1", "at": T[0] - 1, "about": "how the gym went", "set": T[0] - 3600})
check("a planned check-up arrives in its chat by itself", wait(lambda: any(
    l.get("checkup") and l["text"] == "Hello again." for l in call(base5, "/state?v=0", "tok-a")[1]["talk"])))
check("...and it isn't one of your free messages", call(base5, "/state?v=0", "tok-a")[1]["plan"]["plus"]
      or call(base5, "/state?v=0", "tok-a")[1]["plan"]["free_left"] == 10)
check("10 free messages a day by default", call(base5, "/state?v=0", "tok-a")[1]["plan"]["free_per_day"] == 10)
srv5.should_exit = True

print("Phone notifications (Web Push)")
import base64
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.utils import encode_dss_signature
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from server.push import Push, PushGone, b64u, encrypt, new_private_key, unb64u


def hk(salt, ikm, info, n):
    return HKDF(algorithm=hashes.SHA256(), length=n, salt=salt, info=info).derive(ikm)


phone = ec.generate_private_key(ec.SECP256R1())                     # what a phone's browser holds
phone_pub = phone.public_key().public_bytes(serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint)
auth_secret = os.urandom(16)
body = encrypt(b'{"body": "How did Wednesday go?"}', b64u(phone_pub), b64u(auth_secret))
salt, rs, idlen = body[:16], int.from_bytes(body[16:20], "big"), body[20]
sender_pub = body[21:21 + idlen]
shared = phone.exchange(ec.ECDH(), ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256R1(), sender_pub))
ikm = hk(auth_secret, shared, b"WebPush: info\x00" + phone_pub + sender_pub, 32)
plain = AESGCM(hk(salt, ikm, b"Content-Encoding: aes128gcm\x00", 16)).decrypt(
    hk(salt, ikm, b"Content-Encoding: nonce\x00", 12), body[21 + idlen:], None)
check("a notification decrypts on the phone (RFC 8291)", rs == 4096 and idlen == 65
      and plain == b'{"body": "How did Wednesday go?"}\x02')
pk = new_private_key()
pusher = Push(pk, "https://ember.example")
auth_header = pusher._vapid("https://push.example.com/abc", T[0])
token = auth_header.split("t=")[1].split(",")[0]
head, claims, sig = token.split(".")
pub = ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256R1(), unb64u(pusher.public))
raw = unb64u(sig)
try:
    pub.verify(encode_dss_signature(int.from_bytes(raw[:32], "big"), int.from_bytes(raw[32:], "big")),
               f"{head}.{claims}".encode(), ec.ECDSA(hashes.SHA256()))
    signed = True
except Exception:
    signed = False
cl = json.loads(unb64u(claims))
check("...and Ember signs its request (VAPID, RFC 8292)", signed and cl["aud"] == "https://push.example.com"
      and cl["sub"] == "https://ember.example" and auth_header.endswith("k=" + pusher.public))


class FakePush:
    public = "BFAKE"

    def __init__(self):
        self.sent, self.gone = [], set()

    def send(self, device, message, ttl=0, now=None):
        if device["endpoint"] in self.gone:
            raise PushGone()
        self.sent.append((device["endpoint"], message))
        return 201


fp = FakePush()
app6 = create_app(FileStore(os.path.join(tmp, "users6")), FakeAuth(), FakeCfg(), call=FakeMind(), clock=clock,
                  checkup_every=0.1, push=fp)
base6, srv6 = serve(app6)
check("the window learns Ember's public key", call(base6, "/config")[1]["vapid_public"] == "BFAKE")
sub = {"endpoint": "https://push.example.com/phone1", "keys": {"p256dh": b64u(phone_pub), "auth": b64u(auth_secret)}}
check("a phone turns notifications on", call(base6, "/push/subscribe", "tok-a", {"subscription": sub})[1]["ok"])
check("a bad subscription is refused", call(base6, "/push/subscribe", "tok-a",
                                           {"subscription": {"endpoint": "http://x"}})[0] == 400)
call(base6, "/state?v=0&tz=60", "tok-a")
u6 = next(iter(app6.state.users.cache.values()))
check("the window tells Ember its clock", u6.ember.tz == 60 and len(u6.ember.devices) == 1)
check("the same phone sent again (each time Ember opens) stays one device",
      call(base6, "/push/subscribe", "tok-a", {"subscription": sub})[1]["ok"] and len(u6.ember.devices) == 1)
day = T[0] - (T[0] % 86400)
T_saved = T[0]
T[0] = day + 9 * 3600                            # 10:00 their time
with u6.lock:
    u6.ember.followups.append({"chat": "c1", "at": T[0] - 1, "about": "the gym", "set": T[0] - 3600})
check("a check-up goes to the phone as a notification", wait(lambda: fp.sent and fp.sent[-1][1]["chat"] == "c1"
      and fp.sent[-1][1]["body"] == "Hello again." and fp.sent[-1][1]["title"] == "Ember sent you a message"))
check("you can name it, and its notifications say so", call(base6, "/name", "tok-a", {"name": "Lumi"})[1]["ok"]
      and call(base6, "/state?v=0", "tok-a")[1]["name"] == "Lumi")
st6 = call(base6, "/state?v=0", "tok-a")[1]
check("/state has its moments: naming it is one",
      any(m["id"] == "named" and m["text"] == "You named me Lumi." for m in st6.get("moments", [])),
      st6.get("moments"))
with u6.lock:
    u6.ember.talk.append({"t": T[0], "who": "you", "text": "ok"})
    u6.ember.followups.append({"chat": "c1", "at": T[0] - 1, "about": "the run", "set": T[0] - 3600})
check("...\"Lumi sent you a message\"", wait(lambda: fp.sent[-1][1]["title"] == "Lumi sent you a message"))
fp.gone.add(sub["endpoint"])
with u6.lock:
    u6.ember.talk.append({"t": T[0], "who": "you", "text": "ok"})
    u6.ember.followups.append({"chat": "c1", "at": T[0] - 1, "about": "again", "set": T[0] - 3600})
check("a phone that turned notifications off is forgotten", wait(lambda: not u6.ember.devices))
check("turning off from the window", call(base6, "/push/subscribe", "tok-a", {"subscription": sub})[1]["ok"]
      and call(base6, "/push/unsubscribe", "tok-a", {"endpoint": sub["endpoint"]})[1]["ok"] and not u6.ember.devices)
T[0] = T_saved
srv6.should_exit = True

print("The daily limit")
store2 = FileStore(os.path.join(tmp, "users2"))
base2, srv2 = serve(create_app(store2, FakeAuth(), FakeCfg(), call=FakeMind(), clock=clock, daily_cap=2,
                               retry_delay=0.01, retry_every=0.3, plus_emails=("a@x.hu", "b@x.hu")))
call(base2, "/state?v=1", "tok-b")
for s in ("one", "two", "three"):
    call(base2, "/talk", "tok-b", {"text": s})
lines2 = lambda: [l["text"] for l in call(base2, "/state", "tok-b")[1]["talk"] if l["who"] == "ember"]
check("past the limit it says so instead of thinking", wait(lambda: lines2()[-1:] == [CAPPED]), str(lines2()))
srv2.should_exit = True

print("Feedback")
check("it needs Ember's header", call(base, "/feedback", "tok-a", {"text": "hi"}, header=False)[0] == 403)
check("an empty one is refused", call(base, "/feedback", "tok-a", {"kind": "idea", "text": "  "})[0] == 400)
check("an idea is sent", call(base, "/feedback", "tok-a", {"kind": "idea", "text": "a dark mode for goals", "screen": "goal"})[1] == {"ok": True})
fb = store.feedback("user-a")
check("...saved with the email, the kind, the level and where they were", len(fb) == 1 and fb[0]["email"] == "a@x.hu"
      and fb[0]["kind"] == "idea" and fb[0]["text"] == "a dark mode for goals" and fb[0]["extra"]["screen"] == "goal"
      and isinstance(fb[0]["extra"]["level"], int), str(fb))
call(base, "/feedback", "tok-a", {"kind": "nonsense", "text": "b"})
check("an unknown kind becomes other", store.feedback("user-a")[-1]["kind"] == "other")
check("a very long one is cut at 2000 characters",
      call(base, "/feedback", "tok-a", {"text": "x" * 5000})[0] == 200 and len(store.feedback("user-a")[-1]["text"]) == 2000)
codes = [call(base, "/feedback", "tok-a", {"text": f"n{i}"})[0] for i in range(8)]
check("at most 10 an hour", codes[:7] == [200] * 7 and codes[7] == 429, str(codes))

print("Your data")
status, data = call(base, "/me/export", "tok-a")
check("download everything: self and the whole conversation",
      status == 200 and data["ember"]["memories"] and len(data["conversation"]) >= 6)
check("...and the feedback they sent", len(data["feedback"]) == 10)
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
                               retry_delay=0.01, retry_every=0.3, plus_emails=("a@x.hu", "b@x.hu")))
check("it answers what was left unanswered",
      wait(lambda: any(l["text"] == "I heard: hello before the restart" for l in call(base3, "/state", "tok-b")[1]["talk"])))
srv3.should_exit = True


# ------------------------------------------------------------------ fake Supabase
class Fake(BaseHTTPRequestHandler):
    tables = {"embers": [], "lines": [], "usage": [], "plans": []}
    keys = {"embers": ("user_id",), "usage": ("user_id", "day"), "plans": ("user_id",)}
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
        def get(r, k):                             # a JSON field too: extra->>chat
            if "->>" in k:
                col, sub = k.split("->>")
                return (r.get(col) or {}).get(sub)
            return r.get(k)
        f = {k: v[3:] for k, v in q.items() if v.startswith("eq.")}
        nulls = [k for k, v in q.items() if v == "is.null"]
        return [r for r in rows if all(str(get(r, k)) == v for k, v in f.items()) and all(get(r, k) is None for k in nulls)]

    def do_GET(self):
        path, q = self._parse()
        if path == "/auth/v1/admin/users":
            return self._send(200, {"users": [{"id": "u1", "email": "a@x.hu"}]})
        if path == "/auth/v1/user":
            tok = self.headers.get("Authorization", "")[7:]
            return self._send(200, {"id": "sb-1", "email": "Me@X.hu"}) if tok == "good" else self._send(401, {})
        if self.headers.get("apikey") != "service":
            return self._send(401, {})
        if path.split("/")[-1] not in self.tables:
            return self._send(404, {})             # like Supabase, for a table that wasn't made yet
        rows = self._match(self.tables[path.split("/")[-1]], q)
        if "order" in q:
            rows = sorted(rows, key=lambda r: r.get(q["order"].split(".")[0]) or 0)
        rows = rows[int(q.get("offset", 0)):][:int(q.get("limit", 10 ** 9))]
        if "select" in q and q["select"] != "*":
            rows = [{k: r.get(k) for k in q["select"].split(",")} for r in rows]
        self._send(200, rows)

    def do_POST(self):
        path, q = self._parse()
        table = path.split("/")[-1]
        if table not in self.tables:
            return self._send(404, {})
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
        if table not in self.tables:
            return self._send(404, {})
        keep = [r for r in self.tables[table] if r not in self._match(self.tables[table], q)]
        self.tables[table][:] = keep
        self._send(204)


print("Free messages, the paywall and Ember Plus (against a fake Stripe)")


class FakeStripe(BaseHTTPRequestHandler):
    seen = []
    no_branding = False          # an older Stripe API that refuses branding_settings
    gone = set()                 # customers Stripe doesn't know (e.g. made in test mode, now live)

    def log_message(self, *a):
        pass

    def _send(self, body):
        raw = json.dumps(body).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_POST(self):
        fields = dict(urllib.parse.parse_qsl(self.rfile.read(int(self.headers["Content-Length"])).decode()))
        self.seen.append(("POST", self.path, fields, self.headers.get("Authorization")))
        if (self.no_branding and any(k.startswith("branding_settings") for k in fields)) or fields.get("customer") in self.gone:
            raw = json.dumps({"error": {"code": "resource_missing", "param": "customer", "message": "No such customer"}
                              if fields.get("customer") in self.gone else {"code": "parameter_unknown"}}).encode()
            self.send_response(400)
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)
            return
        self._send({"url": "https://pay.test/checkout" if "checkout" in self.path else "https://pay.test/portal"})

    def do_DELETE(self):
        self.seen.append(("DELETE", self.path, {}, self.headers.get("Authorization")))
        self._send({"status": "canceled"})


import hashlib
import hmac
from server.billing import Billing
from server.app import LAST_FREE

st = ThreadingHTTPServer(("127.0.0.1", 0), FakeStripe)
threading.Thread(target=st.serve_forever, daemon=True).start()
billing = Billing("sk_test_x", "price_plus", "whsec_x", "$4.99 / month", api=f"http://127.0.0.1:{st.server_address[1]}")
store4 = FileStore(os.path.join(tmp, "users4"))
base4, srv4 = serve(create_app(store4, FakeAuth(), FakeCfg(), call=FakeMind(), clock=clock, retry_delay=0.01,
                               retry_every=0.3, billing=billing, free_per_day=2, plus_emails=("a@x.hu",)))
plan4 = lambda tok="tok-b": call(base4, "/state", tok)[1]["plan"]
lines4 = lambda tok="tok-b": call(base4, "/state", tok)[1]["talk"]
check("a new person starts with today's free messages", plan4() == {"plus": False, "free_left": 2, "free_per_day": 2,
                                                                  "price": "$4.99 / month", "price_year": None,
                                                                  "payments": True, "manage": False})
check("first free message: answered", call(base4, "/talk", "tok-b", {"text": "hello"})[0] == 200
      and wait(lambda: lines4()[-1]["text"] == "I heard: hello"))
call(base4, "/talk", "tok-b", {"text": "second"})
check("after its answer to the last free one, Ember says so",
      wait(lambda: lines4()[-1]["text"] == LAST_FREE and lines4()[-2]["text"] == "I heard: second"))
check("...the line is marked for the paywall card", lines4()[-1].get("paywall") is True)
check("no free messages left", plan4()["free_left"] == 0)
check("a third message today is refused (402) and not stored",
      call(base4, "/talk", "tok-b", {"text": "third"})[0] == 402 and not any(l["text"] == "third" for l in lines4()))
check("asking for ideas counts too", call(base4, "/experiment/suggest", "tok-b", {})[0] in (200, 402))
check("greetings are free", (call(base4, "/state?v=1", "tok-b") and True))
check("a comped tester (Plus by email) has no limit", plan4("tok-a")["plus"] and plan4("tok-a")["free_left"] is None)
base5, srv5 = serve(create_app(FileStore(os.path.join(tmp, "users5")), FakeAuth(), FakeCfg(), call=FakeMind(), clock=clock, retry_delay=0.01,
                               retry_every=0.3, billing=billing, free_per_day=2, plus_emails=("*",),
                               unlock_emails=("b@x.hu",), owner_emails=("A@x.hu ",)))
p5 = call(base5, "/state", "tok-b")[1]["plan"]
t5 = call(base5, "/talk", "tok-b", {"text": "past the limit"})
check("Plus for everyone (EMBER_PLUS_EMAILS=*): no limit, nothing to buy or manage", p5["plus"] and p5["free_left"] is None
      and not p5["manage"] and t5[0] == 200, f"{p5} talk: {t5}")
lk = lambda tok: call(base5, "/looks", tok)[1]
check("a tester (EMBER_UNLOCK_EMAILS) can wear the highest look at level 1, without any XP",
      lk("tok-b")["all_unlocked"] and call(base5, "/look", "tok-b", {"part": "color", "value": "aurora"})[1]["ok"]
      and call(base5, "/state", "tok-b")[1]["look"]["color"] == "aurora" and lk("tok-b")["level"]["level"] == 1)
check("...anyone else can't", not lk("tok-a")["all_unlocked"]
      and not call(base5, "/look", "tok-a", {"part": "color", "value": "aurora"})[1]["ok"])
print("The owner page")
call(base5, "/feedback", "tok-b", {"kind": "problem", "text": "the button is stuck"})
T[0] += 5
call(base5, "/feedback", "tok-a", {"kind": "idea", "text": "a weekly summary"})
T[0] -= 5
check("only the owner (EMBER_OWNER_EMAILS, case and spaces ignored) is told about it",
      call(base5, "/state", "tok-a")[1]["owner"] and not call(base5, "/state", "tok-b")[1]["owner"])
check("anyone else gets 404", call(base5, "/owner/data", "tok-b")[0] == 404)
check("...and without a login, 401", call(base5, "/owner/data")[0] == 401)
status, own = call(base5, "/owner/data", "tok-a")
pb = next((p for p in own["list"] if p["email"] == "b@x.hu"), {}) if own else {}
check("the owner sees how many people, and who was here today", status == 200 and own["people"] == 2 and own["today"] >= 1
      and own["week"] >= 1 and own["new_week"] == 2, str(own and {k: own[k] for k in ("people", "today", "week", "new_week")}))
check("...each person: email, messages, days, level, Plus", pb.get("said") == 1 and pb.get("days") == 1
      and pb.get("level") >= 1 and pb.get("plus") == "everyone", str(pb))
check("...whether they come back (nobody is a week old yet)", own["retention"] == {"joined_before": 0, "back_day2": 0, "back_week2": 0})
check("...feedback with the email, newest first", [f["text"] for f in own["feedback"]] == ["a weekly summary", "the button is stuck"]
      and own["feedback"][1]["email"] == "b@x.hu" and own["feedback"][1]["kind"] == "problem")
check("...and the cost", own["cost"]["today"]["calls"] >= 1 and own["cost"]["month"]["usd"] >= 0)
check("...but never what anyone said to Ember", "past the limit" not in json.dumps(own) and "I heard" not in json.dumps(own))
srv5.should_exit = True
T[0] += 86400
check("the next day, free messages are back", plan4()["free_left"] == 2)
T[0] -= 86400
status, out = call(base4, "/plus/checkout", "tok-b", {})
sent = FakeStripe.seen[-1]
check("Get Ember Plus opens a Stripe checkout page for this person",
      status == 200 and out["url"] == "https://pay.test/checkout" and sent[2]["client_reference_id"] == "user-b"
      and sent[2]["line_items[0][price]"] == "price_plus" and sent[2]["mode"] == "subscription"
      and sent[2]["payment_method_types[0]"] == "card"
      and sent[3] == "Bearer sk_test_x")
check("...with no terms set, Stripe isn't asked for consent", "consent_collection[terms_of_service]" not in sent[2])
gq = call(base4, "/goal/new", "tok-b", {"title": "Run", "days": 14, "steps": ["Walk"]})
gc = call(base4, "/goal/check", "tok-b", {"id": (gq[1] or {}).get("id"), "how": "done"})
check("progress is free: out of free messages, you can still make a goal and check in on it", (gq[1] or {}).get("ok")
      and (gc[1] or {}).get("ok") and plan4()["free_left"] == 0, f"new: {gq} check: {gc} plan: {plan4()}")

print("Real money: only once the terms (ÁSZF) are online")
live = Billing("sk_live_x", "price_live", "whsec_l", "$4.99 / month", api=f"http://127.0.0.1:{st.server_address[1]}")
base7, srv7 = serve(create_app(FileStore(os.path.join(tmp, "users7")), FakeAuth(), FakeCfg(), call=FakeMind(), clock=clock,
                               billing=live, free_per_day=2))
check("a live Stripe key without EMBER_TERMS_URL sells nothing yet", live.live and not live.selling
      and call(base7, "/plus/checkout", "tok-b", {})[0] == 503 and not call(base7, "/state", "tok-b")[1]["plan"]["payments"])
srv7.should_exit = True
live_t = Billing("sk_live_x", "price_live", "whsec_l", "$4.99 / month", api=f"http://127.0.0.1:{st.server_address[1]}",
                 terms_url="https://example.hu/aszf")
base8, srv8 = serve(create_app(FileStore(os.path.join(tmp, "users8")), FakeAuth(), FakeCfg(), call=FakeMind(), clock=clock,
                               billing=live_t, free_per_day=2))
status, out = call(base8, "/plus/checkout", "tok-b", {})
check("with the terms online: checkout opens, and Stripe asks the buyer to accept them", status == 200
      and FakeStripe.seen[-1][2].get("consent_collection[terms_of_service]") == "required"
      and FakeStripe.seen[-1][3] == "Bearer sk_live_x")
check("the window gets the terms' address (for the menu and the paywall)",
      call(base8, "/config")[1]["terms_url"] == "https://example.hu/aszf")
srv8.should_exit = True


def hook(event, secret="whsec_x", t=None):
    raw = json.dumps(event).encode()
    t = int(clock()) if t is None else t
    sig = hmac.new(secret.encode(), f"{t}.".encode() + raw, hashlib.sha256).hexdigest()
    req = urllib.request.Request(base4 + "/stripe/webhook", data=raw, method="POST",
                                 headers={"Stripe-Signature": f"t={t},v1={sig}", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code


paid = {"type": "checkout.session.completed", "data": {"object": {"mode": "subscription", "client_reference_id": "user-b",
                                                                  "customer": "cus_b", "subscription": "sub_b",
                                                                  "metadata": {"app": "ember"}}}}
check("Ember's payment page has its own name, icon and colours (not the Stripe account's)",
      sent[2].get("branding_settings[display_name]") == "Ember" and sent[2].get("branding_settings[icon][url]", "").endswith("/icons/icon-512.png")
      and sent[2].get("branding_settings[button_color]") == "#ffa862")
FakeStripe.no_branding = True
status_nb, out_nb = call(base4, "/plus/checkout", "tok-b", {})
FakeStripe.no_branding = False
check("...and if Stripe refuses the branding, the plain payment page still opens",
      status_nb == 200 and out_nb["url"] == "https://pay.test/checkout" and "branding_settings[display_name]" not in FakeStripe.seen[-1][2])
check("checkout tags the payment as Ember's", sent[2].get("metadata[app]") == "ember"
      and sent[2].get("subscription_data[metadata][app]") == "ember")
other = {"type": "checkout.session.completed", "data": {"object": {"mode": "subscription", "client_reference_id": "user-b",
                                                                   "customer": "cus_x", "subscription": "sub_x"}}}
check("someone buying something else on the same Stripe account doesn't change any Ember", hook(other) == 200 and not plan4()["plus"])
other_sub = {"type": "customer.subscription.created", "data": {"object": {"id": "sub_x", "customer": "cus_x", "status": "active",
             "metadata": {"user_id": "user-b"}, "items": {"data": [{"price": {"id": "price_other"}}]}}}}
check("...nor their subscription", hook(other_sub) == 200 and not plan4()["plus"])
ghost = {"type": "customer.subscription.created", "data": {"object": {"id": "sub_g", "customer": "cus_g", "status": "active",
         "metadata": {"user_id": "nobody", "app": "ember"}}}}
check("an Ember that no longer exists: received, nothing to do, no retries", hook(ghost) == 200)
check("a webhook with a wrong signature is refused", hook(paid, secret="whsec_wrong") == 400)
check("an old webhook (replayed) is refused", hook(paid, t=int(clock()) - 3600) == 400)
check("Stripe says paid: Ember Plus is on", hook(paid) == 200 and plan4()["plus"] and plan4()["manage"])
said4 = lambda: [l["text"] for l in call(base4, "/state", "tok-b")[1]["talk"]]
created = {"type": "customer.subscription.created", "data": {"object": {"id": "sub_b", "customer": "cus_b",
                                                                        "status": "active", "metadata": {"user_id": "user-b"},
                                                                        "items": {"data": [{"price": {"id": "price_plus"}}]}}}}
check("...Ember says thank you in the conversation, once", hook(created) == 200 and said4().count(PLUS_ON) == 1)
check("with Plus, you can talk again", call(base4, "/talk", "tok-b", {"text": "now plus"})[0] == 200)
check("Manage Ember Plus opens Stripe's portal", call(base4, "/plus/portal", "tok-b", {})[1]["url"] == "https://pay.test/portal")
ended = {"type": "customer.subscription.deleted", "data": {"object": {"id": "sub_b", "customer": "cus_b",
                                                                      "status": "canceled", "metadata": {"user_id": "user-b", "app": "ember"}}}}
check("Stripe says canceled: back to free", hook(ended) == 200 and not plan4()["plus"])
check("...and Ember says so", said4()[-1] == PLUS_ENDED)
check("an ended subscription has nothing to manage", not plan4()["manage"])
FakeStripe.gone = {"cus_b"}
status_g, out_g = call(base4, "/plus/checkout", "tok-b", {})
FakeStripe.gone = set()
check("a customer Stripe no longer knows (from test mode) doesn't stop you buying: it starts fresh with your email",
      status_g == 200 and out_g["url"] == "https://pay.test/checkout" and FakeStripe.seen[-1][2].get("customer_email") == "b@x.hu"
      and "customer" not in FakeStripe.seen[-1][2])
yb = Billing("sk_test_x", "price_plus", "whsec_x", api=f"http://127.0.0.1:{st.server_address[1]}", yearly_id="price_year")
yb.checkout("user-y", "y@x.hu", None, "https://e.test", yearly=True)
year_price = FakeStripe.seen[-1][2].get("line_items[0][price]")
yb.checkout("user-y", "y@x.hu", None, "https://e.test")
check("the yearly plan: its own price on the payment page; monthly stays the default",
      year_price == "price_year" and FakeStripe.seen[-1][2].get("line_items[0][price]") == "price_plus"
      and yb.price_label == "$7.99 / month" and yb.yearly_label == "$49.99 / year")
year_sub = {"type": "customer.subscription.created", "data": {"object": {"id": "sub_y", "customer": "cus_y", "status": "active",
            "metadata": {"user_id": "user-y"}, "items": {"data": [{"price": {"id": "price_year"}}]}}}}
check("...and an untagged subscription at the yearly price is Ember's too",
      Billing.plan_from_event(year_sub, yb.prices) is not None and Billing.plan_from_event(year_sub, "price_plus") is None)
hook(paid)
FakeStripe.gone = {"cus_b"}
status_m, out_m = call(base4, "/plus/portal", "tok-b", {})
FakeStripe.gone = set()
check("Manage Ember Plus with a customer Stripe no longer knows: the plan is forgotten and the payment page opens",
      status_m == 200 and out_m["url"] == "https://pay.test/checkout" and not plan4()["plus"] and not plan4()["manage"])
hook(paid)
call(base4, "/me/delete", "tok-b", {})
check("deleting your Ember also cancels the subscription",
      any(m == "DELETE" and p == "/v1/subscriptions/sub_b" for m, p, _, _ in FakeStripe.seen))
srv4.should_exit = True
st.shutdown()

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
sb.append_lines("u1", [{"t": 3.0, "who": "you", "text": "c", "chat": "c2"}])
sb.delete_lines("u1", "c2")
check("deleting a chat deletes only its lines", [l["text"] for l in sb.lines("u1")] == ["a", "b"])
sb.append_lines("u1", [{"t": 4.0, "who": "you", "text": "d", "chat": "c2"}])
sb.delete_lines("u1", "c1")
check("...the first chat's lines carry no chat", [l["text"] for l in sb.lines("u1")] == ["d"])
sb.delete_lines("u1", "c2")
sb.append_lines("u1", [{"t": 2.0, "who": "ember", "text": "b", "exps": ["x1"]}, {"t": 1.0, "who": "you", "text": "a"}])
sb.add_call("u1", "2026-11-03", 3000, 200)
sb.add_call("u1", "2026-11-03", 1000, 100)
check("usage adds up per day", sb.calls_today("u1", "2026-11-03") == 2 and Fake.tables["usage"][0]["tokens_in"] == 4000)
check("all users listed", sb.all_uids() == ["u1"])
sb.save_self("u0", {"memories": []})
sb.save_self("u2", {"memories": []})
check("...page by page, past Supabase's 1000 rows a request", sb.all_uids(page=2) == ["u0", "u1", "u2"]
      and sb.all_uids(page=1) == ["u0", "u1", "u2"])
for uid in ("u0", "u2"):
    Fake.tables["embers"] = [r for r in Fake.tables["embers"] if r["user_id"] != uid]
sb.add_message("u1", "2026-11-03")
check("free messages are counted per day", sb.messages_today("u1", "2026-11-03") == 1 and sb.calls_today("u1", "2026-11-03") == 2)
sb.set_plan("u1", {"status": "active", "customer": "cus_1", "subscription": "sub_1"})
sb.set_plan("u1", {"status": "canceled", "customer": "cus_1", "subscription": "sub_1"})
check("the plan is one row, updated", sb.get_plan("u1")["status"] == "canceled" and len(Fake.tables["plans"]) == 1)
check("the owner page: every plan, every email, the usage since a day",
      sb.all_plans() == {"u1": {"user_id": "u1", "status": "canceled"}} and sb.emails() == {"u1": "a@x.hu"}
      and [r["calls"] for r in sb.usage_since("2026-11-01")] == [2])
check("...and no feedback table yet is just no feedback", sb.all_feedback() == [])
check("export has everything", sb.export("u1")["ember"] == {"memories": [1, 2]} and len(sb.export("u1")["conversation"]) == 2)
check("without a feedback table yet, the export still works", sb.export("u1")["feedback"] == [])
try:
    sb.add_feedback("u1", {"kind": "idea", "text": "x"})
    check("...and sending feedback says it failed (so the window can say so)", False)
except StoreError:
    check("...and sending feedback says it failed (so the window can say so)", True)
Fake.tables["feedback"] = []
sb.add_feedback("u1", {"t": 1.0, "email": "a@x.hu", "kind": "problem", "text": "the menu is stuck", "extra": {"level": 3}})
check("feedback is saved with the email and kind", Fake.tables["feedback"][0]["kind"] == "problem"
      and Fake.tables["feedback"][0]["email"] == "a@x.hu" and Fake.tables["feedback"][0]["user_id"] == "u1")
check("...and is in their export", sb.export("u1")["feedback"][0]["text"] == "the menu is stuck")
sb.delete_user("u1")
check("delete removes every row and the login", not any(Fake.tables.values()) and Fake.deleted_users == ["u1"])
del Fake.tables["feedback"]
sb.save_self("u9", {"memories": []})
sb.delete_user("u9")
check("...also when the feedback table wasn't made yet", not Fake.tables["embers"] and Fake.deleted_users[-1] == "u9")
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

print("keeping Supabase awake")
from server.__main__ import keep_awake


class Reads:
    def __init__(self, fail=False):
        self.n, self.fail = 0, fail

    def all_uids(self):
        self.n += 1
        if self.fail:
            raise OSError("down")
        return []


ok_store, bad_store = Reads(), Reads(fail=True)
threading.Thread(target=keep_awake, args=(ok_store, 0.05), daemon=True).start()
threading.Thread(target=keep_awake, args=(bad_store, 0.05), daemon=True).start()
time.sleep(0.4)
check("it reads the store again and again", ok_store.n >= 3)
check("a failed read doesn't stop it", bad_store.n >= 3)

print("Many people at once")
from server.app import IDLE_FOR, MindWorker, Users      # noqa: E402
TU = [1_800_000_000.0]
us = Users(FileStore(os.path.join(tmp, "users_many")), lambda: TU[0])
mw = MindWorker(us, FakeCfg(), None, lambda: TU[0], 150, threads=4)
check("one person's thoughts always go to the same thread, in order",
      all(mw.queue_of("user-%d" % i) is mw.queue_of("user-%d" % i) for i in range(50)))
check("...and different people spread over the threads", len({id(mw.queue_of("user-%d" % i)) for i in range(50)}) == 4)
inside, most, mlock = [0], [0], threading.Lock()


def slow_mind(cfg, system, user, json_mode=False):
    with mlock:
        inside[0] += 1
        most[0] = max(most[0], inside[0])
    time.sleep(0.3)
    with mlock:
        inside[0] -= 1
    return json.dumps({"reply": "hi", "face": "happy"})


mw2 = MindWorker(us, FakeCfg(), slow_mind, lambda: TU[0], 150, threads=4)
mw2.start()
for i in range(4):
    mw2.put("user-%d" % i, {"type": "talk", "text": "hello"})
check("several people's answers are thought up at the same time",
      wait(lambda: all(us.get("user-%d" % i).jobs == 0 for i in range(4))) and most[0] >= 2, f"at most {most[0]} at once")
mw3 = MindWorker(us, FakeCfg(), slow_mind, lambda: TU[0], 150, threads=4)
mw3.start()
inside[0] = most[0] = 0
for _ in range(3):
    mw3.put("user-0", {"type": "talk", "text": "again"})
check("...but one person's, one at a time", wait(lambda: us.get("user-0").jobs == 0) and most[0] == 1)
us.get("user-0").ember.name = "Pip"
TU[0] += IDLE_FOR - 1
check("an Ember used within the hour stays in memory", us.evict() == 0 and "user-0" in us.cache)
TU[0] += 2
us.get("user-1")                                # used just now: stays
gone = us.evict()
check("Embers idle for an hour leave memory", "user-0" not in us.cache and "user-2" not in us.cache and gone == 3)
check("...but not one that was just used", "user-1" in us.cache)
check("...saved first: it comes back as it was", us.get("user-0").ember.name == "Pip")
busy = us.get("user-3")
busy.jobs = 1
TU[0] += IDLE_FOR * 2
us.evict()
check("...and never while it's thinking", "user-3" in us.cache)
busy.jobs = 0
us.get("user-5", touch=False)
check("a look from the background (check-ups, a restart) doesn't keep it in memory", us.evict() >= 1 and "user-5" not in us.cache)

print("Ember's own address (yourember.app)")
import http.client  # noqa: E402
baseh, srvh = serve(create_app(FileStore(os.path.join(tmp, "users_home")), FakeAuth(), FakeCfg(), call=FakeMind(), clock=clock,
                               public_url="https://yourember.app/"))


def at(host, path, method="GET"):
    c = http.client.HTTPConnection(baseh.split("//")[1], timeout=5)
    c.request(method, path, body=b"{}" if method == "POST" else None, headers={"Host": host})
    r = c.getresponse()
    r.read()
    return r.status, r.getheader("location")


check("a page opened at Render's address moves to yourember.app", at("ember-dztb.onrender.com", "/") == (301, "https://yourember.app/"))
check("...the terms too, with what came after the address",
      at("ember-dztb.onrender.com", "/terms?x=1") == (301, "https://yourember.app/terms?x=1"))
check("...but Ember's API there keeps answering (open windows, Stripe's webhook)",
      at("ember-dztb.onrender.com", "/config")[0] == 200 and at("ember-dztb.onrender.com", "/stripe/webhook", "POST")[0] != 301)
check("at yourember.app itself, nothing moves", at("yourember.app", "/terms")[0] == 200 and at("yourember.app", "/")[0] == 200)
check("...nor on this computer", at("localhost:8765", "/")[0] == 200)

print("Badges")
bl = call(baseh, "/badges", "tok-a")[1]["badges"]
check("the window gets every badge, with its level and what the next one takes", len(bl) >= 10 and all(b["how"] and b["level"] == 0 for b in bl))
call(baseh, "/talk", "tok-a", {"text": "hi there"})
check("...and your first words reach level 1 of one, which /state shows", wait(lambda: call(baseh, "/state?v=1", "tok-a")[1]["badges"].get("talk") == 1))

print()
print("All checks passed." if not failed else f"{len(failed)} FAILED: {failed}")
sys.stdout.flush()
os._exit(1 if failed else 0)                   # the servers' threads don't need a clean shutdown
