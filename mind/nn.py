"""
Minimal neural network kit in numpy: dense layers, tanh, batch backprop, Adam.

Kept dependency-free on purpose so the mind runs on any laptop. Each MLP
caches its activations on forward() and returns the input gradient on
backward(), so networks can be chained (encoder -> predictor) and the
gradient can flow back through both.
"""
import numpy as np


class MLP:
    def __init__(self, sizes, rng, out_scale=1.0, lr=1e-3, act_last=False):
        self.W, self.b = [], []
        for i, (n_in, n_out) in enumerate(zip(sizes[:-1], sizes[1:])):
            scale = np.sqrt(1.0 / n_in) * (out_scale if i == len(sizes) - 2 else 1.0)
            self.W.append(rng.normal(0, scale, (n_in, n_out)))
            self.b.append(np.zeros(n_out))
        self.act_last = act_last
        self.lr = lr
        self.m = [np.zeros_like(p) for p in self.params()]
        self.v = [np.zeros_like(p) for p in self.params()]
        self.t = 0
        self.grads = [np.zeros_like(p) for p in self.params()]

    def params(self):
        return self.W + self.b

    def forward(self, X, cache=True):
        acts = [X]
        h = X
        n = len(self.W)
        for i in range(n):
            h = h @ self.W[i] + self.b[i]
            if i < n - 1 or self.act_last:
                h = np.tanh(h)
            acts.append(h)
        if cache:
            self._acts = acts
        return h

    def backward(self, dY):
        """Accumulate parameter grads; return grad w.r.t. the input."""
        acts = self._acts
        n = len(self.W)
        g = dY
        gW, gb = [None] * n, [None] * n
        for i in reversed(range(n)):
            if i < n - 1 or self.act_last:
                g = g * (1 - acts[i + 1] ** 2)
            gW[i] = acts[i].T @ g
            gb[i] = g.sum(axis=0)
            g = g @ self.W[i].T
        for k, gr in enumerate(gW + gb):
            self.grads[k] += gr
        return g

    def step(self, clip=5.0):
        self.t += 1
        b1, b2 = 0.9, 0.999
        for p, g, m, v in zip(self.params(), self.grads, self.m, self.v):
            norm = np.linalg.norm(g)
            if norm > clip:
                g *= clip / norm
            m *= b1
            m += (1 - b1) * g
            v *= b2
            v += (1 - b2) * g * g
            p -= self.lr * (m / (1 - b1 ** self.t)) / (np.sqrt(v / (1 - b2 ** self.t)) + 1e-8)
            g[...] = 0.0

    def copy_from(self, other, tau=1.0):
        """Polyak/EMA update toward another network of the same shape."""
        for p, q in zip(self.params(), other.params()):
            p *= (1 - tau)
            p += tau * q
