"""
A simulated you, for trials.py: the light that appears now and then near
Ember and leaves food in it. The real you does this from the window
(ember.py); this lets many copies of Ember meet the same kind of visitor.

Every `every` moments (first visit at a random moment) it appears as a light
on a free cell 1-2 cells from Ember, inside its sight (it sees only 2 cells
around itself), leaves food in it, and goes away `stay` moments later. Its
luck comes from its own seed, so paired versions meet the same visits.
"""
import numpy as np

from .wideworld import EMPTY


class Visitor:
    def __init__(self, seed, every=600, stay=150):
        self.reseed(seed)
        self.every, self.stay = every, stay
        self.next_at = self.leave_at = None
        self.visits = 0
        self.reached = 0              # visits where Ember stepped into the light
        self._reached_this = False

    def reseed(self, seed):
        self.rng = np.random.default_rng([int(seed), 77])

    def act(self, life):
        """One moment of the visitor. Returns True if it changed the world."""
        w = life.world
        light = getattr(w, "light", None)
        if self.next_at is None:
            self.next_at = w.t + int(self.rng.integers(1, self.every))
        if light is not None and not self._reached_this and tuple(w.pos) == light:
            self.reached += 1
            self._reached_this = True
        if light is not None and self.leave_at is not None and w.t >= self.leave_at:
            w.clear_light()
            self.leave_at = None
            return True
        if light is None and w.t >= self.next_at and not w.collapsed:
            self.next_at = w.t + self.every
            y, x = (int(v) for v in w.pos)
            cells = [(y + dy, x + dx) for dy in range(-2, 3) for dx in range(-2, 3)
                     if (dy or dx) and 0 <= y + dy < w.H and 0 <= x + dx < w.W and w.grid[y + dy, x + dx] == EMPTY]
            if not cells:
                return False
            if w.place_light(cells[int(self.rng.integers(len(cells)))]) is None:
                return False
            w.give()
            self.visits += 1
            self._reached_this = False
            self.leave_at = w.t + self.stay
            return True
        return False
