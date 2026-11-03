"""
Subcortex: the parts LLMs have nothing of.

- Hypothalamus (drives): homeostatic needs computed from interoception.
  Reward is not given by a human; it is *drive reduction* (homeostatic
  reinforcement learning, Keramati & Gutkin 2014). Valence and arousal
  fall out of this: valence = is my body getting better or worse,
  arousal = how far from OK am I.
- Amygdala (reflex): a fast, unconscious veto on stepping into a hazard
  that is right in front of me. It works whether or not the hazard ever
  reaches the global workspace.
- Basal ganglia (habits + action selection): a model-free value table
  learned from drive reduction, used when the deliberate plan has
  nothing to say, and as the final gate on which action is released.
"""
import numpy as np
from .world import N_ACTIONS, ACTIONS, VIEW_R, HAZARD, WALL

NEEDS = ["energy", "hydration", "integrity"]
WEIGHTS = np.array([1.0, 1.0, 1.4])
SETPOINT = 0.9


class Drives:
    def __init__(self):
        self.prev_drive = None
        self.valence = 0.0

    def needs(self, intero):
        return np.clip((SETPOINT - intero) / SETPOINT, 0.0, 1.0)

    def drive(self, intero):
        return float((WEIGHTS * self.needs(intero) ** 2).sum())

    def reward(self, intero):
        d = self.drive(intero)
        r = 0.0 if self.prev_drive is None else (self.prev_drive - d) * 10.0
        self.prev_drive = d
        self.valence = 0.9 * self.valence + 0.1 * np.tanh(r * 5)
        return r

    def arousal(self, intero):
        return float(self.needs(intero).max())


def amygdala_veto(view, action):
    dy, dx = ACTIONS[action]
    return view[VIEW_R + dy, VIEW_R + dx] == HAZARD and action != 0


class BasalGanglia:
    def __init__(self, rng, alpha=0.15, gamma=0.95):
        self.rng = rng
        self.alpha, self.gamma = alpha, gamma
        self.Q = {}

    def _q(self, s):
        if s not in self.Q:
            self.Q[s] = np.zeros(N_ACTIONS)
        return self.Q[s]

    @staticmethod
    def state(pos, need_idx):
        return (pos[0], pos[1], need_idx)

    def habit(self, s, temperature=0.3):
        q = self._q(s)
        p = np.exp((q - q.max()) / temperature)
        p /= p.sum()
        return int(self.rng.choice(N_ACTIONS, p=p))

    def learn(self, s, a, r, s2):
        q = self._q(s)
        q[a] += self.alpha * (r + self.gamma * self._q(s2).max() - q[a])

    def select(self, proposals, view):
        """Release the first proposed action not vetoed by the amygdala
        and not walking into a visible wall."""
        for a in proposals:
            if a is None:
                continue
            if amygdala_veto(view, a):
                continue
            dy, dx = ACTIONS[a]
            if a != 0 and view[VIEW_R + dy, VIEW_R + dx] == WALL:
                continue
            return a, False
        safe = [a for a in range(N_ACTIONS) if not amygdala_veto(view, a)]
        return int(self.rng.choice(safe)), True
