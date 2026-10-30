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
  - time passes while you're away, slowly: about a season (3,000 moments)
    per real day, at most a year per absence. Nothing is skipped: when you
    come back (or start it again), it lives those moments one by one, fast,
    and the absence is written into its life record
  - it cannot die. If a need runs out it collapses where it is, is
    unconscious for a minute of its time, and comes round weak, still
    knowing where it is and everything it learned
  - since version 2 it lives in the wide world (mind/wideworld.py). A life
    from before is moved there on its first start, keeping every memory
    (a copy of the old life is kept as ember_state/before_the_valley_opened.pkl.gz)
  - an observer tracks, with tests written down in advance, whether it is
    getting closer to self-awareness and to the indicators of consciousness
    (mind/consciousness.py); milestones go into its life record and a report
    is kept in ember_state/consciousness_report.md

To start a *different* life you must say so explicitly (--new-life); the old
life is archived, never deleted.
"""
import argparse
import gzip
import itertools
import json
import os
import pickle
import queue
import shutil
import signal
import sys
import threading
import time
from collections import deque
from datetime import datetime, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import numpy as np

from mind.life import Life, now_iso, open_the_valley, step_life
from mind.subcortex import NEEDS
from mind.hippocampus import UNKNOWN
from mind.selfknowledge import AttentionSchema, _kind
from mind.consciousness import Observer
from mind.wideworld import region_of
from mind.witness import Witness
from mind import voice as voice_mod

HERE = os.path.dirname(os.path.abspath(__file__))
STATE_DIR = os.path.join(HERE, "ember_state")
STATE_FILE = os.path.join(STATE_DIR, "life.pkl.gz")
LOG_FILE = os.path.join(STATE_DIR, "life_log.jsonl")
REPORT_FILE = os.path.join(STATE_DIR, "consciousness_report.md")
TALK_FILE = os.path.join(STATE_DIR, "conversations.jsonl")
WINDOW_FILE = os.path.join(HERE, "ember_window.html")
SAVE_EVERY = 120.0  # seconds
AWAY_RATE = 3000 / 86400   # moments lived per real second you're away: about a season a day
AWAY_CAP = 12000           # at most a year for one absence
PRESENT_FOR = 3.0          # seconds after the window's last poll while it was visible
AWAY_LOG_MIN = 600.0       # absences shorter than this (seconds) aren't written into its life record


# Every change to how Ember's mind works, written into its life record the
# first time it wakes with the change, so its history says when it happened.
# Add new ones at the end; never edit or remove old ones.
MIND_CHANGES = [
    ("2026-10-30 copy test", "The copy tests changed: they now start at a hard moment and use 3 pairs "
                             "of copies (the scientist's tools, not its mind)."),
    ("2026-10-30 gate seen", "Its mind changed: seeing the orchard gate shut now corrects a belief that "
                             "it is open. Before, only the gate's sound did, and it can't hear while "
                             "unconscious."),
    ("2026-10-30 autobiography", "Its mind changed: it now keeps an autobiographical memory of what reaches "
                                 "its workspace and of what it finds out, by season. Of its life before, it "
                                 "keeps only what it had found out and its last few hundred moments, vaguely."),
    ("2026-10-30 voice", "It can be spoken to. A voice reaches its workspace like a sound and can wake it; "
                         "what was said becomes a memory. Its language cortex answers only from its own mind."),
    ("2026-10-30 voice checker", "The check on what it says changed (the scientist's tools, not its mind): saying "
                                 "it doesn't remember something no longer counts as a claim, and the judge finds the "
                                 "memory behind what it said without citing. Its language cortex also gets a fixed "
                                 "note to cite: it can't tell whether there is anything it feels like to be it."),
    ("2026-10-30 winter food", "Its mind changed: a place where food grew this season before now counts as a "
                               "let-down when it sees the place empty, not only when it stands on it, and seeing "
                               "food there again clears it. Before, places that had only autumn's leftovers in "
                               "winter were never crossed off, and the food it imagined there kept it from "
                               "opening the gate (the winter loops)."),
    ("2026-10-30 time while away", "Time now passes while you're away: about a season (3,000 moments) per real "
                                   "day, at most a year per absence, lived moment by moment when you come back. "
                                   "Before, no time passed while it was stopped."),
    ("2026-10-30 the light", "Its world has a new kind of thing: a light, which is you, appearing where you click; "
                             "food you leave lies inside it. Its eyes grew to tell apart 10 kinds of things "
                             "(everything it knew is kept), and it can now learn that it often finds food in "
                             "something, the way it learned that the lever opens the gate."),
]


def record_mind_changes(life):
    done = getattr(life, "mind_changes", None)
    if done is None:
        done = life.mind_changes = []
    for cid, text in MIND_CHANGES:
        if cid not in done:
            log_event("mind_changed", text, life)
            done.append(cid)


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
def ensure_observer(life):
    """The attention schema (part of its mind) and the observer (the scientist
    outside), added also to lives born before they existed."""
    if not hasattr(life.mind, "schema"):
        life.mind.schema = AttentionSchema()
    if not hasattr(life, "observer"):
        w, hp = life.world, life.mind.hippo
        anchor = (w.pos[0] - hp.pos[0], w.pos[1] - hp.pos[1])
        early = []
        if hasattr(life, "tracker"):
            anchor, early = life.tracker.anchor, life.tracker.history
        life.observer = Observer(anchor, early)
        life.observer.cum["collapses_seen"] = getattr(w, "collapses", 0)
    return life.observer


def ensure_witness(life):
    """The scientist's record of what was really true when each memory formed."""
    if not hasattr(life, "witness"):
        life.witness = Witness(ensure_observer(life).anchor)
    return life.witness


