"""Small online learners. Pure Python, no dependencies."""


class NLMS:
    """Normalized least-mean-squares linear predictor (online)."""

    def __init__(self, n, mu=0.1, eps=1e-6, w=None):
        self.w = list(w) if w is not None else [0.0] * n
        self.mu = mu
        self.eps = eps

    def predict(self, x):
        return sum(a * b for a, b in zip(self.w, x))

    def update(self, x, y, mu=None):
        e = y - self.predict(x)
        m = self.mu if mu is None else mu
        norm = self.eps + sum(v * v for v in x)
        for i, v in enumerate(x):
            self.w[i] += m * e * v / norm
        return e


class EMA:
    def __init__(self, alpha, value=0.0, init=False):
        self.alpha, self.value, self.init = alpha, value, init

    def update(self, x):
        if not self.init:
            self.value, self.init = x, True
        else:
            self.value += self.alpha * (x - self.value)
        return self.value

    def state(self):
        return {"value": self.value, "init": self.init}

    @classmethod
    def from_state(cls, alpha, s):
        return cls(alpha, s["value"], s["init"])
