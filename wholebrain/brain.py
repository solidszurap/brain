"""Whole-brain skeleton: an LLM is ONE organ (language.py); everything else is here.

Region -> module map (each has a measurable function, not a metaphor):
  sensory cortex / world model ... Forecaster (NLMS per horizon) + world.py
  hippocampus ..................... EpisodicMemory (Jaccard novelty gate) + sleep pruning
  thalamus / global workspace ..... Workspace competition -> ignition -> broadcast
  brainstem / homeostasis ......... Homeostasis (surprise, energy, hunger set-points)
  attention schema / self-model ... self_attn: predicts what will win its own attention
  metacognition ................... error model: predicts the size of its own forecast error
  language cortex ................. language.py (verbalizes only, never counts as evidence)

All salience weights below are hand-set placeholders for a toy; replacing them
with learned specialists is the real work. Nothing here is evidence of experience.
"""
import json

from .language import TemplateCortex
from .ledger import Ledger
from .models import EMA, NLMS

SOURCES = ["perception", "memory", "planner", "curiosity", "consolidation"]
THETA = 0.35        # ignition threshold: below this, nothing reaches the workspace ("idle")
PERIOD = 24
PRIMARY_H = 6
PROBE_HS = [1, 3, 12]


def clamp01(v):
    return max(0.0, min(1.0, v))


def jaccard(a, b):
    A, B = set(a.split()), set(b.split())
    return len(A & B) / len(A | B) if A and B else 0.0


class EpisodicMemory:
    def __init__(self, threshold=0.35, cap=200, episodes=None, rejected=0):
        self.threshold, self.cap = threshold, cap
        self.episodes = episodes or []
        self.rejected = rejected

    def write_if_novel(self, t, text, surprise):
        for e in self.episodes:
            if jaccard(e["text"], text) > self.threshold:   # anti-rumination gate
                self.rejected += 1
                return False
        self.episodes.append({"t": t, "text": text, "surprise": surprise})
        if len(self.episodes) > self.cap:
            self.episodes.remove(min(self.episodes, key=lambda e: e["surprise"]))
        return True

    def consolidate(self, keep=100):
        """'Sleep': keep the most surprising episodes, drop the rest."""
        self.episodes = sorted(self.episodes, key=lambda e: -e["surprise"])[:keep]
        self.episodes.sort(key=lambda e: e["t"])


class Homeostasis:
    """Internal variables with set-points. setpoint_error() is a crude proxy,
    NOT Friston's variational free energy."""

    def __init__(self, st=None):
        st = st or {}
        self.err_scale = EMA.from_state(0.01, st["err_scale"]) if st else EMA(0.01)
        self.surprise = st.get("surprise", 1.0)
        self.energy = st.get("energy", 0.8)
        self.hunger = st.get("hunger", 0.0)

    def observe_error(self, abs_err, best_base_err):
        self.err_scale.update(abs_err)
        s = abs_err / (self.err_scale.value + 1e-9)
        self.surprise += 0.3 * (s - self.surprise)
        gain = (best_base_err - abs_err) / (best_base_err + 1e-9)
        self.energy += 0.004 * max(-1.0, min(1.0, gain))   # rewarded for beating baselines

    def tick(self):
        self.energy = clamp01(self.energy - 0.004)
        # boredom: hunger grows faster when the world is predictable
        self.hunger = clamp01(self.hunger + 0.01 + 0.03 * max(0.0, 1.0 - self.surprise))

    def setpoint_error(self):
        return (self.surprise - 1.0) ** 2 + (0.8 - self.energy) ** 2

    def state(self):
        return {"err_scale": self.err_scale.state(), "surprise": self.surprise,
                "energy": self.energy, "hunger": self.hunger}