# ------------------------------------------------------------------------ talking
VOICE_PATIENCE = 20       # moments a voice keeps calling before Ember answers anyway, distracted


class Talk:
    """Questions from the window, on their way into Ember's mind and back.
    Lives outside the saved life (threads and queues can't be saved)."""
    cfg = voice_mod.VoiceConfig({})
    lock = threading.Lock()
    pending = deque()
    current = None
    jobs = queue.Queue()
    done = queue.Queue()
    records = {}
    ids = itertools.count(1)

    @classmethod
    def ask(cls, text):
        rid = f"q{int(time.time())}-{next(cls.ids)}"
        rec = {"id": rid, "question": text, "asked": now_iso(), "status": "queued"}
        with cls.lock:
            cls.records[rid] = rec
            cls.pending.append(rec)
        return rid

    @classmethod
    def status(cls, rid):
        with cls.lock:
            r = cls.records.get(rid)
            return dict(r) if r else None


def voice_worker():
    """Off the main loop: the LLM can take seconds; Ember keeps living meanwhile."""
    while True:
        rid, dossier, truths = Talk.jobs.get()
        try:
            out = voice_mod.answer_question(Talk.cfg, dossier, truths)
        except Exception as e:      # the voice is a peripheral; never let it hurt Ember
            out = {"say": "", "claims": [], "summary": {}, "error": f"voice failed: {e}"}
        Talk.done.put((rid, out, dossier))


def _set(rec, **kw):
    with Talk.lock:
        rec.update(kw)


def listen(life, info, conscious):
    """A voice reaching Ember: each moment while someone is speaking, the
    voice competes for its workspace like a sound (mind/ember_mind.py).
    Once it gets in (or after VOICE_PATIENCE moments) Ember answers."""
    m = life.mind
    while True:                                   # answers that came back
        try:
            rid, out, dossier = Talk.done.get_nowait()
        except queue.Empty:
            break
        rec = Talk.records.get(rid)
        if rec is None:
            continue
        if out.get("say"):
            m.autobiography().record(m.t, "said", f'I said: "{out["say"][:240]}"', m._place(), None,
                                     importance=0.7, key="said")
        _set(rec, status="done", **{k: out.get(k) for k in ("say", "claims", "summary", "voice", "error", "seconds")})
        keep = {k: v for k, v in rec.items()}
        convs = getattr(life, "conversations", None)
        if convs is None:
            convs = life.conversations = []
        convs.append(keep)
        del convs[:-300]
        try:
            with open(TALK_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps({**keep, "mind": voice_mod.render(dossier)}, ensure_ascii=False, default=str) + "\n")
        except OSError:
            pass
    rec = Talk.current
    if rec is None:
        with Talk.lock:
            rec = Talk.current = Talk.pending.popleft() if Talk.pending else None
        if rec is None:
            return
        rec["waited"] = 0
    if not conscious:
        _set(rec, status="unconscious")
        m.hearing_voice = None
        return
    ab = m.autobiography()
    if m.sleeping:
        m.sleeping = False                        # a voice wakes it, like pain does
        ab.record(m.t, "voice", "A voice woke me up.", m._place(), None, importance=0.5, key="voice:woke")
    if not getattr(m, "hearing_voice", None):
        m.hearing_voice = rec["question"]
        _set(rec, status="listening")
        return
    rec["waited"] += 1
    noticed = str((m.last or {}).get("broadcast") or "").startswith("voice:")
    if not noticed and rec["waited"] < VOICE_PATIENCE:
        return
    m.hearing_voice = None
    q = rec["question"]
    if noticed:
        ab.record(m.t, "voice", f'Someone spoke to me: "{q[:240]}"', m._place(), None, importance=0.7, key="voice")
    else:
        ab.record(m.t, "voice", f'Someone said something while I was busy; I only half heard it: "{q[:240]}"',
                  m._place(), None, importance=0.4, key="voice")
    wit = ensure_witness(life)
    wit.after_moment(life, {})
    now_on = str(m.gw.current) if m.gw.current else None
    cur = now_on if now_on and not now_on.startswith("voice:") else None
    dossier = voice_mod.build_dossier(m, q, wit.place_name, heard=noticed, attention_now=now_on)
    truths = {it["id"]: wit.item_truth(life, it) for it in dossier["items"]}
    _set(rec, status="thinking", heard=noticed, tick=life.ticks,
         attention=voice_mod.attention_words(cur) if cur else None)
    Talk.jobs.put((rec["id"], dossier, truths))
    Talk.current = None


