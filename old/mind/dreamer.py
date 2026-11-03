"""
The dreaming mind (v4): same brain as v3, but it decides with what it
has learned instead of with a planner I wrote.

What is the same: body and drives, eyes, hippocampal map and
self-location, self/other attribution, metacognition, global workspace,
language. The workspace still decides what it is conscious of and what
it reports.

What changed:
  - Action comes from a learned value of (inner state, body state),
    not from route search. The only innate behaviour left is the amygdala
    reflex (never step onto a visible hazard).
  - It has an imagination: a latent world model (mind/imagination.py).
  - Sleep can be (a) replay of real memories, (b) dreaming: practice
    inside its own world model, or (c) both. That choice is the
    experiment: does dreaming make it better at waking life?

The hippocampus still tells it where remembered food and water are
relative to itself (like goal-direction cells); how to use that is
learned.
"""
import numpy as np
from .agent import Mind
from .world import FOOD, WATER, N_ACTIONS
from .cortex import N_VIEW
from .subcortex import amygdala_veto
from .imagination import LatentWorldModel, Value, dream, drive
from .striatum import PlaceModel, Striatum, map_dream, context
from collections import deque

# place cells: Gaussian place fields tiling the agent's own map frame
PLACE_GRID = 16          # 16 x 16 fields
PLACE_SPACING = 2.0      # cells between field centres
PLACE_SIGMA = 1.3
N_PLACE = PLACE_GRID * PLACE_GRID
D_OBS = N_VIEW + 6 + N_PLACE


class Memory:
    """Chronological ring buffer of real transitions."""

    def __init__(self, cap=30000):
        self.cap, self.n, self.i = cap, 0, 0
        self.X = np.zeros((cap, D_OBS), np.float32)
        self.X2 = np.zeros((cap, D_OBS), np.float32)
        self.I = np.zeros((cap, 3))
        self.I2 = np.zeros((cap, 3))
        self.A = np.zeros(cap, np.int64)
        self.R = np.zeros(cap)
        self.D = np.zeros(cap)
        self.T = np.zeros(cap, np.int64)

    def add(self, X, I, a, r, X2, I2, done, t):
        j = self.i
        self.X[j], self.I[j], self.A[j], self.R[j] = X, I, a, r
        self.X2[j], self.I2[j], self.D[j], self.T[j] = X2, I2, done, t
        self.i = (self.i + 1) % self.cap
        self.n = min(self.n + 1, self.cap)

    def sample(self, rng, B):
        idx = rng.integers(0, self.n, B)
        return idx

    def nstep(self, j, n, gamma):
        """Discounted reward over up to n consecutive real steps from j.
        Returns (G, index of the last step used, discount for bootstrapping)."""
        G = np.zeros(len(j))
        disc = np.ones(len(j))
        last = j.copy()
        alive = np.ones(len(j), bool)
        for k in range(n):
            idx = (j + k) % self.cap
            ok = alive & (self.T[idx] == self.T[j] + k) & ((self.i - 1 - idx) % self.cap < self.n)
            if k > 0:
                ok &= idx != self.i  # never read past the newest entry
            G += np.where(ok, disc * self.R[idx], 0.0)
            last = np.where(ok, idx, last)
            disc = np.where(ok, disc * gamma, disc)
            alive = ok & (self.D[idx] == 0)
            disc = np.where(ok & (self.D[idx] == 1), 0.0, disc)
        return G, last, disc


def innate_reflex(view, intero):
    """Newborn animals are not blank slates. Two consummatory reflexes come
    built in (like suckling or swallowing): eat food that is right next to me
    when I'm hungry, keep drinking while I stand in water and I'm thirsty.
    *Where to go* to make these possible is entirely learned."""
    from .world import VIEW_R, ACTIONS
    if intero[1] < 0.9 and view[VIEW_R, VIEW_R] == WATER:
        return 0
    if intero[0] < 0.85:
        for a in range(1, N_ACTIONS):
            dy, dx = ACTIONS[a]
            if view[VIEW_R + dy, VIEW_R + dx] == FOOD:
                return a
    return None