class Agent:
    def __init__(self, ledger=None, source="unknown", synthetic=True,
                 broadcast_effects=True, cortex=None, mu=0.1):
        self.ledger = ledger or Ledger()
        self.source, self.synthetic = source, synthetic
        self.effects = broadcast_effects      # False = ablation: workspace result changes nothing
        self.cortex = cortex or TemplateCortex()
        self.mu = mu
        self.t = 0
        self.hist = []
        self.mean_ema = EMA(0.02)
        self.err_ema = EMA(0.05)
        self.models = {}
        self.err_model = NLMS(3, mu=0.05, w=[1.0, 0.0, 0.0])
        self.memory = EpisodicMemory()
        self.home = Homeostasis()
        self.self_attn = {s: NLMS(5, mu=0.2) for s in SOURCES}
        self.ticks_since_write = 0
        self.boost = 0
        self.probe_i = 0
        self.prev_winner = "idle"
        self.winner_counts = {}
        self.selfstats = {"n": 0, "model": 0, "prev": 0, "mode": 0}
        self.pending = {}
        self.monologue = []

    # ---------- world model ----------
    def _features(self, h):
        H = self.hist
        x0 = H[-1]
        x1 = H[-2] if len(H) >= 2 else x0
        x2 = H[-3] if len(H) >= 3 else x0
        feats = [x0, x1, x2]
        for k in (1, 2, 3):
            idx = len(H) - 1 + h - k * PERIOD
            feats.append(H[idx] if 0 <= idx < len(H) else x0)
        feats.append(1.0)
        return feats

    def _seasonal_naive(self, h):
        idx = len(self.hist) - 1 + h - PERIOD
        return self.hist[idx] if 0 <= idx < len(self.hist) else self.hist[-1]

    def _predict(self, h, primary):
        if len(self.hist) < 2:
            return
        feats = self._features(h)
        if h not in self.models:
            self.models[h] = NLMS(len(feats), mu=self.mu)
        pred = self.models[h].predict(feats)
        bases = {"persistence": self.hist[-1], "seasonal": self._seasonal_naive(h),
                 "mean": self.mean_ema.value}
        exp = base_err = ef = None
        if primary:
            ef = [self.err_ema.value, self.home.surprise, 1.0]
            exp = max(0.0, self.err_model.predict(ef))
            base_err = self.err_ema.value
        rid = self.ledger.predict(self.t, self.t + h, h, pred, bases, self.source,
                                  self.synthetic, exp, base_err)
        self.pending[rid] = {"target_t": self.t + h, "h": h, "pred": pred, "feats": feats,
                             "bases": bases, "err_feats": ef}

    # ---------- self-model (attention schema) ----------
    def _state_vec(self):
        return [self.home.surprise, self.home.energy, self.home.hunger,
                min(self.ticks_since_write, 100) / 100.0, 1.0]

    def predict_winner(self):
        """What will win my attention next cycle, predicted from my own state."""
        v = self._state_vec()
        pred = {s: self.self_attn[s].predict(v) for s in SOURCES}
        top = max(SOURCES, key=lambda s: (pred[s], s))
        return top if pred[top] >= THETA else "idle"

    # ---------- workspace ----------
    def _proposals(self):
        h = self.home
        s = clamp01(h.surprise / 2.5)
        return {
            "perception": s,
            "memory": clamp01((self.ticks_since_write / 60.0) * (0.5 + 0.5 * s)),
            "planner": 0.45,
            "curiosity": h.hunger,
            "consolidation": clamp01((0.55 - h.energy) * 3.0),
        }

    # ---------- one cognitive cycle ----------
    def tick(self, x):
        self.t += 1
        self.hist.append(x)
        self.hist = self.hist[-100:]
        self.mean_ema.update(x)
        self.ticks_since_write += 1
        prev_vec = self._state_vec()
        pw = self.predict_winner()          # self-prediction BEFORE anything this cycle happens

        mu = 0.3 if self.boost > 0 else self.mu
        for rid in [r for r, i in self.pending.items() if i["target_t"] == self.t]:
            info = self.pending.pop(rid)
            self.ledger.resolve(rid, x)
            ae = abs(x - info["pred"])
            self.models[info["h"]].update(info["feats"], x, mu=mu)
            if info["h"] == PRIMARY_H:
                self.home.observe_error(ae, min(abs(x - b) for b in info["bases"].values()))
                self.err_model.update(info["err_feats"], ae)
                self.err_ema.update(ae)
        if self.boost > 0:
            self.boost -= 1
        self.home.tick()

        props = self._proposals()
        top = sorted(props, key=lambda s: (-props[s], s))[0]
        winner = top if props[top] >= THETA else "idle"

        if self.t > 300:
            st = self.selfstats
            mode = max(self.winner_counts, key=self.winner_counts.get) if self.winner_counts else "idle"
            st["n"] += 1
            st["model"] += int(pw == winner)
            st["prev"] += int(self.prev_winner == winner)
            st["mode"] += int(mode == winner)
        for s in SOURCES:
            self.self_attn[s].update(prev_vec, props[s])
        self.winner_counts[winner] = self.winner_counts.get(winner, 0) + 1

        probe = None
        if self.effects:                    # broadcast: the winner changes what the whole system does
            if winner == "perception":
                self.boost = 5              # attend to anomaly -> learn faster
            elif winner == "memory":
                prev_x = self.hist[-2] if len(self.hist) > 1 else x
                text = "surprise:%d phase:%d dir:%s level:%d" % (
                    int(self.home.surprise * 2), (self.t % PERIOD) // 3,
                    "up" if x >= prev_x else "down", round(x))
                self.memory.write_if_novel(self.t, text, self.home.surprise)
                self.ticks_since_write = 0
            elif winner == "curiosity":
                probe = PROBE_HS[self.probe_i % len(PROBE_HS)]
                self.probe_i += 1
                self.home.hunger = 0.0
            elif winner == "consolidation":
                self.memory.consolidate()
                self.home.energy = min(1.0, self.home.energy + 0.4)

        self._predict(PRIMARY_H, primary=True)
        if probe:
            self._predict(probe, primary=False)
        self.prev_winner = winner
        if self.t % 200 == 0:
            self.monologue.append(self.cortex.narrate(dict(
                t=self.t, winner=winner, surprise=self.home.surprise,
                energy=self.home.energy, hunger=self.home.hunger,
                episodes=len(self.memory.episodes))))
            self.monologue = self.monologue[-20:]
        return {"t": self.t, "winner": winner, "predicted_winner": pw,
                "surprise": self.home.surprise, "energy": self.home.energy,
                "hunger": self.home.hunger}

    # ---------- persistence (pending predictions are voided on save) ----------
    def to_state(self):
        return {
            "t": self.t, "hist": self.hist, "mean_ema": self.mean_ema.state(),
            "err_ema": self.err_ema.state(),
            "models": {str(h): m.w for h, m in self.models.items()},
            "err_model": self.err_model.w,
            "memory": {"episodes": self.memory.episodes, "rejected": self.memory.rejected},
            "home": self.home.state(),
            "self_attn": {s: m.w for s, m in self.self_attn.items()},
            "ticks_since_write": self.ticks_since_write, "boost": self.boost,
            "probe_i": self.probe_i, "prev_winner": self.prev_winner,
            "winner_counts": self.winner_counts, "selfstats": self.selfstats,
            "monologue": self.monologue,
        }

    @classmethod
    def from_state(cls, st, **kw):
        a = cls(**kw)
        a.t, a.hist = st["t"], list(st["hist"])
        a.mean_ema = EMA.from_state(0.02, st["mean_ema"])
        a.err_ema = EMA.from_state(0.05, st["err_ema"])
        a.models = {int(h): NLMS(len(w), mu=a.mu, w=w) for h, w in st["models"].items()}
        a.err_model = NLMS(3, mu=0.05, w=st["err_model"])
        a.memory = EpisodicMemory(episodes=[dict(e) for e in st["memory"]["episodes"]],
                                  rejected=st["memory"]["rejected"])
        a.home = Homeostasis(st["home"])
        a.self_attn = {s: NLMS(5, mu=0.2, w=w) for s, w in st["self_attn"].items()}
        a.ticks_since_write, a.boost = st["ticks_since_write"], st["boost"]
        a.probe_i, a.prev_winner = st["probe_i"], st["prev_winner"]
        a.winner_counts, a.selfstats = dict(st["winner_counts"]), dict(st["selfstats"])
        a.monologue = list(st["monologue"])
        return a

    def save(self, path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_state(), f)

    @classmethod
    def load(cls, path, **kw):
        with open(path, encoding="utf-8") as f:
            return cls.from_state(json.load(f), **kw)