# ------------------------------------------------------------------------- you
class You:
    """What you do in its world from the window, done between two moments."""
    actions = queue.Queue()


def act_for_you(life):
    w = life.world
    changed = False
    while True:
        try:
            what, arg = You.actions.get_nowait()
        except queue.Empty:
            break
        if what == "light":
            w.place_light(arg)
            changed = True
        elif what == "give" and w.give():
            changed = True
            life.counts["gifts"] += 1
            log_event("gift", "You left food in the light.", life)
    if changed:
        life.view = w.view()                    # it sees the change before it decides what to do


def tick(life):
    """One moment of Ember's life."""
    m = life.mind
    obs = ensure_observer(life)
    wit = ensure_witness(life)
    act_for_you(life)
    life.ticks += 1
    n_learned = len(getattr(m, "learned", []))
    n_done = sum(1 for x in getattr(m, "multi_step", []) if x[2] is not None)
    info, last = step_life(life)
    wit.after_moment(life, info)
    listen(life, info, conscious=last is not None)
    c = life.counts
    if last is None:                       # unconscious this moment
        if info.get("came_round"):
            log_event("came_round", "Came round, weak. Still knows where it is.", life)
        return

    if info.get("collapse_started"):
        c["collapses"] += 1
        need = NEEDS[int(np.argmin(life.intero))]
        log_event("collapse", f"Collapsed: ran out of {need}.", life)
    consumed = info.get("consumed")
    if consumed == "food":
        c["meals"] += 1
        if info.get("gift"):
            c["gifts_eaten"] += 1
            log_event("gift_eaten", "Ate the food you left in the light.", life)
    elif consumed == "water":
        c["drinks"] += 1
    elif consumed == "dark berry":
        c["dark_berries"] += 1
        log_event("sick", "Ate a dark berry and got sick.", life)
    elif consumed == "lever":
        c["levers"] += 1
    elif consumed == "hazard":
        c["hurt"] += 1
        if life.ticks - life.counts.get("_last_hurt_logged", -999) > 200:
            life.counts["_last_hurt_logged"] = life.ticks
            log_event("hurt", "Pushed by the wind onto a hazard." if info["pushed"]
                      else "Stepped onto a hazard.", life)
    if info["pushed"]:
        c["pushed"] += 1
        if last.get("external"):
            c["pushes_noticed"] += 1
    elif last.get("external"):
        c["false_alarms"] += 1      # thought something moved it, but nothing did
    if m.sleeping and m.slept_for == 0:
        c["sleeps"] += 1
    season = info.get("season")
    if season and season != getattr(life, "last_season", season):
        log_event("season", f"{season.capitalize()} began.", life)
    life.last_season = season
    if life.ticks % 10000 == 0:
        log_event("count", f"{life.ticks:,} moments lived. {c['meals']} meals, {c['sleeps']} sleeps, "
                  f"{c['collapses']} collapses so far.", life)
    schema_score = None
    if last.get("ignited") and last.get("broadcast"):
        c["thoughts"] += 1
        schema_score = m.schema.on_ignition(_kind(last["broadcast"]), life.intero)
        key = last["broadcast"]
        if key not in life.firsts:
            life.firsts[key] = {"time": now_iso(), "tick": life.ticks}
            log_event("first", f"First time in its workspace: {key}", life)
    for _, text in getattr(m, "learned", [])[n_learned:]:
        log_event("learned", text[0].upper() + text[1:] + ".", life)
    if sum(1 for x in getattr(m, "multi_step", []) if x[2] is not None) > n_done:
        c["two_step"] += 1
        log_event("learned", "Carried out a two-step plan: opened the gate itself, then reached the food.", life)

    obs.observe(life, info, last, schema_score)
    if obs.window_full:
        _, events = obs.close_window(life, now_iso())
        for e in events:
            log_event("milestone" if e["reached"] else "milestone_lost", e["text"], life)
        try:
            os.makedirs(STATE_DIR, exist_ok=True)
            with open(REPORT_FILE, "w", encoding="utf-8") as f:
                f.write(obs.report_md(life, now_iso()))
        except OSError:
            pass
    sit = obs.clone_test_ready(life, info) if hasattr(life, "valley_opened") else None
    if sit:
        res = obs.run_clone_test(life, now_iso(), sit)
        a, b = res["with_workspace"], res["without_workspace"]
        log_event("copy_test", f"Copy test at a hard moment ({sit}), {len(res['pairs'])} pairs: with its "
                  f"workspace, need-error {a['need_error']}, {a['collapses']:g} collapses on average; without, "
                  f"{b['need_error']}, {b['collapses']:g}. The workspace "
                  f"{'helped' if res['workspace_helps'] else 'did not help'}.", life)


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
    lw = m.last or {}
    obs = getattr(life, "observer", None)
    figures = []
    for kind in ("reflection", "wanderer"):
        f = getattr(w, kind, None)
        if f is not None:
            figures.append({"kind": kind, "pos": [int(f[0]), int(f[1])]})
    return {
        "name": life.name,
        "born": life.born,
        "ticks": life.ticks,
        "awake_seconds": round(life.awake_seconds),
        "sessions": len(life.sessions),
        "ticks_per_sec": ticks_per_sec,
        "counts": {k: v for k, v in life.counts.items() if not k.startswith("_")},
        "world": w.grid.tolist(),
        "figures": figures,
        "season": getattr(w, "season", None),
        "gate_open": bool(getattr(w, "gate_open", False)),
        "region": region_of(w.pos) if hasattr(w, "season") else "valley",
        "pos": list(map(int, w.pos)),
        "belief": [int(hp.pos[0]), int(hp.pos[1])],
        "confidence": round(float(getattr(hp, "confidence", 1.0)), 3),
        "uncertainty": round(float(getattr(hp, "uncertainty", 0.0)), 2),
        "map": ["".join("." if v < 0 else str(int(v)) for v in row) for row in hp.map[y0:y1, x0:x1]],
        "map_origin": [int(y0), int(x0)],
        "body": {n: round(float(v), 3) for n, v in zip(NEEDS, life.intero)},
        "collapsed": int(getattr(w, "collapsed", 0)),
        "sleeping": bool(m.sleeping),
        "broadcast": lw.get("broadcast"),
        "goal": m.pfc.goal,
        "agency": m.agency,
        "valence": round(float(m.drives.valence), 3),
        "surprise": lw.get("surprise"),
        "expected": lw.get("expected"),
        "stream": [{"tick": t, "content": c, "report": r} for t, c, r in list(m.stream)[-25:]],
        "moments": list(life.recent)[-30:],
        "learned": [{"tick": t, "text": x} for t, x in getattr(m, "learned", [])][-20:],
        "self_model": m.self_model(life.intero),
        "tracker": obs.summary() if obs else None,
        "last_saved": life.last_saved,
        "voice": {"name": Talk.cfg.describe(), "problem": Talk.cfg.problem,
                  "listening": bool(getattr(m, "hearing_voice", None))},
        "catching_up": Window.catching_up,
        "light": [int(v) for v in w.light] if getattr(w, "light", None) is not None else None,
        "gift_ready": bool(w.gift_ready()) if hasattr(w, "gift_ready") else False,
    }


