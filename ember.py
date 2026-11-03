"""
Ember: a small being with a face that lives on this computer. It gets to know
you, and (in later slices) helps you find what to work towards and works
alongside you on it.

    python ember.py              then open http://localhost:8765 (start_ember.bat does both)
    python ember.py --port 8800 --state scratch_dir   (a separate Ember, for trying things out)

Its mind is an LLM (set in .env, see mind/llm.py; without one it uses a simple
template mind). Everything it is lives in ember_state/: ember.json (its self
and what it remembers about you) and conversation.jsonl (every line said).
Nothing leaves this computer except what is sent to the LLM when it thinks.

The Ember that lived in a grid world (until 2026-11) is in old/; its life is
archived in ember_state/archive/, never deleted.
"""
import argparse
import json
import os
import queue
import shutil
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from mind import llm
from mind.core import Ember, dumps

HERE = os.path.dirname(os.path.abspath(__file__))
STATE_DIR = os.path.join(HERE, "ember_state")
SELF_FILE = os.path.join(STATE_DIR, "ember.json")
TALK_FILE = os.path.join(STATE_DIR, "conversation.jsonl")
WINDOW_FILE = os.path.join(HERE, "ember_window.html")
PRESENT_FOR = 3.0      # you're here if the visible window polled within this many seconds
MAX_TEXT = 2000


# ------------------------------------------------------------------ saving
def archive_old_life(state_dir=STATE_DIR, now=None):
    """The grid-world Ember's files move to ember_state/archive/<date>_grid_ember/. Never deleted."""
    if not os.path.isdir(state_dir):
        return None
    keep = {"ember.json", "ember.json.bak", "conversation.jsonl", "archive"}
    old = [f for f in os.listdir(state_dir) if f not in keep]
    if not old:
        return None
    stamp = time.strftime("%Y-%m-%d", time.localtime(now or time.time()))
    dest = os.path.join(state_dir, "archive", f"{stamp}_grid_ember")
    os.makedirs(dest, exist_ok=True)
    for f in old:
        shutil.move(os.path.join(state_dir, f), os.path.join(dest, f))
    return dest


def load():
    for path in (SELF_FILE, SELF_FILE + ".bak"):
        if os.path.exists(path):
            try:
                with open(path, encoding="utf-8") as f:
                    return Ember.from_dict(json.load(f))
            except (OSError, ValueError) as e:
                print(f"  couldn't read {os.path.basename(path)}: {e}")
    if os.path.exists(SELF_FILE):
        sys.exit("ember.json and its backup are unreadable; not starting, so nothing gets overwritten.")
    return None


def save(ember):
    os.makedirs(STATE_DIR, exist_ok=True)
    if ember.outbox:
        with open(TALK_FILE, "a", encoding="utf-8") as f:
            for line in ember.outbox:
                f.write(json.dumps(line, ensure_ascii=False) + "\n")
        ember.outbox = []
    tmp = SELF_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(dumps(ember))
    if os.path.exists(SELF_FILE):
        shutil.copyfile(SELF_FILE, SELF_FILE + ".bak")
    os.replace(tmp, SELF_FILE)


# ------------------------------------------------------------------- the mind
class Mind:
    """One thought at a time, in its own thread, so the window never waits on the LLM."""
    events = queue.Queue()
    thinking = False
    cfg = None
    problem = None      # the last error from the LLM, shown in the window

    @classmethod
    def work(cls, ember, lock):
        while True:
            event = cls.events.get()
            cls.thinking = True
            try:
                with lock:
                    system, user = ember.prompt(event, time.time())
                raw = None
                if cls.cfg.usable:
                    try:
                        raw = llm.call_llm(cls.cfg, system, user, json_mode=True)
                        cls.problem = None
                    except llm.LLMError as e:
                        cls.problem = str(e)[:200]
                        print(f"  mind: {cls.problem} (the template mind answered)")
                with lock:
                    r = ember.respond(event, raw, time.time())
                    save(ember)
                if r["dropped"]:
                    print(f"  not remembered (no source in your words, or already known): {len(r['dropped'])}")
            except Exception as e:      # keep the thread alive whatever happens
                print(f"  mind error: {e!r}")
            finally:
                cls.thinking = False


