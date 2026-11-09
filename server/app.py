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
import zlib
from contextlib import asynccontextmanager
from urllib.parse import urlparse

from fastapi import Body, FastAPI, HTTPException, Request
from fastapi.exception_handlers import http_exception_handler
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, PlainTextResponse, RedirectResponse, Response
from starlette.exceptions import HTTPException as StarletteHTTPException

from mind import llm
from mind.core import Ember
from .auth import NotInvited, NotLoggedIn
from .billing import PLUS_STATUSES, BillingError
from .push import PushGone
from .store import StoreError

log = logging.getLogger("ember")
WEB = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "web")
PRESENT_FOR = 3.0            # you're here if your visible window asked within this many seconds
SAVE_EVERY = 60.0
# the website: each page gets web/_header.html and web/_footer.html put in at <!--#header--> and <!--#footer-->
SITE = {"/home": "home.html", "/features": "features.html", "/pricing": "pricing.html", "/faq": "faq.html",
        "/about": "about.html", "/privacy": "privacy.html", "/terms": "terms.html"}
PAGES = ("/", *SITE, "/manifest.webmanifest", "/sitemap.xml", "/robots.txt")   # what moves to Ember's own address
IMAGES = {".webp": "image/webp", ".png": "image/png", ".jpg": "image/jpeg", ".svg": "image/svg+xml",
          ".mp4": "video/mp4"}     # the front page's demo video (served in pieces when asked: iPhones only play video that way)
IDLE_FOR = 3600.0            # an Ember nobody has used for an hour leaves memory (saved; it loads again when needed)
MAX_TEXT = 2000
MAX_BODY = 16384
FEEDBACK_KINDS = ("idea", "problem", "other")
FEEDBACK_MAX = 2000
FEEDBACK_PER_HOUR = 10
OWNER_FOR = 60.0             # the owner page's numbers are worked out at most once a minute
PRICE_IN, PRICE_OUT = 0.10 / 1e6, 0.50 / 1e6   # $ per token, Claude Haiku 5.5 (the owner page's cost estimate)
UNREACHABLE = "My mind can't be reached right now. I'll answer as soon as it's back."
FAILED = "Something went wrong when I tried to think about that, so I couldn't answer it. Could you say it another way?"
CAPPED = ("I've reached today's limit for thinking (it keeps Ember affordable). "
          "Everything you write is saved, and I'll answer it tomorrow.")
LAST_FREE = ("That was your last free message for today. With Ember Plus we can keep going without a daily "
             "limit; otherwise I'll be here tomorrow.")
COUNTED = ("talk", "suggest", "checkin")      # what you send that makes Ember think; its greetings are free
OWN = ("arrive", "followup", "month")         # what Ember says on its own: free, and nothing said if it can't
PLUS_ON = "Ember Plus is on. Thank you! There's no daily limit now."
PLUS_ENDED = ("Your Ember Plus has ended, so there's a daily limit of free messages again. "
              "I still remember everything, as always.")


def today(t):
    return time.strftime("%Y-%m-%d", time.gmtime(t))


class User:
    def __init__(self, uid, ember):
        self.uid, self.ember = uid, ember
        self.email = None
        self.plan = False            # Ember Plus as Stripe last reported it (False: not loaded yet)
        self.lock = threading.RLock()
        self.seen_at = 0.0           # last poll from a visible window
        self.used_at = 0.0           # last request or thought (an Ember idle for IDLE_FOR leaves memory)
        self.uses = 0                # counts every use, so eviction can tell it was used while it was saving
        self.saved_at = 0.0
        self.jobs = 0                # thoughts queued or in progress for this person
        self.thinking_in = None      # the chat its latest thought will answer in
        self.feedback_sent = []      # when they sent feedback (at most FEEDBACK_PER_HOUR an hour)


