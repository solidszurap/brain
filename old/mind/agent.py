"""
The whole brain, wired together.

One tick of the mind:

  perceive ─► sensory cortex ─► world model predicts ─► metacognition
     │                                                      │
     │              surprise beyond expectation ◄───────────┘
     │                         │
     │                 self-model: "was that me?"
     │                         │
     ▼                         ▼
  drives (needs) ─► candidates ─► GLOBAL WORKSPACE (competition, ignition)
  percepts        ─►                      │ broadcast
  recall (hippo.) ─►                      ▼
  curiosity       ─►        PFC goal ─► plan on own cognitive map
                                          │
                     habits (basal ganglia)┤
                     reflex (amygdala) ────┤ veto
                                          ▼
                                       action ─► world
  sleep: no workspace, no action, hippocampal replay trains the cortex.

Each module can be switched off (ablation) to test what it is for.
"""
from collections import deque

import numpy as np
from .world import FOOD, WATER, HAZARD, VIEW_R, N_ACTIONS, TYPE_NAMES
from .cortex import encode, WorldModel
from .metacognition import Metacognition
from .hippocampus import Hippocampus, UNKNOWN
from .subcortex import Drives, BasalGanglia, NEEDS
from .workspace import GlobalWorkspace, Content
from .prefrontal import Prefrontal
from .language import LanguageCortex

DEFAULT_CONFIG = {
    "workspace": True,
    "hippocampus": True,
    "self_other": True,
    "sleep": True,
    "metacognition": True,
    "random": False,
}


