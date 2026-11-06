"""
Where each person's Ember lives. One small interface, two places:

  FileStore      a folder on this computer (local mode, and the checks)
  SupabaseStore  the Postgres database at Supabase (online), reached only from the
                 server with the service key, through Supabase's REST API (urllib)

Per user: the Ember's self (one JSON document), every conversation line (append
only), counts per day (mind calls, the cost guard; messages, the free limit), and
their plan (Ember Plus, as Stripe last reported it).
"""
import json
import os
import shutil
import threading
import time
import urllib.error
import urllib.parse
import urllib.request


class StoreError(Exception):
    pass


def _line_row(uid, line):
    extra = {k: v for k, v in line.items() if k not in ("t", "who", "text")}
    return {"user_id": uid, "t": line["t"], "who": line["who"], "text": line["text"], "extra": extra or None}


def _row_line(row):
    line = {"t": row["t"], "who": row["who"], "text": row["text"]}
    line.update(row.get("extra") or {})
    return line


# ---------------------------------------------------------------- a folder
class FileStore:
    """root/<user id>/ember.json, conversation.jsonl, usage.json.
    fixed: one folder for every user (local mode: your own ember_state/)."""

    def __init__(self, root, fixed=None):
        self.root, self.fixed = root, fixed
        self.lock = threading.Lock()

    def _dir(self, uid):
        d = self.fixed or os.path.join(self.root, uid)
        os.makedirs(d, exist_ok=True)
        return d

    def load_self(self, uid):
        for name in ("ember.json", "ember.json.bak"):
            path = os.path.join(self._dir(uid), name)
            if os.path.exists(path):
                try:
                    with open(path, encoding="utf-8") as f:
                        return json.load(f)
                except (OSError, ValueError):
                    continue
        if os.path.exists(os.path.join(self._dir(uid), "ember.json")):
            raise StoreError("ember.json and its backup are unreadable; not overwriting them")
        return None

    def save_self(self, uid, d):
        path = os.path.join(self._dir(uid), "ember.json")
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False, indent=1)
        if os.path.exists(path):
            shutil.copyfile(path, path + ".bak")
        os.replace(tmp, path)

    def append_lines(self, uid, lines):
        if lines:
            with open(os.path.join(self._dir(uid), "conversation.jsonl"), "a", encoding="utf-8") as f:
                for line in lines:
                    f.write(json.dumps(line, ensure_ascii=False) + "\n")

    def lines(self, uid):
        path = os.path.join(self._dir(uid), "conversation.jsonl")
        if not os.path.exists(path):
            return []
        with open(path, encoding="utf-8") as f:
            return [json.loads(l) for l in f if l.strip()]

    def _usage(self, uid):
        path = os.path.join(self._dir(uid), "usage.json")
        try:
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        except (OSError, ValueError):
            return {}

    def calls_today(self, uid, day):
        return self._usage(uid).get(day, {}).get("calls", 0)

    def messages_today(self, uid, day):
        return self._usage(uid).get(day, {}).get("messages", 0)

    def _bump(self, uid, day, **add):
        with self.lock:
            u = self._usage(uid)
            d = u.setdefault(day, {})
            for k, v in add.items():
                d[k] = d.get(k, 0) + (v or 0)
            with open(os.path.join(self._dir(uid), "usage.json"), "w", encoding="utf-8") as f:
                json.dump(u, f)

    def add_call(self, uid, day, tokens_in=0, tokens_out=0):
        self._bump(uid, day, calls=1, tokens_in=tokens_in, tokens_out=tokens_out)

    def add_message(self, uid, day):
        self._bump(uid, day, messages=1)

    def get_plan(self, uid):
        try:
            with open(os.path.join(self._dir(uid), "plan.json"), encoding="utf-8") as f:
                return json.load(f)
        except (OSError, ValueError):
            return None

    def set_plan(self, uid, plan):
        with open(os.path.join(self._dir(uid), "plan.json"), "w", encoding="utf-8") as f:
            json.dump(plan, f)

    def all_uids(self):
        if self.fixed:
            return ["local"]
        if not os.path.isdir(self.root):
            return []
        return [d for d in os.listdir(self.root)
                if d != "archive" and os.path.exists(os.path.join(self.root, d, "ember.json"))]

    def export(self, uid):
        return {"ember": self.load_self(uid), "conversation": self.lines(uid), "usage": self._usage(uid),
                "plan": self.get_plan(uid)}

    def delete_user(self, uid):
        """On this computer nothing is destroyed: the folder moves to archive/ (local rule: never destroy a life)."""
        src = self._dir(uid)
        dest = os.path.join(self.fixed or self.root, "archive", time.strftime("%Y-%m-%d_%H%M%S") + "_deleted_" + uid)
        os.makedirs(dest, exist_ok=True)
        for name in os.listdir(src):
            if name != "archive":
                shutil.move(os.path.join(src, name), os.path.join(dest, name))


