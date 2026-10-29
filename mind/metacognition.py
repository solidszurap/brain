"""
Metacognition: a second-order model that predicts how wrong the
first-order world model is about to be.

This is the honest, measurable version of "knowing what you don't
know". It never sees the answer before predicting; it is scored on
calibration (does its expected surprise track actual surprise?).

Its most important output is the *residual*: surprise beyond what I
expected. A large residual means "something happened that my own
model of myself and the world did not account for", which is the
signal the self-model uses to decide "that was not me".
"""
from collections import deque

import numpy as np
from .cortex import N_IN
from .world import N_ACTIONS


class Metacognition:
    def __init__(self, lr=0.01, enabled=True):
        self.enabled = enabled
        self.w = np.zeros(N_IN + N_ACTIONS + 1)
        self.w[-1] = np.log(1.0)
        self.lr = lr
        self.resid_mean = 0.0
        self.resid_var = 1.0
        self.raw_mean = 1.0
        self.raw_var = 1.0
        self.history = deque(maxlen=5000)  # (expected, actual) pairs for calibration

    def _features(self, x, a):
        oh = np.zeros(N_ACTIONS)
        oh[a] = 1.0
        return np.concatenate([x, oh, [1.0]])

    def expect(self, x, a):
        """Expected log-surprisal of the next observation."""
        return float(self._features(x, a) @ self.w)

    def observe(self, x, a, surprisal, learn=True):
        """Returns z: how much more surprised I am than I expected to be."""
        ls = np.log(surprisal + 1e-6)
        if not self.enabled:
            # Without a second-order model, the best available signal is
            # raw surprise compared with its running average.
            z = (ls - self.raw_mean) / np.sqrt(self.raw_var + 1e-6)
            self.raw_mean += 0.02 * (ls - self.raw_mean)
            self.raw_var += 0.02 * ((ls - self.raw_mean) ** 2 - self.raw_var)
            self.history.append((self.raw_mean, ls))
            return float(z), float(self.raw_mean)
        f = self._features(x, a)
        exp = float(f @ self.w)
        r = ls - exp
        z = (r - self.resid_mean) / np.sqrt(self.resid_var + 1e-6)
        if learn:
            # robust update: do not let rare external events teach me
            # that I should always expect them
            r_clip = np.clip(r, -2.5 * np.sqrt(self.resid_var), 2.5 * np.sqrt(self.resid_var))
            self.w += self.lr * r_clip * f / (1 + f @ f * 0.01)
            self.resid_mean += 0.01 * (r - self.resid_mean)
            self.resid_var += 0.01 * (min(r * r, 9 * self.resid_var) - self.resid_var)
        self.history.append((exp, ls))
        return float(z), exp

    def calibration(self, last=1000):
        """Correlation between expected and actual log-surprisal."""
        h = np.array(list(self.history)[-last:])
        if len(h) < 50 or h[:, 0].std() < 1e-9:
            return 0.0
        return float(np.corrcoef(h[:, 0], h[:, 1])[0, 1])
