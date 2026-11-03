"""
Ember's server: every person gets their own Ember.

Each request says who it is (online: a Supabase login token; local mode: just
you). The server keeps each person's Ember in memory, lets real time act on it
lazily whenever their window asks for its state, hands their words to the mind
worker (one LLM call at a time), and saves everything to the store.

create_app(...) builds it; `python -m server` (online) and `python ember.py`
(local) run it.
"""
import logging
import os
import queue
import threading
import time
from contextlib import asynccontextmanager
from urllib.parse import urlparse

from fastapi import Body, FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, Response

from mind import llm
from mind.core import MIN_MEMORIES, Ember
from .auth import NotInvited, NotLoggedIn
from .store import StoreError

log = logging.getLogger("ember")
WEB = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "web")
PRESENT_FOR = 3.0            # you're here if your visible window asked within this many seconds
SAVE_EVERY = 60.0
MAX_TEXT = 2000
MAX_BODY = 16384
UNREACHABLE = "My mind can't be reached right now. I'll answer as soon as it's back."
FAILED = "Something went wrong when I tried to think about that, so I couldn't answer it. Could you say it another way?"
CAPPED = ("I've reached today's limit for thinking (it keeps Ember affordable). "
          "Everything you write is saved, and I'll answer it tomorrow.")


class User:
    def __init__(self, uid, ember):
        self.uid, self.ember = uid, ember
        self.lock = threading.RLock()
        self.seen_at = 0.0           # last poll from a visible window
        self.saved_at = 0.0
        self.jobs = 0                # thoughts queued or in progress for this person


class Users:
    def __init__(self, store, clock):
        self.store, self.clock = store, clock
        self.cache, self.lock = {}, threading.Lock()

    def get(self, uid):
        with self.lock:
            u = self.cache.get(uid)
            if u is None:
                d = self.store.load_self(uid)
                u = User(uid, Ember.from_dict(d) if d else Ember(now=self.clock()))
                self.cache[uid] = u
                if d is None:
                    self.save(u)
            return u

    def save(self, u):
        """Lines first (append only), then the self. A failed save keeps the lines for next time."""
        try:
            self.store.append_lines(u.uid, u.ember.outbox)
            u.ember.outbox = []
            self.store.save_self(u.uid, u.ember.to_dict())
            u.saved_at = self.clock()
        except StoreError as e:
            log.error("save failed for %s: %s", u.uid, e)

    def drop(self, uid):
        with self.lock:
            self.cache.pop(uid, None)


class MindWorker:
    """One thought at a time. If the mind is busy or unreachable, Ember says so once and
    the thought is tried again every `retry_every` seconds until it works."""

    def __init__(self, users, cfg, call, clock, daily_cap, retry_delay=10.0, retry_every=60.0):
        self.users, self.cfg, self.call, self.clock = users, cfg, call, clock
        self.daily_cap, self.retry_delay, self.retry_every = daily_cap, retry_delay, retry_every
        self.q, self.pending, self.plock = queue.Queue(), [], threading.Lock()

    def start(self):
        threading.Thread(target=self._work, daemon=True).start()
        threading.Thread(target=self._retry, daemon=True).start()

    def put(self, uid, event):
        u = self.users.get(uid)
        with u.lock:
            u.jobs += 1
        self.q.put((uid, event))

    def requeue_unanswered(self):
        """After a restart: anyone whose last line is theirs and unanswered gets an answer."""
        for uid in self.users.store.all_uids():
            try:
                talk = self.users.get(uid).ember.talk
            except StoreError as e:
                log.error("couldn't load %s: %s", uid, e)
                continue
            if talk and talk[-1]["who"] == "you":
                self.put(uid, {"type": "talk", "text": talk[-1]["text"]})

    def _work(self):
        while True:
            uid, event = self.q.get()
            u = self.users.get(uid)
            try:
                self._think(u, event)
            except Exception:                       # keep the worker alive whatever happens
                log.exception("mind error for %s", uid)
            finally:
                with u.lock:
                    u.jobs -= 1

    def _retry(self):
        while True:
            time.sleep(min(5.0, self.retry_every))
            now = self.clock()
            with self.plock:
                due = [p for p in self.pending if p[0] <= now]
                self.pending = [p for p in self.pending if p[0] > now]
            for _, uid, event in due:
                self.put(uid, event)

    def _ask(self, system, user):
        try:
            return self.call(self.cfg, system, user, json_mode=True)
        except llm.LLMError as e:
            if not e.retryable:
                raise
            time.sleep(self.retry_delay)            # one more try of our own, after the SDK's retries
            return self.call(self.cfg, system, user, json_mode=True)

    def _think(self, u, event):
        store, day = self.users.store, time.strftime("%Y-%m-%d", time.gmtime(self.clock()))
        raw = None
        if self.cfg.usable:
            if store.calls_today(u.uid, day) >= self.daily_cap:
                with u.lock:
                    if event["type"] != "arrive" and (not u.ember.talk or u.ember.talk[-1]["text"] != CAPPED):
                        u.ember.say(self.clock(), CAPPED, "calm")
                    self.users.save(u)
                return
            with u.lock:
                system, user = u.ember.prompt(event, self.clock())
            try:
                raw = self._ask(system, user)
            except llm.LLMError as e:
                log.warning("mind failed for %s: %s", u.uid, e)
                if event["type"] == "arrive":
                    return                          # no greeting this time; nothing to say about it
                with u.lock:
                    if e.retryable:
                        if not u.ember.talk or u.ember.talk[-1]["text"] != UNREACHABLE:
                            u.ember.say(self.clock(), UNREACHABLE, "droopy")
                        with self.plock:
                            self.pending.append((self.clock() + self.retry_every, u.uid, event))
                    else:
                        u.ember.say(self.clock(), FAILED, "calm")
                    self.users.save(u)
                return
            usage = getattr(self.cfg, "last_usage", None) or (0, 0)
            try:
                store.add_call(u.uid, day, *usage)
            except StoreError as e:
                log.error("usage count failed for %s: %s", u.uid, e)
        with u.lock:
            u.ember.respond(event, raw, self.clock())
            self.users.save(u)


