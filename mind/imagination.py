"""
Imagination: a latent world model, a learned sense of value, and dreaming.

Idea 2 (world models, LeCun / JEPA):
  The mind does not predict the next *pixels*. An encoder turns what it
  senses into a compact inner state z, and a predictor learns how z
  changes when it acts. The training target is the encoding of the next
  moment (from a slowly-updated copy of the encoder, so the target does
  not chase itself), and a variance/covariance penalty keeps the inner
  states from collapsing to a constant. A second head predicts what will
  happen to its own body (interoception), which ties the inner state to
  what matters to it.

Idea 3 (learning from experience, Sutton / Silver):
  Nobody tells it what to do. Value is learned from its own life:
  reward is its body getting better (drive reduction), and the value
  network learns which inner states and actions lead there.

Where they meet: dreaming.
  During sleep the mind starts from real remembered moments and lets its
  world model run forward, choosing actions and feeling the imagined
  consequences in its imagined body. It learns from these dreams exactly
  as it learns from real life. If its world model is good, dreams are
  free practice. If it is bad, dreams teach the wrong lessons.
"""
import numpy as np
from .nn import MLP
from .world import N_ACTIONS

Z = 32
NEED_W = np.array([1.0, 1.0, 1.4])
SETPOINT = 0.9


def drive(I):
    """Vectorized homeostatic drive for a batch of body states (B, 3)."""
    n = np.clip((SETPOINT - I) / SETPOINT, 0.0, 1.0)
    return (NEED_W * n ** 2).sum(axis=-1)


def onehot(a, n=N_ACTIONS):
    o = np.zeros((len(a), n))
    o[np.arange(len(a)), a] = 1.0
    return o


class LatentWorldModel:
    def __init__(self, d_obs, rng, lr=1e-3):
        self.enc = MLP([d_obs, 96, Z], rng, lr=lr, act_last=True)
        self.target = MLP([d_obs, 96, Z], rng, act_last=True)
        self.target.copy_from(self.enc)
        self.trans = MLP([Z + N_ACTIONS, 96, Z], rng, out_scale=0.1, lr=lr)
        self.body = MLP([Z + N_ACTIONS, 64, 3], rng, out_scale=0.1, lr=lr)
        self.losses = {"pred": [], "body": [], "std": []}

    def encode(self, X):
        return self.enc.forward(X, cache=False)

    def imagine(self, z, a):
        """One step of imagination: next inner state, predicted body change."""
        za = np.concatenate([z, onehot(a)], axis=1)
        z2 = z + self.trans.forward(za, cache=False)
        dI = self.body.forward(za, cache=False) / 10.0
        return z2, dI

    def train(self, X, A, X2, dI, w_var=1.0, w_cov=0.04, gamma=0.5):
        B = len(X)
        z = self.enc.forward(X)
        za = np.concatenate([z, onehot(A)], axis=1)
        zhat = z + self.trans.forward(za)
        zt = self.target.forward(X2, cache=False)
        bh = self.body.forward(za)

        d_zhat = 2 * (zhat - zt) / (B * Z)
        d_za_t = self.trans.backward(d_zhat)
        d_bh = 2 * (bh - 10 * dI) / (B * 3)
        d_za_b = self.body.backward(d_bh)
        dz = d_zhat + d_za_t[:, :Z] + d_za_b[:, :Z]

        # keep inner states informative: each dimension must vary (variance),
        # and dimensions should not duplicate each other (covariance)
        zc = z - z.mean(axis=0)
        std = np.sqrt(zc.var(axis=0) + 1e-4)
        low = std < gamma
        dz += w_var * (-(low / Z) * zc / (B * std))
        C = zc.T @ zc / (B - 1)
        np.fill_diagonal(C, 0.0)
        dz += w_cov * (4.0 / (Z * (B - 1))) * zc @ C

        self.enc.backward(dz)
        for net in (self.enc, self.trans, self.body):
            net.step()
        self.target.copy_from(self.enc, tau=0.01)

        self.losses["pred"].append(float(((zhat - zt) ** 2).mean()))
        self.losses["body"].append(float(((bh / 10 - dI) ** 2).mean()))
        self.losses["std"].append(float(std.mean()))


class Value:
    """Learned value of acting, from inner state + body state."""

    def __init__(self, rng, gamma=0.9, lr=1e-3):
        self.q = MLP([Z + 3, 96, N_ACTIONS], rng, out_scale=0.1, lr=lr)
        self.q_t = MLP([Z + 3, 96, N_ACTIONS], rng)
        self.q_t.copy_from(self.q)
        self.gamma = gamma
        self.td = []

    def values(self, z, I):
        return self.q.forward(np.concatenate([z, I], axis=1), cache=False)

    def bootstrap(self, z2, I2):
        """Value of the state reached, judged by the slow target network
        (double-Q: the online net picks the action, the target net scores it)."""
        nxt = self.q_t.forward(np.concatenate([z2, I2], axis=1), cache=False)
        a2 = self.values(z2, I2).argmax(axis=1)
        return nxt[np.arange(len(z2)), a2]

    def train(self, z, I, a, G, z2, I2, disc):
        """n-step TD: target = G (discounted reward sum) + disc * value(z2)."""
        B = len(z)
        y = G + disc * self.bootstrap(z2, I2)
        q = self.q.forward(np.concatenate([z, I], axis=1))
        err = q[np.arange(B), a] - y
        g = np.zeros_like(q)
        g[np.arange(B), a] = np.clip(err, -1, 1) / B  # Huber
        self.q.backward(g)
        self.q.step()
        self.q_t.copy_from(self.q, tau=0.01)
        self.td.append(float(np.abs(err).mean()))


def dream(wm, value, X0, I0, rng, horizon=8, epsilon=0.3):
    """Imagined rollouts from real remembered moments.

    Returns training tuples for every imagined step: the return from that
    step to the end of the dream, bootstrapped with the value of the final
    imagined state (n-step targets along the dream, as in Dreamer)."""
    gamma = value.gamma
    z = wm.encode(X0)
    I = I0.copy()
    B = len(z)
    Zs, Is, As, Rs, alive_k = [], [], [], [], []
    alive = np.ones(B, bool)
    for _ in range(horizon):
        q = value.values(z, I)
        a = q.argmax(axis=1)
        explore = rng.random(B) < epsilon
        a[explore] = rng.integers(0, N_ACTIONS, explore.sum())
        z2, dI = wm.imagine(z, a)
        I2 = np.clip(I + dI, 0.0, 1.0)
        r = 10.0 * (drive(I) - drive(I2))
        done = (I2 <= 0.0).any(axis=1)
        r = np.where(done, -5.0, r)
        Zs.append(z); Is.append(I); As.append(a); Rs.append(r * alive); alive_k.append(alive.copy())
        alive = alive & ~done
        z, I = z2, I2
    boot = value.bootstrap(z, I) * alive
    out_z, out_I, out_a, out_G, out_disc = [], [], [], [], []
    G = np.zeros(B)
    disc = np.ones(B)
    # walk backwards: G_k = r_k + gamma * G_{k+1}, final bootstrap folded in
    G = boot.copy()
    for k in reversed(range(horizon)):
        G = Rs[k] + gamma * G
        m = alive_k[k]
        out_z.append(Zs[k][m]); out_I.append(Is[k][m]); out_a.append(As[k][m]); out_G.append(G[m])
    zc = np.concatenate(out_z)
    return (zc, np.concatenate(out_I), np.concatenate(out_a), np.concatenate(out_G),
            zc, np.concatenate(out_I), np.zeros(len(zc)))
