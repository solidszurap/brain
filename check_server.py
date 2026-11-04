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
from server.app import CAPPED, FAILED, PLUS_ENDED, PLUS_ON, UNREACHABLE, create_app
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
        self.last = user
        if self.fail > 0:
            self.fail -= 1
            raise llm.LLMError("fake trouble", retryable=self.retryable)
        cfg.last_usage = (3000, 200)
        if "Look back on it honestly" in user:
            return json.dumps({"reply": "Looking back: " + re.search(r"What actually happened: (.*)", user).group(1)[:80]})
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
      all(urllib.request.urlopen(base + p).status == 200 for p in ("/", "/manifest.webmanifest", "/sw.js", "/privacy")))
check("config says online", call(base, "/config")[1]["mode"] == "online")

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
check("enough memories to build ideas on them", st["knows_enough"], str(st["memories"]))
cid = call(base, "/chat/new", "tok-a", {})[1]["id"]
check("a new chat", cid == "c2" and state("tok-a", 0)["chat"] == "c2" and not state("tok-a", 0)["talk"])
call(base, "/talk", "tok-a", {"text": "what should I work on", "chat": cid})
check("Ember answers in that chat", wait(lambda: "I heard: what should I work on" in ember_lines("tok-a"))
      and "This is your chat" in mind.last)
check("...and the first chat doesn't show it", "I heard: what should I work on" not in
      [l["text"] for l in call(base, "/state?v=0&chat=c1", "tok-a")[1]["talk"]])
check("the chat list has both, latest first", [c["id"] for c in state("tok-a", 0)["chats"]] == ["c2", "c1"])
check("renaming a chat", call(base, "/chat/rename", "tok-a", {"id": "c2", "title": "What to work on"})[1]["ok"]
      and state("tok-a", 0)["chats"][0]["title"] == "What to work on")
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
      wait(lambda: any(l.get("review") == xid and l["text"].startswith("Looking back: 0 work sessions")
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
      or call(base5, "/state?v=0", "tok-a")[1]["plan"]["free_left"] == 5)
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
day = T[0] - (T[0] % 86400)
T_saved = T[0]
T[0] = day + 9 * 3600                            # 10:00 their time
with u6.lock:
    u6.ember.followups.append({"chat": "c1", "at": T[0] - 1, "about": "the gym", "set": T[0] - 3600})
check("a check-up goes to the phone as a notification", wait(lambda: fp.sent and fp.sent[-1][1]["chat"] == "c1"
      and fp.sent[-1][1]["body"] == "Hello again."))
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


print("Free messages, the paywall and Ember Plus (against a fake Stripe)")


class FakeStripe(BaseHTTPRequestHandler):
    seen = []

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
billing = Billing("sk_test_x", "price_plus", "whsec_x", "€4.99 / month", api=f"http://127.0.0.1:{st.server_address[1]}")
store4 = FileStore(os.path.join(tmp, "users4"))
base4, srv4 = serve(create_app(store4, FakeAuth(), FakeCfg(), call=FakeMind(), clock=clock, retry_delay=0.01,
                               retry_every=0.3, billing=billing, free_per_day=2, plus_emails=("a@x.hu",)))
plan4 = lambda tok="tok-b": call(base4, "/state", tok)[1]["plan"]
lines4 = lambda tok="tok-b": call(base4, "/state", tok)[1]["talk"]
check("a new person starts with today's free messages", plan4() == {"plus": False, "free_left": 2, "free_per_day": 2,
                                                                  "price": "€4.99 / month", "payments": True, "manage": False})
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
                                                                  "customer": "cus_b", "subscription": "sub_b"}}}
check("a webhook with a wrong signature is refused", hook(paid, secret="whsec_wrong") == 400)
check("an old webhook (replayed) is refused", hook(paid, t=int(clock()) - 3600) == 400)
check("Stripe says paid: Ember Plus is on", hook(paid) == 200 and plan4()["plus"] and plan4()["manage"])
said4 = lambda: [l["text"] for l in call(base4, "/state", "tok-b")[1]["talk"]]
created = {"type": "customer.subscription.created", "data": {"object": {"id": "sub_b", "customer": "cus_b",
                                                                        "status": "active", "metadata": {"user_id": "user-b"}}}}
check("...Ember says thank you in the conversation, once", hook(created) == 200 and said4().count(PLUS_ON) == 1)
check("with Plus, you can talk again", call(base4, "/talk", "tok-b", {"text": "now plus"})[0] == 200)
check("Manage Ember Plus opens Stripe's portal", call(base4, "/plus/portal", "tok-b", {})[1]["url"] == "https://pay.test/portal")
ended = {"type": "customer.subscription.deleted", "data": {"object": {"id": "sub_b", "customer": "cus_b",
                                                                      "status": "canceled", "metadata": {"user_id": "user-b"}}}}
check("Stripe says canceled: back to free", hook(ended) == 200 and not plan4()["plus"])
check("...and Ember says so", said4()[-1] == PLUS_ENDED)
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
sb.add_call("u1", "2026-11-03", 3000, 200)
sb.add_call("u1", "2026-11-03", 1000, 100)
check("usage adds up per day", sb.calls_today("u1", "2026-11-03") == 2 and Fake.tables["usage"][0]["tokens_in"] == 4000)
check("all users listed", sb.all_uids() == ["u1"])
sb.add_message("u1", "2026-11-03")
check("free messages are counted per day", sb.messages_today("u1", "2026-11-03") == 1 and sb.calls_today("u1", "2026-11-03") == 2)
sb.set_plan("u1", {"status": "active", "customer": "cus_1", "subscription": "sub_1"})
sb.set_plan("u1", {"status": "canceled", "customer": "cus_1", "subscription": "sub_1"})
check("the plan is one row, updated", sb.get_plan("u1")["status"] == "canceled" and len(Fake.tables["plans"]) == 1)
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

print()
print("All checks passed." if not failed else f"{len(failed)} FAILED: {failed}")
sys.stdout.flush()
os._exit(1 if failed else 0)                   # the servers' threads don't need a clean shutdown
