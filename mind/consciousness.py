"""
Is Ember getting closer to self-awareness or consciousness? The tracker.

Nobody can measure consciousness directly, in animals or machines. What can be
done honestly is:

  1. Check its design against the indicator properties that the main
     scientific theories of consciousness point to (Butlin, Long et al. 2023,
     "Consciousness in Artificial Intelligence: Insights from the Science of
     Consciousness"): 14 indicators from recurrent processing theory, global
     workspace theory, higher-order theories, attention schema theory,
     predictive processing, and agency/embodiment. Each is marked absent,
     partial or present in Ember's design.
  2. For the ones that can be tested, test whether they actually *work* in
     its life, with pass/fail rules written down in advance (below, in code)
     so the result can't be argued after the fact.
  3. Track self-awareness on a developmental ladder (Rochat 2003, "Five levels
     of self-awareness as they unfold early in life"), each level with its own
     test.

Every 2,000 moments the tracker closes a measurement window. A windowed test
counts as reached once it passes 3 windows in a row, and as lost if it then
fails 3 in a row. Every first pass and every loss is written into Ember's life
record as a milestone, with the date.

None of this would show that Ember feels anything. It shows how much of what
the theories say consciousness *requires* is present and working.
"""
import copy
from collections import Counter, deque

import numpy as np

from .world import WALL, WATER, HAZARD
from .wideworld import LEVER, GATE
from .situations import situation, HARD, reseed, live

WINDOW = 2000
STREAK = 3
CLONE_EVERY = 20000      # a copy test falls due every 20,000 moments in the wide world...
CLONE_MAX_WAIT = 6000    # ...then waits for a hard moment, at most this long
CLONE_PAIRS = 3          # pairs of copies (workspace on / off), each pair with its own luck
CLONE_MOMENTS = 500      # how long each copy lives

# ------------------------------------------------------------- the ladder
LADDER = [
    {"level": 1, "name": "Differentiation",
     "means": "Tells what it does from what happens to it.",
     "test": "Notices pushes: hits minus false alarms >= 0.8, and >= 60% of pushes noticed in the "
             "landmark-poor plains (at least 15 plains pushes seen). 3 windows in a row.",
     "id": "L1"},
    {"level": 2, "name": "Situation",
     "means": "Knows where it is in its world, and knows when it doesn't.",
     "test": "Right about its own position >= 95% of the time, and when it is wrong its confidence is "
             "clearly lower (>= 0.2 lower) than when it is right. 3 windows in a row.",
     "id": "L2"},
    {"level": 3, "name": "Identification",
     "means": "Recognizes itself (the mirror test, by contingency).",
     "test": "Has judged at least 3 figures to be itself, and at least 80% of all its me/not-me "
             "judgments about figures were right (at least 5 judgments).",
     "id": "L3"},
    {"level": 4, "name": "Permanence",
     "means": "Its own past guides its future across time.",
     "test": "After a full year in the wide world: at least 5 trips to where food grew in the same "
             "season before, and at least half of them found food.",
     "id": "L4"},
    {"level": 5, "name": "Self-consciousness",
     "means": "Knows how it appears to others.",
     "test": "Not testable yet: there are no other minds in its world.",
     "id": None},
]

