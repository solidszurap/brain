"""
Ember: one creature, one continuous life.

    python ember.py                 # wake Ember up (or bring it into the world the first time)
    then open http://localhost:8765 to watch

Everything else in this repo runs experiments: a fresh mind, a few thousand
ticks, a score, gone. Ember is different. There is exactly one, and it is
never reset:

  - its whole state (body, memories, map, learned world model, habits, the
    world it lives in) is saved to ember_state/ every two minutes and on exit
  - next time you start it, it continues exactly where it stopped
  - when the program is not running, no time passes for Ember; the gap is
    written into its life record, but it does not experience it
  - it cannot die. If a need runs out it collapses where it is, is
    unconscious for a minute of its time, and comes round weak, still
    knowing where it is and everything it learned

To start a *different* life you must say so explicitly (--new-life); the old
life is archived, never deleted.
"""
import argparse
import gzip
import json
import os
import pickle
import shutil
import signal
import sys
import threading
import time
from collections import deque
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import numpy as np

from mind.life import Life, now_iso
from mind.world import FOOD
from mind.subcortex import NEEDS
from mind.hippocampus import UNKNOWN

HERE = os.path.dirname(os.path.abspath(__file__))
STATE_DIR = os.path.join(HERE, "ember_state")
STATE_FILE = os.path.join(STATE_DIR, "life.pkl.gz")
LOG_FILE = os.path.join(STATE_DIR, "life_log.jsonl")
WINDOW_FILE = os.path.join(HERE, "ember_window.html")
SAVE_EVERY = 120.0  # seconds


