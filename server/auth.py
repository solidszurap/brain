"""
Who is asking. Online, the window logs in with Google through Supabase and sends
its access token with every request; the server asks Supabase whose token it is
(cached for a few minutes) and checks the invite list. In local mode there is
one person, you, and no login.
"""
import json
import threading
import time
import urllib.error
import urllib.request

CACHE_SECONDS = 300


class NotLoggedIn(Exception):
    pass


class NotInvited(Exception):
    pass


class LocalAuth:
    mode = "local"

    def user(self, token):
        return {"id": "local", "email": None}


class SupabaseAuth:
    mode = "online"

    def __init__(self, url, anon_key, allowed="", timeout=10):
        self.url, self.anon, self.timeout = url.rstrip("/"), anon_key, timeout
        allowed = (allowed or "").strip()
        self.everyone = allowed == "*"
        self.allowed = {e.strip().lower() for e in allowed.split(",") if e.strip() and e.strip() != "*"}
        self.cache, self.lock = {}, threading.Lock()

    def user(self, token):
        if not token:
            raise NotLoggedIn()
        now = time.time()
        with self.lock:
            hit = self.cache.get(token)
            if hit and hit[1] > now:
                return self._invited(hit[0])
        req = urllib.request.Request(self.url + "/auth/v1/user",
                                     headers={"apikey": self.anon, "Authorization": f"Bearer {token}"})
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as r:
                u = json.loads(r.read())
        except urllib.error.HTTPError:
            raise NotLoggedIn() from None
        except (urllib.error.URLError, TimeoutError):
            raise NotLoggedIn() from None
        user = {"id": u["id"], "email": (u.get("email") or "").lower()}
        with self.lock:
            if len(self.cache) > 5000:
                self.cache = {k: v for k, v in self.cache.items() if v[1] > now}
            self.cache[token] = (user, now + CACHE_SECONDS)
        return self._invited(user)

    def _invited(self, user):
        if self.everyone or user["email"] in self.allowed:
            return user
        raise NotInvited(user["email"])