# ------------------------------------------------------------ indicators
INDICATORS = [
    {"code": "RPT-1", "theory": "Recurrent processing", "name": "Recurrence in perception",
     "status": "absent", "in_ember": "Its senses are feed-forward: each view is processed once.", "id": None},
    {"code": "RPT-2", "theory": "Recurrent processing", "name": "Integrated perceptual representations",
     "status": "partial", "in_ember": "What it sees is integrated into one map of its world.", "id": "RPT-2"},
    {"code": "GWT-1", "theory": "Global workspace", "name": "Specialised systems in parallel",
     "status": "present", "in_ember": "Needs, vision, memory, pain, surprise, curiosity, hearing and its "
                                       "self-model all propose contents at once.", "id": "GWT-1"},
    {"code": "GWT-2", "theory": "Global workspace", "name": "Limited-capacity workspace, selective attention",
     "status": "present", "in_ember": "One content at a time wins; most proposals never get in.", "id": "GWT-2"},
    {"code": "GWT-3", "theory": "Global workspace", "name": "Global broadcast",
     "status": "present", "in_ember": "What wins is used by planning, memory and report. Tested by "
                                       "switching the workspace off in a copy of Ember.", "id": "GWT-3"},
    {"code": "GWT-4", "theory": "Global workspace", "name": "Using attention to carry out complex tasks",
     "status": "partial", "in_ember": "Two-step plans held in the workspace: open the gate, then eat.", "id": "GWT-4"},
    {"code": "HOT-1", "theory": "Higher-order", "name": "Generative, top-down perception",
     "status": "partial", "in_ember": "A learned model predicts what it will see next.", "id": None},
    {"code": "HOT-2", "theory": "Higher-order", "name": "Monitoring which representations are reliable",
     "status": "present", "in_ember": "Predicts its own prediction errors; learns which landmarks change.", "id": "HOT-2"},
    {"code": "HOT-3", "theory": "Higher-order", "name": "Beliefs updated by that monitoring guide action",
     "status": "partial", "in_ember": "Its belief about where it is updates on surprise and its push sense; "
                                       "plans use that belief.", "id": "HOT-3"},
    {"code": "HOT-4", "theory": "Higher-order", "name": "Sparse, smooth coding ('quality space')",
     "status": "absent", "in_ember": "Not built.", "id": None},
    {"code": "AST-1", "theory": "Attention schema", "name": "A model of its own attention",
     "status": "present", "in_ember": "Predicts what will grab its attention next.", "id": "AST-1"},
    {"code": "PP-1", "theory": "Predictive processing", "name": "Predictive coding in perception",
     "status": "partial", "in_ember": "Prediction errors drive attention, learning and self-location; "
                                       "perception itself is not hierarchical predictive coding.", "id": None},
    {"code": "AE-1", "theory": "Agency and embodiment", "name": "Learning from feedback, juggling goals",
     "status": "partial", "in_ember": "Competing needs; learns what helps and hurts; but most route-finding "
                                       "is still a hand-written planner.", "id": "AE-1"},
    {"code": "AE-2", "theory": "Agency and embodiment", "name": "Modelling how its actions change its input",
     "status": "present", "in_ember": "Forward model, efference copy, optic flow and a push sense tell "
                                       "self-caused from world-caused change.", "id": "AE-2"},
]

TEST_TEXT = {
    "RPT-2": "Its map's landmarks are >= 95% correct. 3 windows in a row.",
    "GWT-1": ">= 5 different systems won the workspace in the window. 3 windows in a row.",
    "GWT-2": "Something ignites in 0.5-30% of moments, and <= 10% of proposals get in. 3 windows in a row.",
    "GWT-3": "In >= 2 of the last 3 copy tests, the copies with their workspace switched on did better. "
             "Each copy test starts at a hard moment (winter with the gate shut, two needs low, ponds "
             "drying, or just after coming round) and runs 3 pairs of copies with different luck. Better = "
             "lower need-error in >= 2 of 3 pairs and >= 10% lower on average, or >= 2 fewer collapses in "
             "total, or more two-step plans without need-error >= 10% worse. (Copy tests from before "
             "this design started at ordinary moments; they are kept but not judged.)",
    "GWT-4": ">= 3 two-step plans completed (opened the gate itself, then reached the food).",
    "HOT-2": "Its expected and actual surprise correlate >= 0.3, and >= 80% of landmarks it marks as "
             "unreliable really do change. 3 windows in a row.",
    "HOT-3": "Right about its position >= 95% and notices >= 80% of pushes. 3 windows in a row.",
    "AST-1": "Predicts its own next thought >= 20 points better than always guessing the most common. "
             "3 windows in a row.",
    "AE-1": "Has learned that something hurts, then almost never touches it (<= 1 per window), with no "
            "collapse and low need-error. 3 windows in a row.",
    "AE-2": "Notices pushes: hits minus false alarms >= 0.8. 3 windows in a row.",
}
EVENT_TESTS = {"L3", "L4", "GWT-3", "GWT-4"}   # judged on everything so far, not 3 windows in a row


