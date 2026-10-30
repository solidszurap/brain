"""
Growing an existing mind without erasing it.

Used once, when Ember's valley opened into the wide world:

  expand_senses       its eyes can now tell apart 9 kinds of things instead
                      of 5. Every learned connection for the old 5 is kept
                      exactly; the new kinds start with no connections and a
                      low prior (new things are surprising at first).
  resize_hippocampus  its map grows from 48 x 48 to 96 x 96 cells. What it
                      knows is moved into the middle; the rest is unknown.
                      Every memory that refers to a place is shifted with it.
"""
import numpy as np

from .cortex import WorldModel, N_CELLS, N_INTERO, Adam
from .world import N_ACTIONS


def _index_map(n_old, n_new):
    """Old flat index (cell * n_old + kind, then interoception) -> new index."""
    view = [c * n_new + k for c in range(N_CELLS) for k in range(n_old)]
    intero = [N_CELLS * n_new + i for i in range(N_INTERO)]
    return np.array(view + intero)


def expand_senses(mind, n_new):
    old = mind.cortex
    n_old = old.n_types
    if n_new <= n_old:
        return
    A, _, H = old.W1.shape
    new = WorldModel(np.random.default_rng(12345), n_hidden=H, lr=old.opt.lr, n_types=n_new)
    imap = _index_map(n_old, n_new)               # inputs and outputs share the layout
    new.W1[:, imap, :] = old.W1
    new.b1[:] = old.b1
    new.W2[:] = 0.0
    new.W2[:, :, imap] = old.W2
    new.b2[:] = 0.0
    new_view_logits = np.array([c * n_new + k for c in range(N_CELLS) for k in range(n_old, n_new)])
    new.b2[:, new_view_logits] = -3.0              # new kinds: rare until seen
    new.b2[:, imap] = old.b2
    new.S[:] = 0.0
    new.S[:, imap[:, None], imap[None, :]] = old.S
    new.opt = Adam([p.shape for p in new.params], lr=old.opt.lr)
    new.opt.t = old.opt.t
    for i, (m_old, v_old) in enumerate(zip(old.opt.m, old.opt.v)):
        if i == 0:
            new.opt.m[0][:, imap, :], new.opt.v[0][:, imap, :] = m_old, v_old
        elif i == 1:
            new.opt.m[1][:], new.opt.v[1][:] = m_old, v_old
        elif i == 2:
            new.opt.m[2][:, :, imap], new.opt.v[2][:, :, imap] = m_old, v_old
        elif i == 3:
            new.opt.m[3][:, imap], new.opt.v[3][:, imap] = m_old, v_old
        else:
            new.opt.m[4][:, imap[:, None], imap[None, :]] = m_old
            new.opt.v[4][:, imap[:, None], imap[None, :]] = v_old
    new.updates = old.updates
    mind.cortex = new

    # metacognition reads the same sensory vector
    w_old = mind.meta.w
    n_in_old = len(imap)
    w_new = np.zeros(new.n_in + N_ACTIONS + 1)
    w_new[imap] = w_old[:n_in_old]
    w_new[new.n_in:] = w_old[n_in_old:]
    mind.meta.w = w_new

    # episodic memories store what it saw in the old format: translate them
    for e in mind.hippo.episodes:
        x = np.zeros(new.n_in)
        x[imap] = e["x"]
        e["x"] = x


def resize_hippocampus(mind, new_size):
    hp = mind.hippo
    old = hp.size
    if new_size <= old:
        return (0, 0)
    pad = (new_size - old) // 2

    def grow(a, fill):
        b = np.full((new_size, new_size), fill, dtype=a.dtype)
        b[pad:pad + old, pad:pad + old] = a
        return b

    hp.map = grow(hp.map, -1)
    hp.seen = grow(hp.seen, 0)
    hp.last_seen = grow(hp.last_seen, 0)
    if getattr(hp, "volatile", None) is not None:
        hp.volatile = grow(hp.volatile, False)
    hp.size = new_size
    hp.pos = (hp.pos[0] + pad, hp.pos[1] + pad)

    def shift(s):
        return (s[0] + pad, s[1] + pad) + tuple(s[2:]) if isinstance(s, tuple) else s

    for e in hp.episodes:
        e["s"], e["s2"] = shift(e["s"]), shift(e["s2"])
    mind.bg.Q = {shift(k): v for k, v in mind.bg.Q.items()}
    mind.pfc.plan = []
    mind._ctx = {}
    return (pad, pad)
