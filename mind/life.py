"""Ember's life: everything that makes up its existence, saved as one object.
Lives in the package (not in ember.py) so saved lives always load back.

Version 1: Ember in its 16 x 16 valley (born before the wide world existed).
Version 2: the valley is one region of the 40 x 40 wide world; the mind is an
           EmberMind (more senses, more ways to learn). A version-1 life is
           moved into version 2 by open_the_valley(), keeping every memory.
"""
from collections import Counter, deque
from datetime import datetime

import numpy as np

from .agent import Mind
from .world import World

VERSION = 2


def now_iso():
    return datetime.now().astimezone().isoformat(timespec="seconds")


class Life:
    """Everything that makes up Ember's existence, saved as one object."""

    def __init__(self, seed):
        from .wideworld import WideWorld
        from .ember_mind import EmberMind
        self.name = "Ember"
        self.seed = seed
        self.born = now_iso()
        self.version = VERSION
        self.world = WideWorld(seed=seed)
        self.mind = EmberMind.newborn(seed)
        self.valley_opened = {"tick": 0, "time": self.born}
        self.ticks = 0
        self.awake_seconds = 0.0          # real time it has been running
        self.sessions = []                # (start, end) of each time it was running
        self.counts = Counter()           # meals, drinks, pushes noticed, sleeps, collapses...
        self.firsts = {}                  # first time something entered its workspace
        self.recent = deque(maxlen=60)    # recent notable moments for the window
        self.view = self.world.view()
        self.intero = self.world.interoception()
        self.last_saved = None


def open_the_valley(life):
    """Move a version-1 life into the wide world. Nothing it knows is lost:
    its valley is copied in place, its map and every place-based memory are
    shifted to the bigger map, its senses are widened, and its mind gains the
    new capacities. Returns a short description of what changed."""
    from .wideworld import WideWorld, VALLEY_AT, N_TYPES_WIDE
    from .ember_mind import EmberMind, MAP_SIZE
    from .growth import expand_senses, resize_hippocampus

    if getattr(life, "version", 1) >= 2:
        return None
    m = life.mind
    old_world = life.world
    known_before = int((m.hippo.map >= 0).sum())
    believed_before = tuple(m.hippo.pos)
    true_before = tuple(old_world.pos)

    life.world = WideWorld(seed=life.seed, valley=old_world, mortal=False)
    # Its old world ended at the valley's border, and its eyes showed the edge
    # of the world as wall. That was never a real wall, and it is gone now:
    # forget what it "saw" beyond the edge (everything else is kept).
    ay, ax = true_before[0] - believed_before[0], true_before[1] - believed_before[1]   # true - believed
    ys, xs = np.mgrid[0:m.hippo.size, 0:m.hippo.size]
    outside = (ys + ay < 0) | (ys + ay >= old_world.H) | (xs + ax < 0) | (xs + ax >= old_world.W)
    forgotten = int((outside & (m.hippo.map >= 0)).sum())
    m.hippo.map[outside] = -1
    known_before -= forgotten
    pad = resize_hippocampus(m, MAP_SIZE)
    expand_senses(m, N_TYPES_WIDE)
    m.__class__ = EmberMind
    m.escape_reflex = True
    m.init_extras()
    if hasattr(life, "tracker"):
        # keep the self-knowledge measurements consistent: true - believed
        ay, ax = life.tracker.anchor
        life.tracker.anchor = (ay + VALLEY_AT[0] - pad[0], ax + VALLEY_AT[1] - pad[1])
    life.view = life.world.view()
    life.intero = life.world.interoception()
    life.version = 2
    life.valley_opened = {"tick": life.ticks, "time": now_iso()}
    known_after = int((m.hippo.map >= 0).sum())
    assert known_after == known_before, "map memories lost in migration"
    assert (true_before[0] + VALLEY_AT[0], true_before[1] + VALLEY_AT[1]) == tuple(life.world.pos)
    assert (believed_before[0] + pad[0], believed_before[1] + pad[1]) == tuple(m.hippo.pos)
    return (f"The valley opened into a wider world (40 x 40). Kept all {known_after} remembered places "
            f"(forgot the edge of its old world, which it had seen as wall), "
            f"{len(m.hippo.episodes)} episodes and its learned world model; its eyes now tell apart "
            f"{N_TYPES_WIDE} kinds of things.")


def grow_senses(mind):
    """Eyes for every kind of thing in the wide world. A mind from before the
    light existed tells apart 9 kinds; mind/growth.py adds the 10th, keeping
    everything it learned (as when the valley opened). Lazy, so every life
    (the real one, bank snapshots, copies) grows them before it can see a
    light. `old_senses` keeps the old eyes (a trials.py version; only safe
    in a world without a light)."""
    from .wideworld import N_TYPES_WIDE
    if mind.cortex.n_types < N_TYPES_WIDE and not getattr(mind, "old_senses", False):
        from .growth import expand_senses
        # a much lower prior than the valley's -3: with -3, its predictions gave a few
        # percent to a light it had never seen, and in hard moments it was wrong about
        # where it was more often (results/trials/2026-10-30_1432_old_senses_vs_baseline.md)
        expand_senses(mind, N_TYPES_WIDE, prior=-8.0)


def step_life(life):
    """One moment, without any bookkeeping: shared by Ember's real life and by
    the clone tests in mind/consciousness.py so both live by the same rules.
    Returns (world info, mind's last-moment record or None while unconscious)."""
    w, m = life.world, life.mind
    grow_senses(m)
    visitor = getattr(life, "visitor", None)       # a simulated you (trials); the real you acts from the window
    if visitor is not None and visitor.act(life):
        life.view = w.view()                       # it sees the change before it decides what to do
    if w.collapsed:
        info = w.step(0)
        life.view, life.intero = w.view(), w.interoception()
        if info.get("came_round"):
            m.drives.prev_drive = None    # coming round is not a reward for anything it did
            if hasattr(m, "on_came_round"):
                m.on_came_round(life.intero)
        return info, None
    a = m.decide(life.view, life.intero)
    info = w.step(a, sleeping=m.sleeping)
    life.view, life.intero = w.view(), w.interoception()
    if hasattr(m, "sense"):
        m.sense(info.get("sounds"), info.get("season"), info.get("felt_push"))
    last = m.experience(life.view, life.intero, False)
    return info, last