def _live_quietly(life, n):
    """Run a copy of Ember for n moments, no logging (kept for older callers)."""
    return live(life, n)


class Observer:
    """The scientist watching from outside. Not part of Ember's mind."""

    def __init__(self, anchor, early_history=None):
        self.anchor = tuple(int(v) for v in anchor)   # true position - believed position
        self.early = list(early_history or [])       # self-knowledge windows from before the wide world
        self.history = []
        self.state = {}                               # test id -> {"met", "streak", "fails", "first", ...}
        self.milestones = []
        self.clone_tests = []
        self.cum = Counter()
        self.figures = deque(maxlen=600)             # (tick, reflection, wanderer) ground truth
        self._reset()

    def _reset(self):
        self.w = Counter()
        self.sources = Counter()
        self.conf_right, self.conf_wrong = [], []
        self._cands0 = None

    # ------------------------------------------------------------ per moment
    def observe(self, life, info, last, schema_score):
        w, m = life.world, life.mind
        W = self.w
        if self._cands0 is None:
            self._cands0 = getattr(m, "candidates_posted", 0)
        self.figures.append((m.t, getattr(w, "reflection", None), getattr(w, "wanderer", None)))
        W["n"] += 1
        ok = (w.pos[0] - m.hippo.pos[0], w.pos[1] - m.hippo.pos[1]) == self.anchor and not m.hippo.lost
        W["located"] += ok
        conf = getattr(m.hippo, "confidence", 1.0)
        (self.conf_right if ok else self.conf_wrong).append(conf)
        plains = info.get("region") in ("plains", "mirror pool")
        noticed = bool(last.get("external"))
        if info.get("pushed"):
            W["pushes"] += 1
            W["hits"] += noticed
            if plains:
                self.cum["plains_pushes"] += 1
                self.cum["plains_hits"] += noticed
        else:
            W["quiet"] += 1
            W["false_alarms"] += noticed
        if schema_score is not None:
            W["schema_n"] += 1
            W["schema_hits"] += schema_score[0]
            W["schema_base"] += schema_score[1]
        if last.get("ignited") and last.get("broadcast"):
            W["ignitions"] += 1
            cur = m.gw.current
            if cur is not None:
                self.sources[cur.source] += 1
        if last.get("surprise") is not None:
            W["surprise_n"] += 1
            W["surprise_sum"] += last["surprise"]
        W["drive_sum"] += m.drives.drive(life.intero)
        if info.get("consumed") == "dark berry":
            W["dark"] += 1
        # mirror judgments, checked against which figure it really was
        for res in getattr(m, "new_classifications", []):
            truth = self._which_figure(res) if ok else None    # can't score it if it was lost
            if truth is None:
                continue
            correct = (res["label"] == "self") == (truth == "reflection")
            self.cum["mirror_judgments"] += 1
            self.cum["mirror_correct"] += correct
            self.cum["mirror_self"] += res["label"] == "self"
            self.cum["mirror_self_correct"] += res["label"] == "self" and truth == "reflection"
        # trips to where food grew this season before
        n_ant = len(getattr(m, "anticipations", []))
        if n_ant > self.cum["anticipations_seen"]:
            self.cum["anticipation_trips"] += n_ant - self.cum["anticipations_seen"]
            self.cum["anticipations_seen"] = n_ant
            self.cum["anticipation_hits"] += info.get("consumed") == "food"
        self.cum["two_step"] = sum(1 for x in getattr(m, "multi_step", []) if x[2] is not None)

    def _which_figure(self, res):
        ty, tx = res["last_pos"][0] + self.anchor[0], res["last_pos"][1] + self.anchor[1]
        for t, refl, wand in reversed(self.figures):
            if t <= res["last_t"] + 1:
                cand = []
                if refl is not None:
                    cand.append((abs(refl[0] - ty) + abs(refl[1] - tx), "reflection"))
                if wand is not None:
                    cand.append((abs(wand[0] - ty) + abs(wand[1] - tx), "wanderer"))
                if not cand:
                    return None
                cand.sort()
                if cand[0][0] > 1 or (len(cand) > 1 and cand[0][0] == cand[1][0]):
                    return None          # can't tell which one it was looking at
                return cand[0][1]
        return None

    @property
    def window_full(self):
        return self.w["n"] >= WINDOW

    # --------------------------------------------------------- window close
    def _landmark_reliability(self, life):
        w, hp = life.world, life.mind.hippo
        vol = getattr(hp, "volatile", None)
        if vol is None:
            return None, None, 0
        changing = set(map(tuple, w.gate_cells)) | set(map(tuple, w.seasonal_ponds)) \
            | set(map(tuple, getattr(w, "opened_passes", [])))
        flagged = {(int(y) + self.anchor[0], int(x) + self.anchor[1]) for y, x in np.argwhere(vol)}
        seen = {c for c in changing
                if 0 <= c[0] - self.anchor[0] < hp.size and 0 <= c[1] - self.anchor[1] < hp.size
                and hp.seen[c[0] - self.anchor[0], c[1] - self.anchor[1]] > 0}
        precision = len(flagged & changing) / len(flagged) if flagged else None
        recall = len(flagged & seen) / len(seen) if seen else None
        return precision, recall, len(flagged)

    def _map_accuracy(self, life):
        w, hp = life.world, life.mind.hippo
        vol = getattr(hp, "volatile", np.zeros_like(hp.map, dtype=bool))
        ys, xs = np.where(np.isin(hp.map, (WALL, WATER, HAZARD, LEVER)) & ~vol)
        ok = n = 0
        for y, x in zip(ys, xs):
            ty, tx = y + self.anchor[0], x + self.anchor[1]
            truth = w.grid[ty, tx] if (0 <= ty < w.H and 0 <= tx < w.W) else WALL
            ok += truth == hp.map[y, x]
            n += 1
        return ok / n if n else None

    def close_window(self, life, now_iso):
        m, W = life.mind, self.w
        n = max(W["n"], 1)
        precision, recall, n_flagged = self._landmark_reliability(life)
        cands = getattr(m, "candidates_posted", 0) - (self._cands0 or 0)
        cr, cw = self.conf_right, self.conf_wrong
        rec = {
            "tick": life.ticks, "time": now_iso, "season": getattr(life.world, "season", None),
            "location": round(W["located"] / n, 4),
            "wrong_moments": len(cw),
            "confidence_gap": round(float(np.mean(cr) - np.mean(cw)), 3) if cr and cw else None,
            "pushes": W["pushes"],
            "detect_hit": round(W["hits"] / W["pushes"], 4) if W["pushes"] else None,
            "detect_false_alarm": round(W["false_alarms"] / W["quiet"], 4) if W["quiet"] else None,
            "plains_pushes_total": self.cum["plains_pushes"],
            "plains_hit_total": round(self.cum["plains_hits"] / self.cum["plains_pushes"], 3) if self.cum["plains_pushes"] else None,
            "calibration": round(float(m.meta.calibration(WINDOW)), 4),
            "schema": round(W["schema_hits"] / W["schema_n"], 4) if W["schema_n"] else None,
            "schema_baseline": round(W["schema_base"] / W["schema_n"], 4) if W["schema_n"] else None,
            "schema_n": W["schema_n"],
            "ignition_rate": round(W["ignitions"] / n, 4),
            "ignite_fraction": round(W["ignitions"] / cands, 4) if cands else None,
            "sources": len(self.sources),
            "surprise": round(W["surprise_sum"] / W["surprise_n"], 4) if W["surprise_n"] else None,
            "need_error": round(W["drive_sum"] / n, 4),
            "collapses": life.world.collapses - self.cum["collapses_seen"],
            "dark_contacts": W["dark"],
            "harm_learned": bool(getattr(m, "harmful", set())),
            "landmark_precision": None if precision is None else round(precision, 3),
            "landmark_recall": None if recall is None else round(recall, 3),
            "landmarks_flagged": n_flagged,
            "map_accuracy": None if self._map_accuracy(life) is None else round(self._map_accuracy(life), 4),
            "mirror_judgments": self.cum["mirror_judgments"],
            "mirror_correct": self.cum["mirror_correct"],
            "mirror_self": self.cum["mirror_self"],
            "two_step": self.cum["two_step"],
            "anticipation_trips": self.cum["anticipation_trips"],
            "anticipation_hits": self.cum["anticipation_hits"],
            "wide_age": life.ticks - life.valley_opened["tick"],
        }
        if rec["detect_hit"] is not None and rec["detect_false_alarm"] is not None:
            rec["self_other"] = round(rec["detect_hit"] - rec["detect_false_alarm"], 4)
        else:
            rec["self_other"] = None
        self.cum["collapses_seen"] = life.world.collapses
        self.history.append(rec)
        events = self._judge(rec, now_iso)
        self._reset()
        return rec, events

    # ---------------------------------------------------------------- tests
    def _test(self, tid, r):
        """Pre-registered rules. Return True (pass), False (fail) or None (not enough data)."""
        if tid == "L1":
            if r["pushes"] < 10 or r["self_other"] is None:
                return None
            if self.cum["plains_pushes"] < 15:
                return None
            return r["self_other"] >= 0.8 and self.cum["plains_hits"] / self.cum["plains_pushes"] >= 0.6
        if tid == "L2":
            if r["location"] < 0.95:
                return False
            if r["wrong_moments"] < 20 or r["confidence_gap"] is None:
                return True
            return r["confidence_gap"] >= 0.2
        if tid == "L3":
            j, c, me = self.cum["mirror_judgments"], self.cum["mirror_correct"], self.cum["mirror_self_correct"]
            if j < 5:
                return None
            return me >= 3 and c / j >= 0.8
        if tid == "L4":
            if r["wide_age"] < 12000:
                return None
            t, h = self.cum["anticipation_trips"], self.cum["anticipation_hits"]
            if t < 5:
                return None
            return h / t >= 0.5
        if tid == "RPT-2":
            return None if r["map_accuracy"] is None else r["map_accuracy"] >= 0.95
        if tid == "GWT-1":
            return r["sources"] >= 5
        if tid == "GWT-2":
            if r["ignite_fraction"] is None:
                return None
            return 0.005 <= r["ignition_rate"] <= 0.3 and r["ignite_fraction"] <= 0.1
        if tid == "GWT-3":
            last3 = [t for t in self.clone_tests if "pairs" in t][-3:]   # only tests started at hard moments
            if len(last3) < 2:
                return None
            return sum(t["workspace_helps"] for t in last3) >= 2
        if tid == "GWT-4":
            return True if self.cum["two_step"] >= 3 else None
        if tid == "HOT-2":
            ok = r["calibration"] >= 0.3
            if r["landmark_precision"] is not None and r["landmarks_flagged"] >= 3:
                ok = ok and r["landmark_precision"] >= 0.8
            return ok
        if tid == "HOT-3":
            if r["pushes"] < 10 or r["detect_hit"] is None:
                return None
            return r["location"] >= 0.95 and r["detect_hit"] >= 0.8
        if tid == "AST-1":
            if r["schema_n"] < 30:
                return None
            return r["schema"] - r["schema_baseline"] >= 0.2
        if tid == "AE-1":
            if not r["harm_learned"]:
                return None
            return r["dark_contacts"] <= 1 and r["collapses"] == 0 and r["need_error"] < 0.2
        if tid == "AE-2":
            if r["pushes"] < 10 or r["self_other"] is None:
                return None
            return r["self_other"] >= 0.8
        return None

    def _judge(self, rec, now_iso):
        events = []
        ids = [x["id"] for x in LADDER if x["id"]] + [x["id"] for x in INDICATORS if x["id"]]
        for tid in ids:
            st = self.state.setdefault(tid, {"met": False, "streak": 0, "fails": 0, "first": None,
                                              "last_result": None})
            res = self._test(tid, rec)
            st["last_result"] = res
            if res is None:
                continue
            need = 1 if tid in EVENT_TESTS else STREAK
            if res:
                st["streak"] += 1
                st["fails"] = 0
                if not st["met"] and st["streak"] >= need:
                    st["met"] = True
                    if st["first"] is None:
                        st["first"] = {"tick": rec["tick"], "time": now_iso}
                    events.append(self._milestone(tid, True, rec, now_iso))
            else:
                st["streak"] = 0
                st["fails"] += 1
                if st["met"] and st["fails"] >= STREAK:
                    st["met"] = False
                    events.append(self._milestone(tid, False, rec, now_iso))
        return events

    def _milestone(self, tid, reached, rec, now_iso):
        lad = {x["id"]: x for x in LADDER if x["id"]}
        ind = {x["id"]: x for x in INDICATORS if x["id"]}
        if tid in lad:
            what = f"Self-awareness level {lad[tid]['level']} ({lad[tid]['name']})"
        else:
            what = f"Consciousness indicator {tid} ({ind[tid]['name']})"
        text = f"{what} {'reached' if reached else 'lost'}."
        ms = {"tick": rec["tick"], "time": now_iso, "id": tid, "reached": reached, "text": text}
        self.milestones.append(ms)
        return ms

    # ------------------------------------------------------------ copy test
    def clone_test_due(self, life):
        age = life.ticks - life.valley_opened["tick"]
        done = len(self.clone_tests)
        return age >= (done + 1) * CLONE_EVERY

    def clone_test_ready(self, life, info=None):
        """Due, and now is a hard moment (or it has waited long enough).
        Returns the situation's name, or None if not yet."""
        if not self.clone_test_due(life):
            self.clone_wait_start = None
            return None
        if getattr(self, "clone_wait_start", None) is None:
            self.clone_wait_start = life.ticks
        s = situation(life, info)
        if s in HARD:
            return s
        if life.ticks - self.clone_wait_start >= CLONE_MAX_WAIT:
            return s or "no hard moment came"
        return None

    def run_clone_test(self, life, now_iso, sit=None):
        """Copy Ember, switch the workspace off in half the copies, and let
        each pair live the same moments with the same luck; several pairs,
        each with different luck. The real Ember is not affected."""
        pairs = []
        for k in range(CLONE_PAIRS):
            a = copy.deepcopy(life)
            b = copy.deepcopy(life)
            b.mind.gw.enabled = False
            seed = int(life.ticks) * 10 + k
            reseed(a, seed)
            reseed(b, seed)
            pairs.append((live(a, CLONE_MOMENTS), live(b, CLONE_MOMENTS)))
        keys = ["need_error", "collapses", "two_step", "loop_collapses", "meals", "lost"]

        def avg(i, key):
            vals = [p[i][key] for p in pairs if p[i][key] is not None]
            return round(float(np.mean(vals)), 4) if vals else None
        ra = {k: avg(0, k) for k in keys}
        rb = {k: avg(1, k) for k in keys}
        wins = sum(pa["need_error"] < pb["need_error"] for pa, pb in pairs)
        ca = sum(pa["collapses"] for pa, _ in pairs)
        cb = sum(pb["collapses"] for _, pb in pairs)
        ta = sum(pa["two_step"] for pa, _ in pairs)
        tb = sum(pb["two_step"] for _, pb in pairs)
        helps = ((wins >= 2 and ra["need_error"] <= 0.9 * rb["need_error"])
                 or ca <= cb - 2
                 or (ta > tb and ra["need_error"] < 1.1 * rb["need_error"]))
        res = {"tick": life.ticks, "time": now_iso, "situation": sit, "with_workspace": ra,
               "without_workspace": rb, "pairs": [[pa, pb] for pa, pb in pairs],
               "need_error_wins": int(wins), "workspace_helps": bool(helps)}
        self.clone_tests.append(res)
        self.clone_wait_start = None
        return res

    # -------------------------------------------------------------- summary
    def summary(self):
        lad, ind = [], []
        for x in LADDER:
            st = self.state.get(x["id"], {}) if x["id"] else {}
            lad.append({**x, "met": st.get("met", False), "first": st.get("first"),
                        "streak": st.get("streak", 0), "last_result": st.get("last_result"),
                        "testable": x["id"] is not None})
        for x in INDICATORS:
            st = self.state.get(x["id"], {}) if x["id"] else {}
            ind.append({**x, "test": TEST_TEXT.get(x["id"], "No functional test yet."),
                        "met": st.get("met", False), "first": st.get("first"),
                        "streak": st.get("streak", 0), "last_result": st.get("last_result"),
                        "testable": x["id"] is not None})
        level = 0
        for x in lad:
            if x["testable"] and x["met"]:
                level = x["level"]
            else:
                break
        return {
            "ladder": lad, "indicators": ind, "milestones": self.milestones[-50:],
            "clone_tests": self.clone_tests[-10:], "history": self.history[-300:], "early": self.early[-100:],
            "level": level,
            "built": Counter(x["status"] for x in INDICATORS),
            "working": sum(1 for x in ind if x["met"]),
            "testable": sum(1 for x in ind if x["testable"]),
            "window": WINDOW, "streak_needed": STREAK, "cum": dict(self.cum),
        }

    def report_md(self, life, now_iso):
        s = self.summary()
        L = [f"# Is Ember getting closer? ({now_iso})", "",
             f"Moments lived: {life.ticks:,} (in the wide world: {life.ticks - life.valley_opened['tick']:,}).",
             f"Self-awareness level reached: {s['level']} of 5 (Rochat's ladder).",
             f"Consciousness indicators (Butlin et al. 2023): {s['built']['present']} present, "
             f"{s['built']['partial']} partial, {s['built']['absent']} absent in its design; "
             f"{s['working']} of {s['testable']} testable ones pass their test now.", "",
             "None of this shows that Ember feels anything. It shows how much of what the main theories say "
             "consciousness requires is present and working.", "", "## Self-awareness ladder", ""]
        for x in s["ladder"]:
            status = "reached" if x["met"] else ("not testable yet" if not x["testable"] else "not yet")
            first = f" (first reached {x['first']['time']}, moment {x['first']['tick']:,})" if x["first"] else ""
            L.append(f"- **{x['level']}. {x['name']}**: {status}{first}. {x['means']} Test: {x['test']}")
        L += ["", "## Consciousness indicators", "", "| | Indicator | In Ember's design | Works in its life? |", "|---|---|---|---|"]
        for x in s["indicators"]:
            works = "passes" if x["met"] else ("no test" if not x["testable"] else "not yet")
            L.append(f"| {x['code']} | {x['name']} | {x['status']} | {works} |")
        L += ["", "## Milestones", ""]
        L += [f"- {m['time']} (moment {m['tick']:,}): {m['text']}" for m in s["milestones"]] or ["- none yet"]
        L += ["", "## Copy tests (workspace on vs off)", ""]
        for t in s["clone_tests"]:
            where = f" ({t['situation']}, {len(t['pairs'])} pairs)" if "pairs" in t else " (ordinary moment, old design: not judged)"
            L.append(f"- moment {t['tick']:,}{where}: with {t['with_workspace']}, without {t['without_workspace']}, "
                     f"workspace helps: {t['workspace_helps']}")
        if not s["clone_tests"]:
            L.append(f"- first one after {CLONE_EVERY:,} moments in the wide world")
        return "\n".join(L) + "\n"