class Mind:
    def __init__(self, seed=0, **config):
        self.cfg = {**DEFAULT_CONFIG, **config}
        self.rng = np.random.default_rng(seed + 1000)
        self.cortex = WorldModel(self.rng)
        self.meta = Metacognition(enabled=self.cfg["metacognition"])
        self.hippo = Hippocampus(self.rng, map_enabled=self.cfg["hippocampus"])
        self.drives = Drives()
        self.bg = BasalGanglia(self.rng)
        self.gw = GlobalWorkspace(self.rng, enabled=self.cfg["workspace"])
        self.pfc = Prefrontal()
        self.lang = LanguageCortex()

        self.sleeping = False
        self.sleep_need, self.wake_need = 0.35, 0.55  # only sleep when the body is OK
        self.relocalize_patience = 25  # ticks lost before starting a fresh map
        self.sleep_pressure = 0.0
        self.slept_for = 0
        self.sleeps = 0
        self.pending_surprise = None
        self.pain = 0.0
        self.agency = "self"
        self.t = 0
        self.stream = deque(maxlen=500)  # stream of consciousness: (t, content, report)
        self.last = {}

    # ================================================================ decide
    def decide(self, view, intero):
        self.t += 1
        x = encode(view, intero, self.cortex.n_types)
        needs = self.drives.needs(intero)
        dom = int(needs.argmax())
        self._ctx = {"x": x, "view": view, "intero": intero.copy(),
                     "s": BasalGanglia.state(self.hippo.pos, dom)}

        if self.cfg["random"]:
            a = int(self.rng.integers(N_ACTIONS))
            self._ctx["a"] = a
            self.last = {"broadcast": None, "ignited": False, "goal": None, "sleeping": False}
            return a

        if self.sleeping and getattr(self, "escape_reflex", False) and view[VIEW_R, VIEW_R] == HAZARD:
            self.sleeping = False  # pain wakes you up
        if self.sleeping:
            self._ctx["a"] = 0
            self.last = {"broadcast": None, "ignited": False, "goal": "sleep", "sleeping": True}
            return 0

        # ---- every module posts candidates into the workspace ----------
        for i, n in enumerate(NEEDS):
            self.gw.post(Content("need", n, float(needs[i]) ** 0.8 * (1.2 if i < 2 else 1.5), "hypothalamus"))
        for ttype, name, ni in ((FOOD, "food", 0), (WATER, "water", 1)):
            cells = np.argwhere(view == ttype)
            if len(cells):
                d = int(np.abs(cells - VIEW_R).sum(axis=1).min())
                self.gw.post(Content("percept", name, 0.12 + 1.1 * float(needs[ni]) ** 0.8, "visual cortex", {"dist": d}))
            elif needs[ni] > 0.2 and self.cfg["hippocampus"] and not self.hippo.lost:
                known = self.hippo.known(ttype)
                if known:
                    py, px = self.hippo.pos
                    d = min(abs(y - py) + abs(xx - px) for y, xx in known)
                    self.gw.post(Content("recall", name, 0.05 + 1.0 * float(needs[ni]) ** 0.8, "hippocampus", {"dist": d}))
        if self.pain > 0:
            self.gw.post(Content("threat", "hazard", 0.6 + self.pain, "amygdala"))
        if self.pending_surprise is not None:
            self.gw.post(self.pending_surprise)
            self.pending_surprise = None
        self.extra_candidates(view, intero, needs)
        frontier = self.hippo.frontier_size()
        mapped = self.hippo.map_enabled and (self.hippo.map != UNKNOWN).any()
        self.gw.post(Content("curiosity", "explore" if frontier or not mapped else "patrol", 0.32, "PFC",
                             {"frontier": frontier}))

        broadcast, ignited = self.gw.cycle()
        self.pfc.set_goal_from(broadcast, self.t)

        a, plan_a = self.choose_action(view, intero, needs)
        self._ctx["a"] = a
        self._ctx["conscious"] = broadcast is not None

        report = None
        if ignited and broadcast is not None:
            report = self.lang.report(broadcast, self.self_model(intero))
            self.stream.append((self.t, str(broadcast), report))
        self.last = {"broadcast": str(broadcast) if broadcast else None, "ignited": ignited,
                     "goal": self.pfc.goal, "sleeping": False, "report": report,
                     "used_plan": plan_a is not None and a == plan_a}
        return a

    def extra_candidates(self, view, intero, needs):
        """Hook for minds with more senses or skills (see mind/ember_mind.py)."""

    def choose_action(self, view, intero, needs):
        """v3 controller: deliberate plan on the cognitive map (PFC),
        habits as fallback, amygdala veto. Returns (action, plan action)."""
        if self.cfg["hippocampus"] and not self.hippo.lost:
            grid, pos, seen = self.hippo.map, self.hippo.pos, self.hippo.last_seen
        else:
            grid, pos, seen = view.copy(), (VIEW_R, VIEW_R), None
        plan_a = self.pfc.act(grid, pos, view, needs, seen)
        habit_a = self.bg.habit(self._ctx["s"])
        a, _ = self.bg.select([plan_a, habit_a], view)
        if getattr(self, "escape_reflex", False) and a == 0 and view[VIEW_R, VIEW_R] == HAZARD:
            # standing on something that hurts: get off it, whatever the plan says
            from .world import ACTIONS, WALL
            safe = [b for b in range(1, N_ACTIONS)
                    if view[VIEW_R + ACTIONS[b][0], VIEW_R + ACTIONS[b][1]] not in (WALL, HAZARD)]
            if safe:
                a = int(self.rng.choice(safe))
        return a, plan_a

    # ============================================================ experience
    def experience(self, next_view, next_intero, died):
        c = self._ctx
        x, a, view = c["x"], c["a"], c["view"]
        if self.cfg["random"]:
            return {}
        s_pred = self.cortex.surprisal(x, a, next_view)
        z, expected = self.meta.observe(x, a, s_pred)
        self.cortex.learn(x, a, next_view, next_intero - c["intero"])

        # ---- self-location and self/other attribution -----------------
        shift = None
        external = False
        if died:
            self.hippo.lost = True
            self.hippo.lost_for = 0
            self.agency = "reborn"
        else:
            # efference copy: where *my* action should have taken me
            self.hippo.path_integrate(a, view)
            # does what I see agree with that? Surprise lowers the bar.
            if self.cfg["self_other"]:
                shift = self.hippo.relocalize_local(next_view, margin=1.0 if z > 1.5 else 2.5)
                external = shift != (0, 0) or z > 2.5
            else:
                external = z > 2.5  # noticed, but never used to correct the self-location
            self.agency = "external" if external else "self"
            if external:
                self.pending_surprise = Content("surprise", "push", min(1.0, 0.35 + 0.12 * max(z, 0)),
                                                "self-model", {"z": round(z, 2), "shift": shift})
        if self.hippo.lost:
            self.hippo.lost_for += 1
            if not self.hippo.relocalize_global(next_view) and self.hippo.lost_for > self.relocalize_patience:
                self.hippo.reset_map()
        self.hippo.write_view(next_view, self.t)

        # ---- value learning from drive reduction ----------------------
        r = self.drives.reward(next_intero)
        if died:
            r = -5.0  # being reset is not relief
        self.pain = max(0.0, self.pain * 0.7 - 0.02)
        if next_intero[2] < c["intero"][2] - 0.05:
            self.pain = 0.6
        needs2 = self.drives.needs(next_intero)
        s2 = BasalGanglia.state(self.hippo.pos, int(needs2.argmax()))
        self.bg.learn(c["s"], a, r, s2)

        conscious = c.get("conscious", False)
        self.hippo.store({"x": x, "a": a, "next_view": next_view, "d": next_intero - c["intero"],
                          "s": c["s"], "r": r, "s2": s2, "surprise": s_pred,
                          "conscious": conscious, "ignited": bool(self.last.get("ignited")), "t": self.t,
                          "report": self.last.get("report") or self.last.get("broadcast") or "",
                          "priority": s_pred + (1.0 if conscious and self.last.get("ignited") else 0.0)})

        # ---- sleep ------------------------------------------------------
        woke = False
        if self.cfg["sleep"]:
            self.sleep_pressure += 1 / 350 + 0.002 * min(s_pred, 3)
            if self.sleeping:
                self._replay(24)
                self.slept_for += 1
                self.sleep_pressure = max(0.0, self.sleep_pressure - 0.04)
                if needs2.max() > self.wake_need or self.slept_for >= 30 or z > 3.0:
                    self.sleeping, woke = False, True
            elif self.sleep_pressure > 1.0 and needs2.max() < self.sleep_need and not self.hippo.lost and self.pain == 0:
                self.sleeping, self.slept_for = True, 0
                self.sleeps += 1

        self.last.update({"surprise": round(s_pred, 3), "expected": round(float(np.exp(expected)), 3),
                          "z": round(z, 2), "external": external, "shift": shift, "agency": self.agency,
                          "reward": round(r, 4), "woke": woke})
        return self.last

    def _replay(self, n):
        for e in self.hippo.sample(n):
            self.cortex.learn(e["x"], e["a"], e["next_view"], e["d"])
            s = self.cortex.surprisal(e["x"], e["a"], e["next_view"])
            self.meta.observe(e["x"], e["a"], s, learn=True)
            self.meta.history.pop()
            self.bg.learn(e["s"], e["a"], e["r"], e["s2"])

    # ============================================================ self-model
    def self_model(self, intero=None):
        if intero is None:
            intero = self._ctx["intero"]
        return {
            "body": {n: round(float(v), 2) for n, v in zip(NEEDS, intero)},
            "believed_position": self.hippo.pos if not self.hippo.lost else "lost",
            "attending": str(self.gw.current) if self.gw.current else "nothing",
            "goal": self.pfc.goal,
            "last_movement_caused_by": self.agency,
            "valence": round(self.drives.valence, 2),
            "arousal": round(self.drives.arousal(intero), 2),
            "sleeping": self.sleeping,
            "map_known": int((self.hippo.map != UNKNOWN).sum()),
            "world_model_confidence": round(float(np.clip(self.meta.calibration(300), 0, 1)), 2),
        }

    def ask(self, question):
        eps = [{"t": e["t"], "report": e["report"]} for e in self.hippo.recent_conscious(12) if e["report"]]
        return self.lang.ask(question, self.self_model(), eps)