class Users:
    def __init__(self, store, clock):
        self.store, self.clock = store, clock
        self.cache, self.lock = {}, threading.Lock()

    def get(self, uid, email=None, touch=True):
        """touch=False: a look from the background (check-ups, a restart), which doesn't keep it in memory."""
        with self.lock:
            u = self.cache.get(uid)
            if u is None:
                d = self.store.load_self(uid)
                u = User(uid, Ember.from_dict(d) if d else Ember(now=self.clock()))
                self.cache[uid] = u
                if d is None:
                    self.save(u)
            if email:
                u.email = email
            if touch:
                u.used_at = self.clock()
                u.uses += 1
            return u

    def evict(self, idle=None):
        """Embers nobody has used for `idle` seconds leave memory (saved first), so memory stays flat as
        people join. One that's thinking, or was used since, stays. Returns how many left."""
        idle = IDLE_FOR if idle is None else idle
        now, gone = self.clock(), 0
        with self.lock:
            idle_ones = [(u, u.uses) for u in self.cache.values() if u.jobs == 0 and now - u.used_at >= idle]
        for u, uses in idle_ones:
            with u.lock:                            # saved first, while it's still the one in memory
                self.save(u)
            with self.lock:                         # then it leaves, unless someone used it meanwhile
                if self.cache.get(u.uid) is u and u.uses == uses and u.jobs == 0:
                    del self.cache[u.uid]
                    gone += 1
        return gone

    def plan(self, u):
        if u.plan is False:
            try:
                u.plan = self.store.get_plan(u.uid)
            except StoreError as e:
                log.error("plan load failed for %s: %s", u.uid, e)
                return None
        return u.plan

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
    """Several thoughts at once (`threads`), but one person's thoughts always in order on the same thread,
    so an answer is never thought up from a self that's about to change. If the mind is busy or unreachable,
    Ember says so once and the thought is tried again every `retry_every` seconds until it works."""

    def __init__(self, users, cfg, call, clock, daily_cap, retry_delay=10.0, retry_every=60.0, after=None, threads=4):
        self.users, self.cfg, self.call, self.clock, self.after = users, cfg, call, clock, after
        self.daily_cap, self.retry_delay, self.retry_every = daily_cap, retry_delay, retry_every
        self.qs = [queue.Queue() for _ in range(max(1, int(threads)))]
        self.pending, self.plock = [], threading.Lock()

    def start(self):
        for q in self.qs:
            threading.Thread(target=self._work, args=(q,), daemon=True).start()
        threading.Thread(target=self._retry, daemon=True).start()

    def queue_of(self, uid):
        return self.qs[zlib.crc32(uid.encode()) % len(self.qs)]

    def put(self, uid, event):
        u = self.users.get(uid)
        with u.lock:
            u.jobs += 1
            u.thinking_in = u.ember.event_chat(event)
        self.queue_of(uid).put((uid, event))

    def requeue_unanswered(self):
        """After a restart: anyone whose last line in a chat is theirs and unanswered gets an answer."""
        for uid in self.users.store.all_uids():
            try:
                e = self.users.get(uid, touch=False).ember
            except StoreError as err:
                log.error("couldn't load %s: %s", uid, err)
                continue
            for c in e.chats:
                last = e.last_line(c["id"])
                if last and last["who"] == "you":
                    self.put(uid, {"type": "talk", "text": last["text"], "chat": c["id"]})

    def _work(self, q):
        while True:
            uid, event = q.get()
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
        with u.lock:
            if u.ember.gone(event):
                return                              # its chat or goal was deleted meanwhile: nothing to answer
            chat = u.ember.event_chat(event)
        raw = None

        def said_last(text):
            last = u.ember.last_line(chat)
            return last is not None and last["text"] == text
        if self.cfg.usable:
            if store.calls_today(u.uid, day) >= self.daily_cap:
                with u.lock:
                    if event["type"] not in OWN and not said_last(CAPPED):
                        u.ember.say(self.clock(), CAPPED, "calm", chat)
                    self.users.save(u)
                return
            with u.lock:
                system, user = u.ember.prompt(event, self.clock())
            t0 = time.time()
            try:
                raw = self._ask(system, user)
                if not isinstance(llm.parse_json(raw), dict):       # an answer it can't read: once more, and if
                    raw = self._ask(system, user)                   # that fails too, say so (no template answer)
                    if not isinstance(llm.parse_json(raw), dict):
                        raise llm.LLMError("the mind's answer couldn't be read", retryable=False)
            except llm.LLMError as e:
                log.warning("mind failed for %s: %s", u.uid, e)
                if event["type"] in OWN:
                    return                          # no greeting or check-up this time; nothing to say about it
                with u.lock:
                    if e.retryable:
                        if not said_last(UNREACHABLE):
                            u.ember.say(self.clock(), UNREACHABLE, "droopy", chat)
                        with self.plock:
                            self.pending.append((self.clock() + self.retry_every, u.uid, event))
                    else:
                        u.ember.say(self.clock(), FAILED, "calm", chat)
                    self.users.save(u)
                return
            took = time.time() - t0              # how long its mind took (ids and times only, never words)
            (log.warning if took > 20 else log.info)("mind answered %s (%s) in %.1fs", u.uid, event["type"], took)
            usage = llm.take_usage(self.cfg) or (0, 0)
            try:
                store.add_call(u.uid, day, *usage)
            except StoreError as e:
                log.error("usage count failed for %s: %s", u.uid, e)
        with u.lock:
            result = u.ember.respond(event, raw, self.clock())
            if self.after:
                self.after(u, event, result)
            self.users.save(u)


