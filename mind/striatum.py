"""
Striatum + cognitive-map model: learning *where to go* from experience,
and dreaming over the map.

The hippocampus already gives the mind a map and a sense of where it is.
Here the mind learns two more things from its own life:

  Place model (hippocampus): what happens when I do action a at place p.
    - where I end up (walls block, so it learns the maze)
    - what happens to my body there (water here quenches thirst, the
      hazard here hurts, food often appears here)
  Place values (striatum): how good action a is at place p, given what
    my body needs right now (hungry / thirsty / hurt / content).

Real experience trains the values directly. Sleep can then:
  replay: re-learn from real remembered moments, exactly as they happened
  dream:  start at a remembered place, *imagine a body state* (maybe
          thirsty where I was only ever hungry), and walk through the place
          model, feeling the imagined consequences and learning from them.

Dreaming can teach something replay cannot: what a place is worth for a
need I never had there. That is Tolman's latent learning (1948): rats
that explored a maze without reward learned to use it fast once reward
appeared, because they already had the map.
"""
import numpy as np
from .world import ACTIONS, N_ACTIONS
from .imagination import drive

N_CTX = 4  # dominant need: energy, hydration, integrity, or content


def context(I):
    need = np.clip((0.9 - I) / 0.9, 0.0, 1.0)
    return int(need.argmax()) if need.max() > 0.15 else 3


class PlaceModel:
    def __init__(self, size):
        self.T = np.zeros((size, size, N_ACTIONS, N_ACTIONS))   # displacement counts
        self.B = np.zeros((size, size, N_ACTIONS, 3))           # summed body change
        self.N = np.zeros((size, size, N_ACTIONS))
        self.Die = np.zeros((size, size, N_ACTIONS))

    def observe(self, p, a, p2, dI, died):
        y, x = p
        self.N[y, x, a] += 1
        self.Die[y, x, a] += died
        if died:
            return
        self.B[y, x, a] += dI
        disp = (p2[0] - y, p2[1] - x)
        if disp in ACTIONS:
            self.T[y, x, a, ACTIONS.index(disp)] += 1

    def known_actions(self, p):
        return np.where(self.N[p[0], p[1]] > 0)[0]

    def imagine(self, p, a, rng):
        y, x = p
        n = self.N[y, x, a]
        died = rng.random() < self.Die[y, x, a] / n
        cnt = self.T[y, x, a]
        if cnt.sum() == 0:
            return p, self.B[y, x, a] / n, died
        d = ACTIONS[int(rng.choice(N_ACTIONS, p=cnt / cnt.sum()))]
        live = max(n - self.Die[y, x, a], 1)
        return (y + d[0], x + d[1]), self.B[y, x, a] / live, died


class Striatum:
    """Action values = place part + perceptual part, both learned, both
    indexed by the loudest need right now (hungry / thirsty / hurt / content).

    place part: one value per (place, need, action), a table over the
      cognitive map. Good for things that stay put (water, hazards, bushes).
    perceptual part: a linear readout of what I see right now (per need).
      Good for things that move (food): "food to my left and I'm hungry ->
      left is good" works anywhere.
    Dreams have no eyes, so they only train the place part.

    (Tried and dropped: one value map per drive, mixed by need strength.
    It learned worse in this world; see README.)"""

    def __init__(self, size, rng, n_view, alpha=0.2, alpha_view=0.05, gamma=0.95, epsilon=0.1):
        self.Q = np.zeros((size, size, N_CTX, N_ACTIONS))
        self.Wv = np.zeros((N_CTX, n_view, N_ACTIONS))
        self.rng = rng
        self.alpha, self.alpha_view = alpha, alpha_view
        self.gamma, self.epsilon = gamma, epsilon
        self.updates = 0

    def values(self, p, c, v=None):
        q = self.Q[p[0], p[1], c].copy() if p is not None else np.zeros(N_ACTIONS)
        if v is not None:
            q += v @ self.Wv[c] / max(v.sum(), 1.0)
        return q

    def act(self, p, c, v, allowed):
        if self.rng.random() < self.epsilon:
            return int(self.rng.choice(allowed))
        q = self.values(p, c, v)[allowed]
        ties = [a for a, qa in zip(allowed, q) if qa >= q.max() - 1e-9]
        return int(self.rng.choice(ties))

    def learn(self, p, c, a, r, p2, c2, done, v=None, v2=None):
        q = self.values(p, c, v)[a]
        target = r if done else r + self.gamma * self.values(p2, c2, v2).max()
        delta = target - q
        if p is not None:
            self.Q[p[0], p[1], c, a] += self.alpha * delta
        if v is not None:
            self.Wv[c, :, a] += self.alpha_view * delta * v
        self.updates += 1


def map_dream(model, striatum, starts, rng, n_updates, horizon=20, epsilon=0.2):
    """Imagined walks over the cognitive map. Each starts at a remembered
    place with an imagined body state. Returns how many imagined steps found
    something that made the body better."""
    done_updates, good = 0, 0
    while done_updates < n_updates:
        p = starts[int(rng.integers(len(starts)))]
        I = rng.uniform(0.15, 1.0, 3)  # imagine being hungry, thirsty, hurt, or fine
        for _ in range(horizon):
            allowed = model.known_actions(p)
            if len(allowed) == 0:
                break
            c = context(I)
            if rng.random() < epsilon:
                a = int(rng.choice(allowed))
            else:
                q = striatum.values(p, c)[allowed]
                a = int(allowed[int(rng.choice(np.flatnonzero(q >= q.max() - 1e-9)))])
            p2, dI, died = model.imagine(p, a, rng)
            I2 = np.clip(I + dI, 0.0, 1.0)
            died = died or (I2 <= 0).any()
            r = -5.0 if died else 10.0 * float(drive(I[None])[0] - drive(I2[None])[0])
            good += r > 0.5
            striatum.learn(p, c, a, r, p2, context(I2), died)
            done_updates += 1
            if died or done_updates >= n_updates:
                break
            p, I = p2, I2
    return good