class DreamingMind(Mind):
    """controller="map": place values over its own cognitive map (striatum),
    dreams walk through its learned place model. This is the one that works.
    controller="neural": a value network on the latent state, dreams run in
    the latent world model. Kept for the record: in this world it learns too
    slowly to be useful (see README, v4 findings)."""

    def __init__(self, seed=0, sleep_mode="dream", controller="map", **config):
        config = {**config}
        super().__init__(seed=seed, **config)
        self.controller = controller
        self.sleep_mode = sleep_mode
        # "awake_replay" / "awake_dream": never sleeps, but does a little offline
        # learning every waking tick (rats replay during quiet rest too). This
        # separates the *content* of offline learning from the cost of sleeping.
        self.awake_offline = sleep_mode.startswith("awake_")
        if sleep_mode == "none" or self.awake_offline:
            self.cfg["sleep"] = False
        self.relocalize_patience = 150  # it dies often while learning; don't throw the map away
        self.wm = LatentWorldModel(D_OBS, self.rng)
        self.value = Value(self.rng)
        self.mem = Memory()
        self.batch = 32
        self.dream_stats = []
        size = self.hippo.size
        self.place_model = PlaceModel(size)
        self.striatum = Striatum(size, self.rng, n_view=N_VIEW)
        self.real = deque(maxlen=30000)   # (p, c, a, r, p2, c2, done) for replay

    # ---------------------------------------------------------- perception
    def features(self, view):
        oh = np.zeros((25, 5))
        oh[np.arange(25), view.reshape(-1)] = 1.0
        mv = np.zeros(6)
        if self.cfg["hippocampus"] and not self.hippo.lost:
            py, px = self.hippo.pos
            for k, ttype in enumerate((FOOD, WATER)):
                known = self.hippo.known(ttype)
                if known:
                    d = [(abs(y - py) + abs(x - px), y - py, x - px) for y, x in known]
                    _, dy, dx = min(d)
                    mv[3 * k:3 * k + 3] = (np.clip(dy / 10, -1, 1), np.clip(dx / 10, -1, 1), 1.0)
        pc = np.zeros(N_PLACE)
        if self.cfg["hippocampus"] and not self.hippo.lost:
            # place cells fire for where I believe I am (centred on where my map began)
            py, px = self.hippo.pos
            c0 = self.hippo.size // 2 - PLACE_SPACING * (PLACE_GRID - 1) / 2
            cy = c0 + PLACE_SPACING * np.arange(PLACE_GRID)
            gy = np.exp(-((py - cy) ** 2) / (2 * PLACE_SIGMA ** 2))
            gx = np.exp(-((px - cy) ** 2) / (2 * PLACE_SIGMA ** 2))
            pc = np.outer(gy, gx).reshape(-1)
        return np.concatenate([oh.reshape(-1), mv, pc])

    # -------------------------------------------------------------- acting
    def choose_action(self, view, intero, needs):
        X = self.features(view)
        self._ctx["X"] = X
        if self.controller == "map":
            return self._choose_map(view, intero), None
        z = self.wm.encode(X[None])
        q = self.value.values(z, intero[None])[0]
        eps = max(0.05, 0.4 * (1 - self.t / 3000))
        order = list(np.argsort(-q))
        if self.rng.random() < eps:
            order = list(self.rng.permutation(N_ACTIONS))
        for a in order:
            if not amygdala_veto(view, int(a)):
                return int(a), None
        return 0, None

    def _choose_map(self, view, intero):
        allowed = [a for a in range(N_ACTIONS) if not amygdala_veto(view, a)]
        reflex = innate_reflex(view, intero)
        self._ctx["reflex"] = reflex
        known = not self.hippo.lost and self.cfg["hippocampus"]
        p = tuple(int(v) for v in self.hippo.pos) if known else None
        v = self._ctx["X"][:N_VIEW]
        self._ctx["p"], self._ctx["c"], self._ctx["v"] = p, context(intero), v
        if reflex is not None:
            return reflex
        return self.striatum.act(p, self._ctx["c"], v, allowed)

    # ---------------------------------------------------------- experience
    def experience(self, next_view, next_intero, died):
        c = self._ctx
        last = super().experience(next_view, next_intero, died)
        if "X" not in c:
            # Asleep: that "stay" was not a choice, and its slower drain would
            # teach the value system that standing still is good. Not stored.
            if self.controller == "neural" and self.mem.n >= 2 * self.batch:
                self._learn_real(self.batch)
            return last
        X2 = self.features(next_view)
        I, I2 = c["intero"], next_intero
        r = -5.0 if died else 10.0 * float(drive(I[None])[0] - drive(I2[None])[0])
        self.mem.add(c["X"], I, c["a"], r, X2, I2, float(died), self.t)
        if self.controller == "map":
            p = c.get("p")
            p2 = None if (died or self.hippo.lost) else tuple(int(v) for v in self.hippo.pos)
            c2, v2 = context(I2), X2[:N_VIEW]
            if p is not None and p2 is not None:
                self.place_model.observe(p, c["a"], p2, I2 - I, died)
            elif p is not None and died:
                self.place_model.observe(p, c["a"], p, I2 - I, died)
            tr = (p, c["c"], c["a"], r, p2, c2, died, c["v"], v2)
            self.striatum.learn(*tr)
            self.real.append(tr)
            if self.awake_offline:
                self._offline_map(8, self.sleep_mode[6:])
            if self.mem.n >= 2 * self.batch:
                self._train_wm(1)
        elif self.mem.n >= 2 * self.batch:
            self._learn_real(self.batch)
            self._train_wm(1)
        return last

    def _train_wm(self, n):
        for _ in range(n):
            j = self.mem.sample(self.rng, self.batch)
            m = self.mem
            ok = m.D[j] == 0
            j = j[ok]
            if len(j) > 4:
                self.wm.train(m.X[j], m.A[j], m.X2[j], m.I2[j] - m.I[j])

    def _learn_real(self, B, n=8):
        m = self.mem
        j = m.sample(self.rng, B)
        G, last, disc = m.nstep(j, n, self.value.gamma)
        z = self.wm.encode(m.X[j])
        z2 = self.wm.encode(m.X2[last])
        self.value.train(z, m.I[j], m.A[j], G, z2, m.I2[last], disc)

    def _learn_dream(self, n_starts):
        m = self.mem
        j = m.sample(self.rng, n_starts)
        z, I, a, r, z2, I2, d = dream(self.wm, self.value, m.X[j], m.I[j], self.rng)
        perm = self.rng.permutation(len(z))
        for k in range(0, len(z), self.batch):
            b = perm[k:k + self.batch]
            self.value.train(z[b], I[b], a[b], r[b], z2[b], I2[b], d[b])
        self.dream_stats.append({"t": self.t, "n": len(z), "reward": float(r.mean()),
                                 "eat_events": int((r > 1.0).sum())})

    def _offline_map(self, K, mode):
        """K value updates from real memories (replay), imagined walks over
        the place model (dream), or half of each (both)."""
        n_real = {"replay": K, "dream": 0, "both": K // 2}[mode]
        for _ in range(min(n_real, len(self.real))):
            self.striatum.learn(*self.real[int(self.rng.integers(len(self.real)))])
        n_dream = K - n_real
        if n_dream:
            starts = list({e[0] for e in list(self.real)[-3000:] if e[0] is not None})
            if starts:
                good = map_dream(self.place_model, self.striatum, starts, self.rng, n_dream)
                self.dream_stats.append({"t": self.t, "n": n_dream, "eat_events": int(good)})

    def _replay(self, n):
        """One tick of sleep. Every sleep mode gets the same world-model
        training and the same number of value updates; only the source of
        the experience differs (real memories vs imagined walks)."""
        super()._replay(6)            # v3 pixel predictor + metacognition
        if self.mem.n < 2 * self.batch:
            return
        self._train_wm(2)
        if self.controller == "map":
            self._offline_map(256, self.sleep_mode)
            return
        if self.sleep_mode == "replay":
            for _ in range(8):
                self._learn_real(self.batch)
        elif self.sleep_mode == "dream":
            self._learn_dream(self.batch)          # 32 starts x 8 steps = 8 batches
        elif self.sleep_mode == "both":
            for _ in range(4):
                self._learn_real(self.batch)
            self._learn_dream(self.batch // 2)


def imagination_accuracy(mind, k_max=10, n=300, recent=1500):
    """How far ahead can it imagine? Start from real recent moments, roll the
    world model forward with the actions it actually took, and compare with
    what actually happened.
    latent: normalized error vs the encoding of the real future (0 = perfect,
            1 = no better than guessing the average inner state)
    body:   R^2 of predicted vs real cumulative change in energy+hydration"""
    m, rng = mind.mem, np.random.default_rng(0)
    idx_all = (m.i - 1 - np.arange(min(recent, m.n))) % m.cap
    starts = []
    for s in rng.permutation(idx_all):
        seq = [(s + k) % m.cap for k in range(k_max)]
        if all(m.T[q] == m.T[s] + k for k, q in enumerate(seq)) and m.D[seq].sum() == 0:
            starts.append(seq)
        if len(starts) >= n:
            break
    if len(starts) < 20:
        return None
    S = np.array(starts)
    wm = mind.wm
    z = wm.encode(m.X[S[:, 0]])
    zvar = ((wm.encode(m.X[S].reshape(-1, D_OBS)) - z.mean(0)) ** 2).sum(1).mean()
    cum_pred = np.zeros((len(S), 2))
    cum_real = np.zeros((len(S), 2))
    lat, body = [], []
    for k in range(k_max):
        z, dI = wm.imagine(z, m.A[S[:, k]])
        cum_pred += dI[:, :2]
        cum_real += (m.I2[S[:, k]] - m.I[S[:, k]])[:, :2]
        zreal = wm.encode(m.X2[S[:, k]])
        lat.append(float(((z - zreal) ** 2).sum(1).mean() / zvar))
        ss_res = ((cum_pred - cum_real) ** 2).sum()
        ss_tot = ((cum_real - cum_real.mean(0)) ** 2).sum()
        body.append(float(1 - ss_res / ss_tot) if ss_tot > 1e-12 else float("nan"))
    return {"latent_error": lat, "body_r2": body}
