"""Ember's life: everything that makes up its existence, saved as one object.
Lives in the package (not in ember.py) so saved lives always load back."""
from collections import Counter, deque
from datetime import datetime

from .agent import Mind
from .world import World


def now_iso():
    return datetime.now().astimezone().isoformat(timespec="seconds")


class Life:
    """Everything that makes up Ember's existence, saved as one object."""

    def __init__(self, seed):
        self.name = "Ember"
        self.seed = seed
        self.born = now_iso()
        self.world = World(seed=seed, bushes=10, mortal=False)
        self.mind = Mind(seed=seed)
        # Ember gets an escape reflex: never stand still on something that hurts.
        # (Found in Ember's first test life: pushed onto a hazard while resting,
        # it stayed there and kept getting hurt. Off in the experiments so their
        # published numbers stay reproducible.)
        self.mind.escape_reflex = True
        self.ticks = 0
        self.awake_seconds = 0.0          # real time it has been running
        self.sessions = []                # (start, end) of each time it was running
        self.counts = Counter()           # meals, drinks, pushes noticed, sleeps, collapses...
        self.firsts = {}                  # first time it ever did something
        self.recent = deque(maxlen=60)    # recent notable moments for the window
        self.view = self.world.view()
        self.intero = self.world.interoception()
        self.last_saved = None