def create_app(store, auth, cfg, call=llm.call_llm, clock=time.time, daily_cap=150,
               retry_delay=10.0, retry_every=60.0, public_config=None, web_dir=WEB,
               billing=None, free_per_day=10, plus_emails=(), checkup_every=300.0, push=None, unlock_emails=(),
               owner_emails=(), mind_threads=4, public_url=None, analytics_token=None):
    users = Users(store, clock)
    plus_emails = {e.strip().lower() for e in plus_emails if e.strip()}
    plus_everyone = "*" in plus_emails             # Plus for everyone, for now (Szilard, 2026-11-06)
    unlock_emails = {e.strip().lower() for e in unlock_emails if e.strip()}

    owner_emails = {e.strip().lower() for e in owner_emails if e.strip()}

    def is_owner(u):                                # the owner page: Szilard (EMBER_OWNER_EMAILS); locally, you
        return auth.mode == "local" or bool(u.email and u.email in owner_emails)

    def all_unlocked(u):                            # testers: every look, without changing the XP (Szilard, 2026-11-06)
        return bool(u.email and u.email in unlock_emails)

    # ------------------------------------------------------------ Ember Plus
    def is_plus(u):
        if auth.mode == "local" or plus_everyone or (u.email and u.email in plus_emails):
            return True
        plan = users.plan(u)
        return bool(plan and plan.get("status") in PLUS_STATUSES)

    def free_left(u, now):
        if is_plus(u):
            return None
        try:
            return max(0, free_per_day - store.messages_today(u.uid, today(now)))
        except StoreError:
            return free_per_day                     # can't count right now: don't punish anyone for it

    def spend_free(u, now):
        """A message that makes Ember think. Free people get free_per_day a day; past that, 402."""
        left = free_left(u, now)
        if left is None:
            return
        if left <= 0:
            raise HTTPException(402, "out of free messages for today")
        try:
            store.add_message(u.uid, today(now))
        except StoreError as e:
            log.error("message count failed for %s: %s", u.uid, e)

    def after_reply(u, event, result=None):
        """Right after its answer to your last free message, Ember says so. A check-up goes to your phone too."""
        if event["type"] in COUNTED and free_left(u, clock()) == 0:
            u.ember.say(clock(), LAST_FREE, "calm", u.ember.event_chat(event), paywall=True)
        if event["type"] == "followup" and result and result.get("reply"):
            notify(u, result["reply"], u.ember.event_chat(event))

    def notify(u, text, chat):
        """A notification on each of your devices, sent in the background; devices that are gone are forgotten."""
        if not push:
            return
        if not u.ember.devices:
            log.info("check-up for %s: no device to notify", u.uid)
            return
        devices = [dict(d) for d in u.ember.devices]
        message = {"title": f"{u.ember.name} sent you a message", "body": text[:180], "chat": chat}

        def send():
            gone, sent = [], 0
            for d in devices:
                try:
                    push.send(d, message)
                    sent += 1
                except PushGone:
                    gone.append(d["endpoint"])
                except Exception as e:              # a push service that's down: this one is missed
                    log.warning("notification failed for %s: %s", u.uid, type(e).__name__)
            log.info("notification for %s: sent to %d of %d device(s)%s", u.uid, sent, len(devices),
                     f", {len(gone)} gone (forgotten; it's sent again when that phone opens Ember)" if gone else "")
            if gone:
                with u.lock:
                    u.ember.devices = [d for d in u.ember.devices if d["endpoint"] not in gone]
                    users.save(u)
        threading.Thread(target=send, daemon=True).start()

    worker = MindWorker(users, cfg, call, clock, daily_cap, retry_delay, retry_every, after=after_reply, threads=mind_threads)

    def checkups():
        """Ember checks up on you even while you're away: every few minutes, the check-ups that are due."""
        while True:
            try:
                for uid in store.all_uids():
                    u = users.get(uid, touch=False)
                    with u.lock:
                        due = u.ember.due_checkups(clock())
                        if due:
                            users.save(u)
                    for event in due:
                        log.info("check-up due for %s: %s", uid, "regular" if event.get("regular") else
                                 "quiet goal" if event.get("auto") else "planned")
                        worker.put(uid, event)
            except Exception as e:                  # keep checking whatever happens
                log.error("check-ups failed: %s", type(e).__name__)
            try:
                gone = users.evict()
                if gone:
                    log.info("%d idle Embers left memory, %d stay", gone, len(users.cache))
            except Exception as e:
                log.error("eviction failed: %s", type(e).__name__)
            time.sleep(checkup_every)

    @asynccontextmanager
    async def lifespan(_app):
        worker.start()
        threading.Thread(target=worker.requeue_unanswered, daemon=True).start()
        threading.Thread(target=checkups, daemon=True).start()
        yield
        for u in list(users.cache.values()):       # a last save on the way down
            with u.lock:
                users.save(u)

    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None, lifespan=lifespan)
    app.state.users, app.state.worker = users, worker

    home_url = (public_url or "").rstrip("/")
    home_host = urlparse(home_url).netloc

    @app.middleware("http")
    async def _headers(request: Request, call_next):
        # pages opened at Render's own address (…onrender.com) move to Ember's address (yourember.app), so links,
        # logins and the home-screen app all live in one place; Ember's API there keeps answering for open windows
        host = request.headers.get("host", "")
        if (home_host and host != home_host and host.endswith(".onrender.com") and request.method in ("GET", "HEAD")
                and request.url.path in PAGES):
            q = ("?" + request.url.query) if request.url.query else ""
            return RedirectResponse(home_url + request.url.path + q, status_code=301)
        if request.method == "POST" and request.url.path == "/stripe/webhook":
            if int(request.headers.get("content-length") or 0) > 512 * 1024:
                return JSONResponse({"error": "too large"}, status_code=413)
        elif request.method == "POST":
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
        if request.url.path.startswith("/img/"):
            r.headers["Cache-Control"] = "public, max-age=86400"
        elif request.url.path not in ("/sw.js",) and not request.url.path.startswith("/icons/"):
            r.headers["Cache-Control"] = "no-store"
        return r

    def who(request: Request):
        h = request.headers.get("authorization", "")
        token = h[7:] if h.lower().startswith("bearer ") else None
        try:
            me = auth.user(token)
            return users.get(me["id"], me.get("email"))
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

    def read(name):
        with open(os.path.join(web_dir, name), encoding="utf-8") as f:
            return f.read()

    # Cloudflare Web Analytics (2026-11-09, Szilard: who visits the site): visits per page, where people came from,
    # country and device; no cookies, no personal data. Only online (never this computer's Ember or the checks), on
    # every page the server sends: the website and the app. The token isn't secret: it's in every page anyway.
    beacon = (f"<script type=\"module\" src=\"https://static.cloudflareinsights.com/beacon.min.js\" "
              f"data-cf-beacon='{{\"token\": \"{analytics_token}\"}}'></script>") if analytics_token else ""

    def counted(html):
        return html.replace("</body>", beacon + "</body>", 1) if beacon else html

    @app.get("/")
    def index():
        # online, the window knows it from its first line, so a stranger goes straight to the front page (/home)
        # before anything is drawn (the script at the top of index.html); this computer's Ember has no front page
        html = read("index.html")
        if auth.mode == "online":
            html = html.replace('<html lang="en">', '<html lang="en" data-mode="online">', 1)
        return HTMLResponse(counted(html))

    def site_page(name, path=None, status=200):
        """A page of the website with its header (this page's link marked) and footer put in."""
        header = read("_header.html")
        if path:
            header = header.replace(f'<a href="{path}">', f'<a href="{path}" aria-current="page">')
        html = read(name).replace("<!--#header-->", header).replace("<!--#footer-->", read("_footer.html"))
        return HTMLResponse(counted(html), status_code=status)

    def site_route(path, name):
        app.add_api_route(path, lambda: site_page(name, path), methods=["GET"], include_in_schema=False)

    for path, name in SITE.items():       # /home is the public front page (also Google Branding's home page);
        site_route(path, name)            # /terms is TermsFeed's text plus Plus, cancelling and withdrawal

    @app.get("/site.css")
    def site_css():
        return page("site.css", "text/css; charset=utf-8")

    @app.get("/site.js")
    def site_js():
        return page("site.js", "application/javascript")

    @app.get("/img/{name}")
    def site_image(name: str):
        kind = IMAGES.get(os.path.splitext(name)[1].lower())
        path = os.path.join(web_dir, "img", name)
        if "/" in name or "\\" in name or not kind or not os.path.exists(path):
            raise HTTPException(404)
        return FileResponse(path, media_type=kind)

    @app.get("/sitemap.xml")
    def sitemap():
        home = (public_url or "https://yourember.app").rstrip("/")
        urls = "".join(f"<url><loc>{home}{p}</loc></url>" for p in SITE)
        return Response('<?xml version="1.0" encoding="UTF-8"?>'
                        f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>',
                        media_type="application/xml")

    @app.get("/robots.txt")
    def robots():
        home = (public_url or "https://yourember.app").rstrip("/")
        return PlainTextResponse(f"User-agent: *\nAllow: /\nSitemap: {home}/sitemap.xml\n")

    @app.exception_handler(StarletteHTTPException)
    async def not_found(request: Request, exc):
        # a person's browser asking for a page that isn't there gets the website's own page; everything else
        # (the window's own calls) keeps the usual answer
        if (exc.status_code == 404 and request.method == "GET"
                and "text/html" in request.headers.get("accept", "")):
            return site_page("404.html", status=404)
        return await http_exception_handler(request, exc)

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
        return dict(public_config or {}, mode=auth.mode, vapid_public=push.public if push else None,
                    terms_url=billing.terms_url if billing else None)

    # ------------------------------------------------------------ Ember
    @app.get("/state")
    def state(request: Request, v: int = 0, chat: str = "", tz: int = None):
        u = who(request)
        now = clock()
        with u.lock:
            e = u.ember
            if tz is not None:
                e.tz = max(-840, min(840, tz))     # your clock: Ember's sense of your day, and its quiet nights
            chat = e.find_chat(chat)["id"]          # the chat you have open (none: your latest)
            if v == 1:
                if now - u.seen_at >= PRESENT_FOR:             # you've come back
                    greet = e.arrive(now, chat)
                    month = e.month_due(now)                 # a new month: its note on the last one (instead of a
                    if month:                                # greeting; on its page, never a notification)
                        e.month_asked = {"month": month, "t": now}
                        worker.put(u.uid, {"type": "month", "month": month})
                    elif greet:
                        worker.put(u.uid, {"type": "arrive", "chat": chat})
                u.seen_at = now
            present = now - u.seen_at < PRESENT_FOR
            e.update(now, present)
            s = e.snapshot(now, present, u.jobs > 0, chat)
            s["thinking_in"] = u.thinking_in
            if now - u.saved_at > SAVE_EVERY:
                users.save(u)
        plan = users.plan(u) if auth.mode != "local" else None
        s["plan"] = {"plus": is_plus(u), "free_left": free_left(u, now), "free_per_day": free_per_day,
                     "price": billing.price_label if billing else None,
                     "price_year": billing.yearly_label if billing else None,
                     "payments": bool(billing and billing.selling),
                     # Manage Ember Plus: only for a subscription that's running (an old or test one can't be managed)
                     "manage": bool(billing and billing.enabled and plan and plan.get("customer")
                                    and plan.get("status") in PLUS_STATUSES)}
        s["owner"] = is_owner(u)
        return s

    @app.get("/memory")
    def memory(request: Request):
        u = who(request)
        with u.lock:
            return u.ember.memory_page(clock())

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
            spend_free(u, now)
            chat = u.ember.find_chat(body.get("chat"))["id"]
            u.ember.hear(now, text, chat)
            worker.put(u.uid, {"type": "talk", "text": text, "chat": chat})
            return True
        return act(request, f)

    @app.post("/chat/delete")
    def chat_delete(request: Request, body: dict = Body(default={})):
        """You deleted a chat: its lines (in the store too), its goals and its planned check-ups."""
        u = who(request)
        cid = str(body.get("id") or "")
        with u.lock:
            if not any(c["id"] == cid for c in u.ember.chats):
                raise HTTPException(404, "no such chat")
            if u.jobs > 0 and u.thinking_in == cid:
                raise HTTPException(409, "Ember is still answering there")
            try:
                store.delete_lines(u.uid, cid)
            except StoreError as e:
                log.error("deleting a chat failed for %s: %s", u.uid, e)
                raise HTTPException(503, "couldn't delete it right now")
            u.ember.delete_chat(cid, clock())
            users.save(u)
            log.info("chat deleted for %s", u.uid)
            return {"ok": True, "chat": u.ember.latest_chat()["id"]}

    @app.post("/goal/delete")
    def goal_delete(request: Request, body: dict = Body(default={})):
        return act(request, lambda u, now: u.ember.delete_goal(body.get("id"), now))

    @app.post("/chat/rename")
    def chat_rename(request: Request, body: dict = Body(default={})):
        return act(request, lambda u, now: u.ember.rename_chat(body.get("id"), body.get("title", "")))

    @app.get("/badges")
    def badges(request: Request):                   # every badge, earned or not (the window celebrates new ones)
        u = who(request)
        with u.lock:
            return {"badges": u.ember.badge_list(clock())}

    @app.get("/looks")
    def looks(request: Request):
        u = who(request)
        with u.lock:
            return u.ember.looks(all_unlocked(u))

    @app.post("/look")
    def look_set(request: Request, body: dict = Body(default={})):
        return act(request, lambda u, now: u.ember.set_look(body.get("part"), body.get("value"), all_unlocked(u)))

    @app.post("/name")
    def name_set(request: Request, body: dict = Body(default={})):
        return act(request, lambda u, now: u.ember.set_name(body.get("name", ""), now))

    @app.post("/checkups")
    def checkups_set(request: Request, body: dict = Body(default={})):
        at = body.get("at")
        if at is None and body.get("hour") is not None:               # a window from before minutes and days
            at = f"{body.get('hour')}:00"
        return act(request, lambda u, now: u.ember.set_checkups(body.get("every"), at, body.get("days")))

    @app.post("/push/subscribe")
    def push_subscribe(request: Request, body: dict = Body(default={})):
        sub = body.get("subscription") or {}
        keys = sub.get("keys") or {}
        endpoint = str(sub.get("endpoint", ""))
        if not push or not endpoint.startswith("https://") or not keys.get("p256dh") or not keys.get("auth"):
            raise HTTPException(400, "subscription")

        def f(u, now):
            devices = [d for d in u.ember.devices if d["endpoint"] != endpoint]
            devices.append({"endpoint": endpoint, "keys": {"p256dh": str(keys["p256dh"]), "auth": str(keys["auth"])},
                            "added": now})
            u.ember.devices = devices[-10:]
            return True
        return act(request, f)

    @app.post("/push/unsubscribe")
    def push_unsubscribe(request: Request, body: dict = Body(default={})):
        def f(u, now):
            u.ember.devices = [d for d in u.ember.devices if d["endpoint"] != body.get("endpoint")]
            return True
        return act(request, f)

    @app.post("/chat/new")
    def chat_new(request: Request):
        u = who(request)
        with u.lock:
            cid = u.ember.new_chat(clock())
            users.save(u)
        return {"ok": True, "id": cid}

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
    def suggest(request: Request, body: dict = Body(default={})):
        def f(u, now):
            chat = u.ember.find_chat(body.get("chat"))["id"]
            ok = u.ember.can_suggest(chat)
            if ok:
                spend_free(u, now)
                worker.put(u.uid, {"type": "suggest", "chat": chat})
            return ok
        return act(request, f)

    @app.post("/experiment/pick")
    def pick(request: Request, body: dict = Body(default={})):
        return act(request, lambda u, now: u.ember.pick(body.get("id"), now))

    @app.post("/experiment/step")
    def step(request: Request, body: dict = Body(default={})):
        return act(request, lambda u, now: u.ember.set_step(body.get("id"), body.get("index"), body.get("done"), now))

    @app.post("/experiment/end")
    def end(request: Request, body: dict = Body(default={})):
        def f(u, now):
            ok = u.ember.end_experiment(body.get("id"), body.get("how"), now)
            if ok:
                worker.put(u.uid, {"type": "review", "id": body.get("id")})   # it looks back; not a free message
            return ok
        return act(request, f)

    @app.post("/experiment/extend")
    def extend(request: Request, body: dict = Body(default={})):
        return act(request, lambda u, now: u.ember.extend(body.get("id"), now))

    # ------------------------------------------------------------ goals of their own
    @app.get("/goals")
    def goals(request: Request):
        u = who(request)
        with u.lock:
            return {"goals": u.ember.goals(clock())}

    @app.post("/goal/new")
    def goal_new(request: Request, body: dict = Body(default={})):
        u = who(request)
        now = clock()
        with u.lock:
            if body.get("with_ember"):                       # talk it through with Ember: that's a message
                spend_free(u, now)
                event = u.ember.plan_with_ember(body.get("title"), now)
                if event:
                    worker.put(u.uid, event)
                out = {"ok": bool(event), "chat": event and event["chat"]}
            else:
                steps = body.get("steps") if isinstance(body.get("steps"), list) else []
                x = u.ember.new_goal(body.get("title"), body.get("done_when"), body.get("days", 30), steps, now,
                                     n=body.get("n"), unit=body.get("unit"))
                out = {"ok": bool(x), "id": x and x["id"], "chat": x and x["chat"]}
            users.save(u)
        return out

    @app.post("/goal/check")
    def goal_check(request: Request, body: dict = Body(default={})):
        def f(u, now):
            event = u.ember.daily_check(body.get("id"), body.get("how"), str(body.get("words", ""))[:MAX_TEXT], now)
            if event and event.pop("first"):                 # Ember answers the first check of the day
                worker.put(u.uid, event)
            return event is not None
        return act(request, f)

    @app.post("/goal/phase")
    def goal_phase(request: Request, body: dict = Body(default={})):
        def f(u, now):
            x = u.ember.find_exp(body.get("id"))
            if not x or x["status"] != "active" or not x.get("phases") or x["phase"] >= len(x["phases"]) - 1:
                return False
            p = x.get("phase_pending") or {}
            if p.get("phase") == x["phase"] and now - p.get("t", 0) < 120:
                return True                                  # already asked (a second tap); after 2 minutes, again
            x["phase_pending"] = {"phase": x["phase"], "t": now}
            worker.put(u.uid, {"type": "phase", "id": x["id"], "from": x["phase"]})   # it looks back and plans the
            return True                                                              # next; not a free message
        return act(request, f)

    @app.post("/goal/step")
    def goal_step(request: Request, body: dict = Body(default={})):
        return act(request, lambda u, now: u.ember.add_step(body.get("id"), body.get("text")))

    @app.post("/session/start")
    def session_start(request: Request, body: dict = Body(default={})):
        return act(request, lambda u, now: u.ember.start_session(now, body.get("chat")))

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
            if u.ember.checkin_due:
                spend_free(u, now)
            event = u.ember.checkin(now, rating, str(body.get("words", "")).strip()[:MAX_TEXT])
            if event:
                worker.put(u.uid, event)
            return event is not None
        return act(request, f)

    # ------------------------------------------------------------ feedback
    @app.post("/feedback")
    def feedback(request: Request, body: dict = Body(default={})):
        u = who(request)
        text = str(body.get("text") or "").strip()[:FEEDBACK_MAX]
        kind = body.get("kind") if body.get("kind") in FEEDBACK_KINDS else "other"
        if not text:
            raise HTTPException(400, "write something first")
        now = clock()
        with u.lock:
            sent = [t for t in u.feedback_sent if now - t < 3600]
            if len(sent) >= FEEDBACK_PER_HOUR:
                raise HTTPException(429, "that's a lot of feedback for one hour; try again later")
            e = u.ember
            extra = {"level": e.level_info()["level"],
                     "plus": is_plus(u), "screen": str(body.get("screen") or "")[:40],
                     "agent": request.headers.get("user-agent", "")[:200]}
            try:
                users.store.add_feedback(u.uid, {"t": now, "email": u.email, "kind": kind, "text": text, "extra": extra})
            except StoreError as err:
                log.error("feedback failed for %s: %s", u.uid, err)
                raise HTTPException(503, "couldn't send it right now; try again") from None
            u.feedback_sent = sent + [now]
        log.info("feedback from %s (%s)", u.uid, kind)       # never what they wrote
        return {"ok": True}

    # ------------------------------------------------------------ the owner page
    owner_cache = {}

    def owner_numbers(now):
        """Who uses Ember and whether they come back: counts only, never what anyone said or wants."""
        emails = store.emails()
        plans = store.all_plans()
        people = []
        for uid in store.all_uids():
            u = users.cache.get(uid)
            if u:
                with u.lock:
                    v = u.ember.owner_view(now)
            else:
                d = store.load_self(uid)
                if not d:
                    continue
                v = Ember.from_dict(d).owner_view(now)
            email = emails.get(uid) or (u.email if u else None)
            plan = plans.get(uid) or {}
            v.update(email=email, plus="everyone" if plus_everyone else "gift" if email and email.lower() in plus_emails
                     else "paying" if plan.get("status") in PLUS_STATUSES else "")
            people.append(v)
        people.sort(key=lambda p: -(p["last"] or p["joined"] or 0))
        old = [p for p in people if p["joined"] <= now - 7 * 86400]
        day0, day29 = today(now), today(now - 29 * 86400)
        rows = store.usage_since(day29)

        def cost(rs):
            t = {k: sum(r.get(k) or 0 for r in rs) for k in ("calls", "messages", "tokens_in", "tokens_out")}
            t["usd"] = round(t["tokens_in"] * PRICE_IN + t["tokens_out"] * PRICE_OUT, 4)
            return t
        feedback = [{"t": f.get("t"), "kind": f.get("kind"), "text": f.get("text"),
                     "email": f.get("email") or emails.get(f.get("user_id"))} for f in store.all_feedback(50)]
        return {"at": now, "people": len(people), "today": sum(p["today"] for p in people),
                "week": sum(1 for p in people if p["last"] and p["last"] >= now - 7 * 86400),
                "new_week": sum(1 for p in people if p["joined"] >= now - 7 * 86400),
                "retention": {"joined_before": len(old), "back_day2": sum(p["back_day2"] for p in old),
                              "back_week2": sum(p["back_week2"] for p in old)},
                "cost": {"today": cost([r for r in rows if str(r["day"]) == day0]), "month": cost(rows)},
                "list": people, "feedback": feedback}

    @app.get("/owner/data")
    def owner_data(request: Request):
        u = who(request)
        if not is_owner(u):
            raise HTTPException(404, "not found")
        now = clock()
        if not owner_cache or now - owner_cache["at"] > OWNER_FOR:
            try:
                owner_cache.clear()
                owner_cache.update(owner_numbers(now))
            except StoreError as e:
                log.error("owner page failed: %s", e)
                raise HTTPException(503, "couldn't read the database right now; try again") from None
        return owner_cache

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
            plan = users.plan(u)
            if billing and billing.enabled and plan and plan.get("subscription") and plan.get("status") in PLUS_STATUSES:
                try:                                # deleting your Ember also stops the payments
                    billing.cancel(plan["subscription"])
                except BillingError as e:
                    log.error("cancel failed for %s: %s", u.uid, e)
                    raise HTTPException(503, "couldn't cancel your Ember Plus right now; nothing was deleted, try again") from None
            try:
                users.store.delete_user(u.uid)
            except StoreError as e:
                log.error("delete failed for %s: %s", u.uid, e)
                raise HTTPException(503, "couldn't delete right now; nothing was half-deleted on purpose, try again") from None
            users.drop(u.uid)
        return {"ok": True}

    # ------------------------------------------------------------ paying
    def base_url(request):
        return str(request.base_url).rstrip("/")

    @app.post("/plus/checkout")
    def plus_checkout(request: Request, body: dict = Body(default={})):
        u = who(request)
        yearly = bool(isinstance(body, dict) and body.get("yearly"))
        if not (billing and billing.selling):          # a live key without the terms online sells nothing yet
            raise HTTPException(503, "Ember Plus opens soon")
        plan = users.plan(u)
        try:
            return {"url": billing.checkout(u.uid, u.email, plan and plan.get("customer"), base_url(request), yearly)}
        except BillingError as e:
            log.error("checkout failed for %s: %s", u.uid, e)
            raise HTTPException(503, "couldn't reach the payment page, try again") from None

    @app.post("/plus/portal")
    def plus_portal(request: Request):
        u = who(request)
        plan = users.plan(u)
        if not (billing and billing.enabled and plan and plan.get("customer")):
            raise HTTPException(404, "no subscription")
        try:
            return {"url": billing.portal(plan["customer"], base_url(request))}
        except BillingError as e:
            if e.code != "resource_missing":
                log.error("portal failed for %s: %s", u.uid, e)
                raise HTTPException(503, "couldn't reach the payment page, try again") from None
        # Stripe doesn't know this customer (say, one from test mode): nothing to manage, so the plan is forgotten
        # and they get the payment page instead
        log.info("stale Stripe customer for %s forgotten", u.uid)
        stale = {"status": "gone", "customer": None, "subscription": None}
        try:
            users.store.set_plan(u.uid, stale)
        except StoreError as e:
            log.error("plan save failed for %s: %s", u.uid, e)
        u.plan = stale
        if not billing.selling:
            raise HTTPException(404, "no subscription")
        try:
            return {"url": billing.checkout(u.uid, u.email, None, base_url(request))}
        except BillingError as e:
            log.error("checkout failed for %s: %s", u.uid, e)
            raise HTTPException(503, "couldn't reach the payment page, try again") from None

    @app.post("/stripe/webhook")
    async def stripe_webhook(request: Request):
        if not (billing and billing.enabled):
            raise HTTPException(404)
        payload = await request.body()
        try:
            event = billing.verify(payload, request.headers.get("stripe-signature", ""), clock())
        except (BillingError, ValueError) as e:
            log.warning("webhook refused: %s", e)
            raise HTTPException(400, "bad signature") from None
        found = billing.plan_from_event(event, billing.prices)
        if found:
            uid, plan = found
            try:
                if store.load_self(uid) is None:    # no such Ember (deleted since): nothing to change, no retries
                    log.info("plan event for unknown %s ignored", uid)
                    return {"received": True}
                before = store.get_plan(uid)
                store.set_plan(uid, plan)
            except StoreError as e:
                log.error("plan save failed for %s: %s", uid, e)
                raise HTTPException(503, "try again") from None        # Stripe retries
            cached = users.cache.get(uid)
            if cached:
                cached.plan = plan
            was, now_plus = bool(before and before.get("status") in PLUS_STATUSES), plan.get("status") in PLUS_STATUSES
            if was != now_plus and store.load_self(uid) is not None:     # Ember says so in the conversation, once
                u = users.get(uid)
                with u.lock:
                    u.ember.say(clock(), PLUS_ON if now_plus else PLUS_ENDED, "happy" if now_plus else "calm")
                    users.save(u)
            log.info("plan for %s is now %s", uid, plan.get("status"))
        return {"received": True}

    return app