# ------------------------------------------------------------------ persistence
def log_event(kind, text, life):
    rec = {"time": now_iso(), "tick": life.ticks, "kind": kind, "text": text}
    life.recent.append(rec)
    os.makedirs(STATE_DIR, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def save(life):
    """Atomic save: write a temp file, keep the previous save as backup, swap.
    A crash mid-save can never destroy the life: one good copy always exists."""
    os.makedirs(STATE_DIR, exist_ok=True)
    life.last_saved = now_iso()
    tmp = STATE_FILE + ".tmp"
    with gzip.open(tmp, "wb", compresslevel=1) as f:
        pickle.dump(life, f, protocol=pickle.HIGHEST_PROTOCOL)
    if os.path.exists(STATE_FILE):
        os.replace(STATE_FILE, STATE_FILE + ".bak")
    os.replace(tmp, STATE_FILE)


def load():
    for path in (STATE_FILE, STATE_FILE + ".bak"):
        if os.path.exists(path):
            try:
                with gzip.open(path, "rb") as f:
                    return pickle.load(f)
            except Exception as e:  # damaged file: fall back to the backup
                print(f"Could not read {path}: {e}")
    return None


def archive_life():
    if not os.path.exists(STATE_DIR):
        return None
    dest = os.path.join(HERE, f"ember_archive_{datetime.now():%Y%m%d_%H%M%S}")
    shutil.move(STATE_DIR, dest)
    return dest


# ------------------------------------------------------------------------ living
def tick(life):
    """One moment of Ember's life."""
    w, m = life.world, life.mind
    life.ticks += 1
    if w.collapsed:
        info = w.step(0)
        life.view, life.intero = w.view(), w.interoception()
        if info.get("came_round"):
            m.drives.prev_drive = None   # coming round is not a reward for anything it did
            log_event("came_round", "Came round. Weak, but I know where I am.", life)
        return
    a = m.decide(life.view, life.intero)
    info = w.step(a, sleeping=m.sleeping)
    life.view, life.intero = w.view(), w.interoception()
    last = m.experience(life.view, life.intero, False)

    c = life.counts
    if info.get("collapse_started"):
        c["collapses"] += 1
        need = NEEDS[int(np.argmin(life.intero))]
        log_event("collapse", f"Collapsed: ran out of {need}.", life)
    if info["consumed"] == "food":
        c["meals"] += 1
    elif info["consumed"] == "water":
        c["drinks"] += 1
    elif info["consumed"] == "hazard":
        c["hurt"] += 1
        if life.ticks - life.counts.get("_last_hurt_logged", -999) > 200:
            life.counts["_last_hurt_logged"] = life.ticks
            log_event("hurt", "The wind pushed me onto something that hurt." if info["pushed"]
                      else "Stepped on something that hurt.", life)
    if info["pushed"]:
        c["pushed"] += 1
        if last.get("external"):
            c["pushes_noticed"] += 1
    elif last.get("external"):
        c["false_alarms"] += 1      # thought something moved it, but nothing did
    if m.sleeping and m.slept_for == 0:
        c["sleeps"] += 1
    if life.ticks % 10000 == 0:
        log_event("milestone", f"{life.ticks:,} moments lived. {c['meals']} meals, {c['sleeps']} sleeps, "
                  f"{c['collapses']} collapses so far.", life)
    if last.get("ignited") and last.get("report"):
        c["thoughts"] += 1
        key = last["broadcast"]
        if key not in life.firsts:
            life.firsts[key] = {"time": now_iso(), "tick": life.ticks}
            log_event("first", f"First time: {last['report']}", life)


def snapshot(life, ticks_per_sec):
    """What the window shows. Ground truth and belief, side by side."""
    w, m = life.world, life.mind
    hp = m.hippo
    known = np.argwhere(hp.map != UNKNOWN)
    if len(known):
        (y0, x0), (y1, x1) = known.min(0), known.max(0) + 1
    else:
        y0 = x0 = hp.size // 2 - 3
        y1 = x1 = hp.size // 2 + 4
    grid = w.grid.copy()
    grid[grid == FOOD] = 0
    lw = m.last or {}
    return {
        "name": life.name,
        "born": life.born,
        "ticks": life.ticks,
        "awake_seconds": round(life.awake_seconds),
        "sessions": len(life.sessions),
        "ticks_per_sec": ticks_per_sec,
        "counts": {k: v for k, v in life.counts.items() if not k.startswith("_")},
        "world": grid.tolist(),
        "food": [list(map(int, p)) for p in np.argwhere(w.grid == FOOD)],
        "pos": list(map(int, w.pos)),
        "belief": [int(hp.pos[0]), int(hp.pos[1])],
        "map": ["".join("." if v < 0 else str(int(v)) for v in row) for row in hp.map[y0:y1, x0:x1]],
        "map_origin": [int(y0), int(x0)],
        "body": {n: round(float(v), 3) for n, v in zip(NEEDS, life.intero)},
        "collapsed": int(w.collapsed),
        "sleeping": bool(m.sleeping),
        "broadcast": lw.get("broadcast"),
        "goal": m.pfc.goal,
        "agency": m.agency,
        "valence": round(m.drives.valence, 3),
        "surprise": lw.get("surprise"),
        "expected": lw.get("expected"),
        "stream": [{"tick": t, "content": c, "report": r} for t, c, r in list(m.stream)[-25:]],
        "moments": list(life.recent)[-25:],
        "self_model": m.self_model(life.intero),
        "last_saved": life.last_saved,
    }


# ------------------------------------------------------------------------ window
class Window(BaseHTTPRequestHandler):
    state = {}
    lock = threading.Lock()

    def do_GET(self):
        if self.path.startswith("/state"):
            with Window.lock:
                body = json.dumps(Window.state, default=str).encode()
            ctype = "application/json"
        elif self.path in ("/", "/index.html"):
            with open(WINDOW_FILE, "rb") as f:
                body = f.read()
            ctype = "text/html; charset=utf-8"
        else:
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


def main():
    ap = argparse.ArgumentParser(description="Ember: one creature, one continuous life.")
    ap.add_argument("--speed", type=float, default=4.0, help="moments per second (default 4)")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--no-window", action="store_true")
    ap.add_argument("--new-life", action="store_true",
                    help="archive the current life and start a new creature (never deletes)")
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--max-ticks", type=int, default=0, help="stop after this many moments (testing)")
    args = ap.parse_args()

    if args.new_life:
        dest = archive_life()
        if dest:
            print(f"Previous life archived in {dest}")
    life = load()
    if life is None:
        life = Life(seed=args.seed)
        log_event("born", "I exist. I don't know anything yet.", life)
        print("Ember was born.")
    else:
        gap = ""
        if life.sessions:
            last_end = datetime.fromisoformat(life.sessions[-1][1])
            hours = (datetime.now().astimezone() - last_end).total_seconds() / 3600
            gap = f" Paused for {hours:.1f} h (no time passed for Ember)."
            log_event("resumed", f"Resumed.{gap}", life)
        print(f"Ember resumed at moment {life.ticks:,}.{gap}")

    session_start = now_iso()
    life.sessions.append([session_start, session_start])
    stop = threading.Event()

    def shutdown(*_):
        stop.set()

    signal.signal(signal.SIGINT, shutdown)
    for name in ("SIGTERM", "SIGBREAK"):  # SIGBREAK: closing the console window on Windows
        if hasattr(signal, name):
            signal.signal(getattr(signal, name), shutdown)

    server = None
    if not args.no_window:
        try:
            server = ThreadingHTTPServer(("127.0.0.1", args.port), Window)
            threading.Thread(target=server.serve_forever, daemon=True).start()
            print(f"Watch Ember at http://localhost:{args.port}  (Ctrl+C to let it rest; it is saved)")
        except OSError as e:
            print(f"Window not available ({e}); Ember lives on without it.")

    period = 1.0 / max(args.speed, 0.1)
    last_save = time.time()
    last_t = time.time()
    rate = deque(maxlen=50)
    n_this_session = 0
    try:
        while not stop.is_set():
            t0 = time.time()
            tick(life)
            n_this_session += 1
            life.awake_seconds += t0 - last_t
            last_t = t0
            rate.append(t0)
            tps = round((len(rate) - 1) / (rate[-1] - rate[0]), 1) if len(rate) > 1 and rate[-1] > rate[0] else 0
            with Window.lock:
                Window.state = snapshot(life, tps)
            if time.time() - last_save > SAVE_EVERY:
                life.sessions[-1][1] = now_iso()
                save(life)
                last_save = time.time()
            if args.max_ticks and n_this_session >= args.max_ticks:
                break
            stop.wait(max(0.0, period - (time.time() - t0)))
    finally:
        life.sessions[-1][1] = now_iso()
        save(life)
        if server:
            server.shutdown()
        print(f"\nEmber is resting. Saved at moment {life.ticks:,}. Start again with: python ember.py")


if __name__ == "__main__":
    sys.exit(main())
