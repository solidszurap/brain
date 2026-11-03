"""
Sensory cortex + predictive world model (cortex/cerebellum analogue).

The world model is a forward model: given what I see and feel now, and
the action I am about to take (the *efference copy*), what will I see
and feel next? It is learned online from experience, not given.

Its prediction error, measured as surprisal (-log p of what actually
happened), is the raw signal that the rest of the brain uses for
attention, self/other attribution, memory priority and sleep pressure.
"""
import numpy as np
from .world import N_TYPES, VIEW, N_ACTIONS

N_CELLS = VIEW * VIEW
N_VIEW = N_CELLS * N_TYPES
N_INTERO = 3
N_IN = N_VIEW + N_INTERO


def encode(view, intero, n_types=N_TYPES):
    """Sensory cortex: one-hot egocentric view + interoception.
    n_types: how many kinds of things its eyes can tell apart."""
    oh = np.zeros((N_CELLS, n_types))
    oh[np.arange(N_CELLS), view.reshape(-1)] = 1.0
    return np.concatenate([oh.reshape(-1), intero])


class Adam:
    def __init__(self, shapes, lr=2e-3, b1=0.9, b2=0.999):
        self.lr, self.b1, self.b2 = lr, b1, b2
        self.m = [np.zeros(s) for s in shapes]
        self.v = [np.zeros(s) for s in shapes]
        self.t = 0

    def step(self, params, grads, idx):
        """Update params[i][idx] slices (one action's weights)."""
        self.t += 1
        c1 = 1 - self.b1 ** self.t
        c2 = 1 - self.b2 ** self.t
        for p, g, m, v in zip(params, grads, self.m, self.v):
            m[idx] = self.b1 * m[idx] + (1 - self.b1) * g
            v[idx] = self.b2 * v[idx] + (1 - self.b2) * g * g
            p[idx] -= self.lr * (m[idx] / c1) / (np.sqrt(v[idx] / c2) + 1e-8)


class WorldModel:
    """Action-conditioned forward model: one small network per action,
    with a linear skip path (easy to learn 'the view shifts north') and a
    hidden layer (needed for 'unless a wall blocks me')."""

    # defaults for the original world (5 kinds of cell); a mind whose senses
    # were expanded (see mind/growth.py) carries its own values
    n_types, n_view, n_in = N_TYPES, N_VIEW, N_IN

    def __init__(self, rng, n_hidden=48, lr=2e-3, n_types=N_TYPES):
        A, H = N_ACTIONS, n_hidden
        self.n_types = n_types
        self.n_view = N_CELLS * n_types
        self.n_in = self.n_view + N_INTERO
        n_out = self.n_view + N_INTERO
        self.W1 = rng.normal(0, 1 / np.sqrt(self.n_in), (A, self.n_in, H))
        self.b1 = np.zeros((A, H))
        self.W2 = rng.normal(0, 0.1 / np.sqrt(H), (A, H, n_out))
        self.b2 = np.zeros((A, n_out))
        self.S = np.zeros((A, self.n_in, n_out))
        self.params = [self.W1, self.b1, self.W2, self.b2, self.S]
        self.opt = Adam([p.shape for p in self.params], lr=lr)
        self.updates = 0

    def _forward(self, x, a):
        h = np.tanh(x @ self.W1[a] + self.b1[a])
        out = h @ self.W2[a] + self.b2[a] + x @ self.S[a]
        logits = out[:self.n_view].reshape(N_CELLS, self.n_types)
        logits = logits - logits.max(axis=1, keepdims=True)
        p = np.exp(logits)
        p /= p.sum(axis=1, keepdims=True)
        return h, p, out[self.n_view:]

    def predict(self, x, a):
        """Returns (per-cell type probabilities, predicted body change)."""
        _, p, d = self._forward(x, a)
        return p, d / 100.0

    def surprisal(self, x, a, next_view):
        p, _ = self.predict(x, a)
        actual = next_view.reshape(-1)
        return float(-np.log(p[np.arange(N_CELLS), actual] + 1e-9).mean())

    def learn(self, x, a, next_view, intero_delta):
        h, p, d = self._forward(x, a)
        actual = next_view.reshape(-1)
        g_logits = p.copy()
        g_logits[np.arange(N_CELLS), actual] -= 1.0
        g_logits /= N_CELLS
        g_d = (d - intero_delta * 100.0) * 0.05
        g_out = np.concatenate([g_logits.reshape(-1), g_d])
        gW2 = np.outer(h, g_out)
        gb2 = g_out
        gS = np.outer(x, g_out)
        g_h = (self.W2[a] @ g_out) * (1 - h * h)
        gW1 = np.outer(x, g_h)
        gb1 = g_h
        self.opt.step(self.params, [gW1, gb1, gW2, gb2, gS], a)
        self.updates += 1