def create_app(store, auth, cfg, call=llm.call_llm, clock=time.time, daily_cap=150,
               retry_delay=10.0, retry_every=60.0, public_config=None, web_dir=WEB):
    users = Users(store, clock)
    worker = MindWorker(users, cfg, call, clock, daily_cap, retry_delay, retry_every)

    @asynccontextmanager
    async def lifespan(_app):
        worker.start()
        threading.Thread(target=worker.requeue_unanswered, daemon=True).start()
        yield
        for u in list(users.cache.values()):       # a last save on the way down
            with u.lock:
                users.save(u)

    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None, lifespan=lifespan)
    app.state.users, app.state.worker = users, worker

    @app.middleware("http")
    async def _headers(request: Request, call_next):
        if request.method == "POST":
            if int(request.headers.get("content-length") or 0) > MAX_BODY:
                return JSONResponse({"error": "too large"}, status_code=413)
            # only Ember's own window may act: a custom header (forces a CORS preflight this
            # server never answers) and, when the browser says where it came from, the same host
            origin = request.headers.get("origin")
            if request.headers.get("x-ember") != "1" or (origin and urlparse(origin).netloc != request.headers.get("host")):
                return JSONResponse({"error": "forbidden"}, status_code=403)
        r = await call_next(request)
        r.headers["X-Content-Type-Options"] = "nosniff"
        r.headers["Referrer-Policy"] = "no-referrer"
        r.headers["X-Frame-Options"] = "DENY"
        if request.url.path not in ("/sw.js",) and not request.url.path.startswith("/icons/"):
            r.headers["Cache-Control"] = "no-store"
        return r

    def who(request: Request):
        h = request.headers.get("authorization", "")
        token = h[7:] if h.lower().startswith("bearer ") else None
        try:
            return users.get(auth.user(token)["id"])
        except NotLoggedIn:
            raise HTTPException(401, "log in") from None
        except NotInvited:
            raise HTTPException(403, "not invited") from None
        except StoreError as e:
            log.error("load failed: %s", e)
            raise HTTPException(503, "storage unavailable") from None

    # ------------------------------------------------------------ pages
    def page(name, media=None):
        return FileResponse(os.path.join(web_dir, name), media_type=media)

    @app.get("/")
    def index():
        return page("index.html", "text/html; charset=utf-8")

    @app.get("/privacy")
    def privacy():
        return page("privacy.html", "text/html; charset=utf-8")

    @app.get("/manifest.webmanifest")
    def manifest():
        return page("manifest.webmanifest", "application/manifest+json")

    @app.get("/sw.js")
    def sw():
        return page("sw.js", "application/javascript")

    @app.get("/icons/{name}")
    def icon(name: str):
        if "/" in name or "\\" in name or not name.endswith(".png"):
            raise HTTPException(404)
        path = os.path.join(web_dir, "icons", name)
        if not os.path.exists(path):
            raise HTTPException(404)
        return FileResponse(path, media_type="image/png")

    @app.get("/config")
    def config():
        return dict(public_config or {}, mode=auth.mode)

    # ------------------------------------------------------------ Ember
    @app.get("/state")
    def state(request: Request, v: int = 0):
        u = who(request)
        now = clock()
        with u.lock:
            e = u.ember
            if v == 1:
                if now - u.seen_at >= PRESENT_FOR and e.arrive(now):
                    worker.put(u.uid, {"type": "arrive"})
                u.seen_at = now
            present = now - u.seen_at < PRESENT_FOR
            e.update(now, present)
            s = e.snapshot(now, present, u.jobs > 0)
            if now - u.saved_at > SAVE_EVERY:
                users.save(u)
        s["mind"] = cfg.describe()
        return s

    @app.get("/memory")
    def memory(request: Request):
        u = who(request)
        with u.lock:
            return u.ember.memory_page()

    def act(request, fn):
        u = who(request)
        with u.lock:
            ok = fn(u, clock())
            users.save(u)
        return {"ok": bool(ok)}

    @app.post("/talk")
    def talk(request: Request, body: dict = Body(default={})):
        text = str(body.get("text", "")).strip()[:MAX_TEXT]
        if not text:
            raise HTTPException(400, "empty")

        def f(u, now):
            u.ember.hear(now, text)
            worker.put(u.uid, {"type": "talk", "text": text})
            return True
        return act(request, f)

    @app.post("/poke")
    def poke(request: Request):
        return act(request, lambda u, now: u.ember.poke(now) or True)

    @app.post("/memory/edit")
    def memory_edit(request: Request, body: dict = Body(default={})):
        return act(request, lambda u, now: u.ember.edit_memory(body.get("id"), body.get("note", ""), now))

    @app.post("/memory/forget")
    def memory_forget(request: Request, body: dict = Body(default={})):
        return act(request, lambda u, now: u.ember.forget(body.get("id")))

    @app.post("/experiment/suggest")
    def suggest(request: Request):
        def f(u, now):
            ok = u.ember.can_suggest() or len(u.ember.memories) < MIN_MEMORIES
            if ok:
                worker.put(u.uid, {"type": "suggest"})
            return ok
        return act(request, f)

    @app.post("/experiment/pick")
    def pick(request: Request, body: dict = Body(default={})):
        return act(request, lambda u, now: u.ember.pick(body.get("id"), now))

    @app.post("/experiment/step")
    def step(request: Request, body: dict = Body(default={})):
        return act(request, lambda u, now: u.ember.set_step(body.get("id"), body.get("index"), body.get("done")))

    @app.post("/experiment/end")
    def end(request: Request, body: dict = Body(default={})):
        return act(request, lambda u, now: u.ember.end_experiment(body.get("id"), body.get("how"), now))

    @app.post("/session/start")
    def session_start(request: Request):
        return act(request, lambda u, now: u.ember.start_session(now))

    @app.post("/session/stop")
    def session_stop(request: Request):
        return act(request, lambda u, now: u.ember.stop_session(now) is not None)

    @app.post("/session/checkin")
    def session_checkin(request: Request, body: dict = Body(default={})):
        try:
            rating = max(1, min(5, int(body.get("rating"))))
        except (TypeError, ValueError):
            raise HTTPException(400, "rating") from None

        def f(u, now):
            event = u.ember.checkin(now, rating, str(body.get("words", "")).strip()[:MAX_TEXT])
            if event:
                worker.put(u.uid, event)
            return event is not None
        return act(request, f)

    # ------------------------------------------------------------ your data
    @app.get("/me/export")
    def export(request: Request):
        u = who(request)
        with u.lock:
            users.save(u)
            data = users.store.export(u.uid)
        return JSONResponse(data, headers={"Content-Disposition": 'attachment; filename="my-ember.json"'})

    @app.post("/me/delete")
    def delete(request: Request):
        u = who(request)
        with u.lock:
            try:
                users.store.delete_user(u.uid)
            except StoreError as e:
                log.error("delete failed for %s: %s", u.uid, e)
                raise HTTPException(503, "couldn't delete right now; nothing was half-deleted on purpose, try again") from None
            users.drop(u.uid)
        return {"ok": True}

    return app