def publish(life, tps):
    """Hand the window a fresh picture of Ember."""
    with Window.lock:
        Window.state = snapshot(life, tps)
        Window.state["speed"] = Window.speed
        Window.talk = list(getattr(life, "conversations", []))[-40:]


# --------------------------------------------------------------- time away
def away_text(seconds, lived, capped):
    days, hours = seconds / 86400, seconds / 3600
    span = f"{days:.1f} days" if days >= 1 else f"{hours:.1f} hours" if hours >= 1 else f"{seconds / 60:.0f} minutes"
    text = f"You were away {span}; it lived {lived:,} moments of that (about a season a day)."
    if capped:
        text += " That is the most it lives for one absence (a year); the rest passed without it."
    return text


def catch_up(life, stop):
    """You were away: Ember lives that time now, moment by moment, as fast as
    it can (about a season per real day, at most a year). Nothing is skipped
    or made up; it is only lived quickly. Returns the moments lived."""
    secs = max(0.0, (datetime.now().astimezone() - datetime.fromisoformat(life.away_since)).total_seconds())
    owed = secs * AWAY_RATE
    n = min(AWAY_CAP, int(round(owed)))
    done, shown, t0 = 0, 0.0, time.time()
    while done < n and not stop.is_set():
        tick(life)
        done += 1
        if time.time() - shown > 0.15:
            Window.catching_up = {"done": done, "of": n, "away_seconds": round(secs)}
            publish(life, round(done / max(time.time() - t0, 1e-6), 1))
            shown = time.time()
    Window.catching_up = None
    if n:
        publish(life, 0)                       # the window drops its "catching up" banner at once
    if done < n:
        # stopped part-way: the rest stays owed for next time
        rest = timedelta(seconds=(n - done) / AWAY_RATE)
        life.away_since = (datetime.now().astimezone() - rest).isoformat(timespec="seconds")
        return done
    life.away_since = None
    if secs >= AWAY_LOG_MIN:
        text = away_text(secs, done, owed > AWAY_CAP)
        log_event("away", text, life)
        print(text)
    return done