# ------------------------------------------------------------------- window
class Window(BaseHTTPRequestHandler):
    ember = None
    lock = threading.Lock()
    seen_at = 0.0

    @classmethod
    def present(cls, now):
        return now - cls.seen_at < PRESENT_FOR

    def _send(self, body, ctype="application/json"):
        if isinstance(body, (dict, list)):
            body = json.dumps(body, ensure_ascii=False, default=str).encode()
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        now = time.time()
        e = Window.ember
        if self.path.startswith("/state"):
            if "v=1" in self.path:                    # /state?v=1: the window is open and visible
                Window.seen_at = now
            with Window.lock:
                s = e.snapshot(now, Window.present(now), Mind.thinking or not Mind.events.empty())
            s["mind"] = Mind.cfg.describe()
            s["problem"] = Mind.cfg.problem or Mind.problem
            self._send(s)
        elif self.path.startswith("/memory"):
            with Window.lock:
                self._send(e.memory_page())
        elif self.path in ("/", "/index.html"):
            with open(WINDOW_FILE, "rb") as f:
                self._send(f.read(), "text/html; charset=utf-8")
        else:
            self.send_error(404)

    def do_POST(self):
        # only the window may talk to Ember: same-origin and a custom header, so other
        # web pages open in the browser can't (the header forces a CORS preflight this
        # server never answers)
        origin = self.headers.get("Origin")
        port = self.server.server_address[1]
        if self.path not in ("/talk", "/poke", "/memory/edit", "/memory/forget") or \
                self.headers.get("X-Ember") != "1" or \
                (origin and origin not in (f"http://localhost:{port}", f"http://127.0.0.1:{port}")):
            self.send_error(403)
            return
        try:
            n = min(int(self.headers.get("Content-Length", 0)), 16384)
            data = json.loads(self.rfile.read(n) or b"{}")
            if not isinstance(data, dict):
                raise ValueError
        except ValueError:
            self.send_error(400)
            return
        now = time.time()
        e = Window.ember
        with Window.lock:
            if self.path == "/talk":
                text = str(data.get("text", "")).strip()[:MAX_TEXT]
                if not text:
                    self.send_error(400)
                    return
                e.hear(now, text)
                Mind.events.put({"type": "talk", "text": text})
                ok = True
            elif self.path == "/poke":
                e.poke(now)
                ok = True
            elif self.path == "/memory/edit":
                ok = e.edit_memory(data.get("id"), data.get("note", ""), now)
            else:
                ok = e.forget(data.get("id"))
            save(e)
        self._send({"ok": bool(ok)})

    def log_message(self, *args):
        pass


# ---------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--state", default=None, help="a different folder for its self (for trying things out)")
    args = ap.parse_args()
    if args.state:
        global STATE_DIR, SELF_FILE, TALK_FILE
        STATE_DIR = os.path.abspath(args.state)
        SELF_FILE = os.path.join(STATE_DIR, "ember.json")
        TALK_FILE = os.path.join(STATE_DIR, "conversation.jsonl")

    llm.load_dotenv(os.path.join(HERE, ".env"))
    Mind.cfg = llm.LLMConfig()
    moved = archive_old_life(STATE_DIR)
    if moved:
        print(f"The grid-world Ember's life was archived (not deleted) in {os.path.relpath(moved, HERE)}")
    ember = load()
    if ember is None:
        ember = Ember()
        save(ember)
        print("A new Ember. It hasn't met you yet.")
    else:
        print(f"Ember is here. It remembers {len(ember.memories)} things about you.")
    print(f"Its mind: {Mind.cfg.describe()}" + (f"  (problem: {Mind.cfg.problem})" if Mind.cfg.problem else ""))
    Window.ember = ember
    threading.Thread(target=Mind.work, args=(ember, Window.lock), daemon=True).start()
    server = ThreadingHTTPServer(("127.0.0.1", args.port), Window)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    print(f"Its window: http://localhost:{args.port}   (Ctrl+C to close)")

    was_present, last_save = False, time.time()
    try:
        while True:
            now = time.time()
            present = Window.present(now)
            with Window.lock:
                if present and not was_present and ember.arrive(now):
                    Mind.events.put({"type": "arrive"})
                ember.update(now, present)
                if now - last_save > 60:
                    save(ember)
                    last_save = now
            was_present = present
            time.sleep(0.25)
    except KeyboardInterrupt:
        pass
    finally:
        with Window.lock:
            save(ember)
        server.shutdown()
        print("Saved. Ember will know how long you were gone.")


if __name__ == "__main__":
    main()