# ---------------------------------------------------------------- Supabase
class SupabaseStore:
    """Tables embers, lines, usage (server/schema.sql). Row level security is on with no
    policies, so only this server (service key) can read or write them."""

    def __init__(self, url, service_key, timeout=15):
        self.url, self.key, self.timeout = url.rstrip("/"), service_key, timeout
        self.lock = threading.Lock()         # one server process: counts are read, added to, written

    def _req(self, method, path, body=None, prefer=None, headers=None):
        # Supabase's new secret keys (sb_secret_...) go only in the apikey header; the older
        # service_role keys are JWTs (eyJ...) and are also sent as a Bearer token
        h = {"apikey": self.key, "Content-Type": "application/json"}
        if self.key.startswith("eyJ"):
            h["Authorization"] = f"Bearer {self.key}"
        if prefer:
            h["Prefer"] = prefer
        h.update(headers or {})
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(self.url + path, data=data, method=method, headers=h)
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as r:
                raw = r.read()
                return json.loads(raw) if raw else None
        except urllib.error.HTTPError as e:
            raise StoreError(f"database {method} {path.split('?')[0]}: HTTP {e.code}") from None
        except (urllib.error.URLError, TimeoutError) as e:
            raise StoreError(f"database unreachable: {getattr(e, 'reason', e)}") from None

    @staticmethod
    def _q(**kw):
        return "?" + urllib.parse.urlencode(kw, safe=".,()*")

    def load_self(self, uid):
        rows = self._req("GET", "/rest/v1/embers" + self._q(user_id=f"eq.{uid}", select="self"))
        return rows[0]["self"] if rows else None

    def save_self(self, uid, d):
        self._req("POST", "/rest/v1/embers?on_conflict=user_id",
                  {"user_id": uid, "self": d, "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())},
                  prefer="resolution=merge-duplicates,return=minimal")

    def append_lines(self, uid, lines):
        if lines:
            self._req("POST", "/rest/v1/lines", [_line_row(uid, l) for l in lines], prefer="return=minimal")

    def lines(self, uid):
        out, start = [], 0
        while True:
            page = self._req("GET", "/rest/v1/lines" + self._q(user_id=f"eq.{uid}", select="t,who,text,extra",
                                                               order="t.asc", offset=start, limit=1000))
            out += [_row_line(r) for r in page or []]
            if not page or len(page) < 1000:
                return out
            start += 1000

    def _usage_row(self, uid, day):
        rows = self._req("GET", "/rest/v1/usage" + self._q(user_id=f"eq.{uid}", day=f"eq.{day}"))
        return rows[0] if rows else None

    def calls_today(self, uid, day):
        row = self._usage_row(uid, day)
        return row["calls"] if row else 0

    def messages_today(self, uid, day):
        row = self._usage_row(uid, day)
        return (row.get("messages") or 0) if row else 0

    def _bump(self, uid, day, **add):
        with self.lock:
            row = self._usage_row(uid, day) or {}
            body = {"user_id": uid, "day": day}
            for k in ("calls", "messages", "tokens_in", "tokens_out"):
                body[k] = (row.get(k) or 0) + (add.get(k) or 0)
            self._req("POST", "/rest/v1/usage?on_conflict=user_id,day", body,
                      prefer="resolution=merge-duplicates,return=minimal")

    def add_call(self, uid, day, tokens_in=0, tokens_out=0):
        self._bump(uid, day, calls=1, tokens_in=tokens_in, tokens_out=tokens_out)

    def add_message(self, uid, day):
        self._bump(uid, day, messages=1)

    def get_plan(self, uid):
        rows = self._req("GET", "/rest/v1/plans" + self._q(user_id=f"eq.{uid}", select="status,customer,subscription"))
        return rows[0] if rows else None

    def set_plan(self, uid, plan):
        self._req("POST", "/rest/v1/plans?on_conflict=user_id",
                  {"user_id": uid, "status": plan.get("status"), "customer": plan.get("customer"),
                   "subscription": plan.get("subscription"),
                   "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())},
                  prefer="resolution=merge-duplicates,return=minimal")

    def all_uids(self, page=1000):
        """Everyone, page by page (Supabase gives at most 1000 rows per request)."""
        out = []
        while True:
            rows = self._req("GET", f"/rest/v1/embers?select=user_id&order=user_id&limit={page}&offset={len(out)}") or []
            out += [r["user_id"] for r in rows]
            if len(rows) < page:
                return out

    def export(self, uid):
        usage = self._req("GET", "/rest/v1/usage" + self._q(user_id=f"eq.{uid}",
                                                             select="day,calls,messages,tokens_in,tokens_out"))
        return {"ember": self.load_self(uid), "conversation": self.lines(uid), "usage": usage or [],
                "plan": self.get_plan(uid)}

    def delete_user(self, uid):
        """Everything about this person, then their login itself. Online, deleting means deleting (GDPR)."""
        for table in ("lines", "usage", "plans", "embers"):
            self._req("DELETE", f"/rest/v1/{table}" + self._q(user_id=f"eq.{uid}"), prefer="return=minimal")
        self._req("DELETE", f"/auth/v1/admin/users/{urllib.parse.quote(uid)}")