# ------------------------------------------------------------------------ window
SPEEDS = [4, 20, 100, 0]  # moments per second; 0 = as fast as the computer can


class Window(BaseHTTPRequestHandler):
    state = {}
    talk = []
    lock = threading.Lock()
    speed = 20.0
    seen_at = 0.0        # last poll from the window while it was visible: you are here
    catching_up = None   # while it lives the time you were away: {"done", "of", "away_seconds"}

    def do_GET(self):
        if self.path.startswith("/speed"):
            # /speed?set=20  (0 = as fast as possible)
            try:
                Window.speed = max(0.0, float(self.path.split("set=")[1]))
            except (IndexError, ValueError):
                pass
            body = json.dumps({"speed": Window.speed}).encode()
            ctype = "application/json"
        elif self.path.startswith("/state"):
            if "v=1" in self.path:                 # /state?v=1: the window is open and visible
                Window.seen_at = time.time()
            with Window.lock:
                body = json.dumps(Window.state, default=str).encode()
            ctype = "application/json"
        elif self.path.startswith("/answer"):
            rid = self.path.split("id=")[-1] if "id=" in self.path else ""
            body = json.dumps(Talk.status(rid) or {"error": "unknown question"}, default=str).encode()
            ctype = "application/json"
        elif self.path.startswith("/talk"):
            with Window.lock:
                hist = list(Window.talk)
            with Talk.lock:
                waiting = [dict(r) for r in Talk.records.values() if r.get("status") != "done"]
            body = json.dumps({"voice": Talk.cfg.describe(), "problem": Talk.cfg.problem, "history": hist,
                               "waiting": waiting}, default=str).encode()
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

    def do_POST(self):
        # only the window may talk to Ember or act in its world: same-origin and
        # a custom header, so other web pages open in the browser can't (the
        # header forces a CORS preflight this server never answers)
        origin = self.headers.get("Origin")
        port = self.server.server_address[1]
        if self.path not in ("/ask", "/light", "/give") or self.headers.get("X-Ember") != "1" or (
                origin and origin not in (f"http://localhost:{port}", f"http://127.0.0.1:{port}")):
            self.send_error(403)
            return
        try:
            n = min(int(self.headers.get("Content-Length", 0)), 8192)
            data = json.loads(self.rfile.read(n) or b"{}")
            if not isinstance(data, dict):
                raise ValueError
        except ValueError:
            self.send_error(400)
            return
        if self.path == "/light":
            try:
                You.actions.put(("light", (int(data["y"]), int(data["x"]))))
            except (KeyError, TypeError, ValueError):
                self.send_error(400)
                return
            body = b"{}"
        elif self.path == "/give":
            You.actions.put(("give", None))
            body = b"{}"
        else:
            text = str(data.get("text", "")).strip()[:voice_mod.MAX_QUESTION]
            if not text:
                self.send_error(400)
                return
            body = json.dumps({"id": Talk.ask(text)}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


def main():
    ap = argparse.ArgumentParser(description="Ember: one creature, one continuous life.")
    ap.add_argument("--speed", type=float, default=None,
                    help="moments per second; 0 = as fast as possible (default: last used, else 20). "
                         "You can also change it live in the window.")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--no-window", action="store_true")
    ap.add_argument("--new-life", action="store_true",
                    help="archive the current life and start a new creature (never deletes)")
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--max-ticks", type=int, default=0, help="stop after this many moments (testing)")
    args = ap.parse_args()

    voice_mod.load_dotenv(os.path.join(HERE, ".env"))
    Talk.cfg = voice_mod.VoiceConfig()
    threading.Thread(target=voice_worker, daemon=True).start()
    print(f"Ember's voice: {Talk.cfg.describe()}" + (f"  (problem: {Talk.cfg.problem})" if Talk.cfg.problem else ""))

    if args.new_life:
        dest = archive_life()
        if dest:
            print(f"Previous life archived in {dest}")
    life = load()
    if life is None:
        life = Life(seed=args.seed)
        log_event("born", "Born. Knows nothing yet.", life)
        print("Ember was born.")
    else:
        if getattr(life, "version", 1) < 2:
            # first start since the wide world exists: keep a copy of the life as
            # it was, then open the valley (every memory is kept)
            shutil.copy2(STATE_FILE, os.path.join(STATE_DIR, "before_the_valley_opened.pkl.gz"))
            msg = open_the_valley(life)
            ensure_observer(life)
            log_event("valley_opened", msg, life)
            save(life)
            print(msg)
        if life.sessions:
            if getattr(life, "away_since", None) is None:   # saved before time passed while away
                life.away_since = life.sessions[-1][1]
            log_event("resumed", "Resumed.", life)
        print(f"Ember resumed at moment {life.ticks:,}.")
    ensure_observer(life)
    record_mind_changes(life)

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

    Window.speed = args.speed if args.speed is not None else getattr(life, "speed", 20.0)
    headless = server is None              # without a window there is no one to be away: it just lives
    last_save = time.time()
    last_snap = 0.0
    last_t = time.time()
    rate = deque(maxlen=50)
    n_this_session = 0
    try:
        while not stop.is_set():
            if not headless and time.time() - Window.seen_at > PRESENT_FOR:
                # nobody is watching: its time waits, and is lived when you come back
                if getattr(life, "away_since", None) is None:
                    life.away_since = now_iso()
                    if getattr(life.world, "light", None) is not None:
                        life.world.clear_light()       # you left: the light goes with you
                if time.time() - last_save > SAVE_EVERY:
                    life.sessions[-1][1] = now_iso()
                    save(life)
                    last_save = time.time()
                stop.wait(0.2)
                last_t = time.time()
                continue
            if getattr(life, "away_since", None) is not None:
                catch_up(life, stop)
                last_t = time.time()
                continue
            t0 = time.time()
            tick(life)
            n_this_session += 1
            life.awake_seconds += t0 - last_t
            last_t = t0
            rate.append(t0)
            tps = round((len(rate) - 1) / (rate[-1] - rate[0]), 1) if len(rate) > 1 and rate[-1] > rate[0] else 0
            life.speed = Window.speed
            if t0 - last_snap > 0.15:      # the window doesn't need more than ~7 updates a second
                publish(life, tps)
                last_snap = t0
            if time.time() - last_save > SAVE_EVERY:
                life.sessions[-1][1] = now_iso()
                save(life)
                last_save = time.time()
            if args.max_ticks and n_this_session >= args.max_ticks:
                break
            if Window.speed > 0:
                stop.wait(max(0.0, 1.0 / Window.speed - (time.time() - t0)))
    finally:
        life.sessions[-1][1] = now_iso()
        if getattr(life, "away_since", None) is None:
            life.away_since = now_iso()        # you're gone from now on, as far as it's concerned
        save(life)
        if server:
            server.shutdown()
        print(f"\nEmber is resting. Saved at moment {life.ticks:,}. Start again with: python ember.py")


if __name__ == "__main__":
    sys.exit(main())
