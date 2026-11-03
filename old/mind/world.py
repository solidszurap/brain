"""
The environment and the body.

A mind needs something to be *about*. This is a small grid world with
static walls, hazards and water, plus food that is eaten and regrows.
The agent has a body with three homeostatic variables (energy,
hydration, integrity) that drift away from their setpoints, so doing
nothing is fatal. Occasionally the world pushes the agent ("wind"):
the agent did not cause that movement, and a mind with a self-model
should be able to tell.

The agent never sees its true position. It only receives:
  - an egocentric 5x5 view of cell types
  - interoception (its own body variables)
Everything else (where it is, what is where) it must build itself.
"""
import numpy as np

EMPTY, WALL, FOOD, WATER, HAZARD = 0, 1, 2, 3, 4
N_TYPES = 5
TYPE_NAMES = ["empty", "wall", "food", "water", "hazard"]

# action 0 = stay, 1..4 = N, S, W, E   (dy, dx)
ACTIONS = [(0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)]
ACTION_NAMES = ["stay", "north", "south", "west", "east"]
N_ACTIONS = len(ACTIONS)

VIEW_R = 2
VIEW = 2 * VIEW_R + 1

LAYOUT = [
    "################",
    "#..............#",
    "#..~~....##....#",
    "#..~~....##..x.#",
    "#..............#",
    "#.###......x...#",
    "#.#............#",
    "#.#...xx...###.#",
    "#..........#...#",
    "#....##....#.~.#",
    "#....##......~.#",
    "#..x...........#",
    "#.......###....#",
    "#.~~.....#...x.#",
    "#........#.....#",
    "################",
]
CHAR = {"#": WALL, ".": EMPTY, "~": WATER, "x": HAZARD}


class World:
    def __init__(self, seed=0, wind_prob=0.06, n_food=7, drain=1.0, bushes=0, mortal=True):
        self.rng = np.random.default_rng(seed)
        self.grid = np.array([[CHAR[c] for c in row] for row in LAYOUT], dtype=np.int8)
        self.H, self.W = self.grid.shape
        self.wind_prob = wind_prob
        self.n_food = n_food
        self.drain = drain
        # mortal=False (Ember's one life): running out of a need does not kill
        # and teleport; the body collapses where it is, stays unconscious for a
        # while, then comes round weak. Memory and place are kept.
        self.mortal = mortal
        self.collapsed = 0
        self.collapses = 0
        # bushes > 0: food only regrows at that many fixed places (like fruit
        # bushes); otherwise it pops up anywhere at random
        self.bush_sites = []
        while len(self.bush_sites) < bushes:
            site = self._random_empty()
            if site not in self.bush_sites:
                self.bush_sites.append(site)
        for _ in range(n_food):
            self._spawn_food()
        self.pos = self._random_empty()
        self.body = {"energy": 0.8, "hydration": 0.8, "integrity": 1.0}
        self.t = 0
        self.deaths = 0

    # ---------------------------------------------------------------- utils
    def _random_empty(self):
        while True:
            y, x = self.rng.integers(1, self.H - 1), self.rng.integers(1, self.W - 1)
            if self.grid[y, x] == EMPTY:
                return (int(y), int(x))

    def _spawn_food(self):
        if self.bush_sites:
            free = [p for p in self.bush_sites if self.grid[p] == EMPTY and p != getattr(self, "pos", None)]
            if free:
                self.grid[free[int(self.rng.integers(len(free)))]] = FOOD
            return
        y, x = self._random_empty()
        self.grid[y, x] = FOOD

    def passable(self, y, x):
        return 0 <= y < self.H and 0 <= x < self.W and self.grid[y, x] != WALL

    def view(self):
        y0, x0 = self.pos
        v = np.full((VIEW, VIEW), WALL, dtype=np.int8)
        for dy in range(-VIEW_R, VIEW_R + 1):
            for dx in range(-VIEW_R, VIEW_R + 1):
                y, x = y0 + dy, x0 + dx
                if 0 <= y < self.H and 0 <= x < self.W:
                    v[dy + VIEW_R, dx + VIEW_R] = self.grid[y, x]
        return v

    def interoception(self):
        return np.array([self.body["energy"], self.body["hydration"], self.body["integrity"]])

    # ----------------------------------------------------------------- step
    COLLAPSE_TICKS = 60

    def step(self, action, sleeping=False):
        """Apply the agent's action, then physics. Returns an info dict
        with ground truth that the agent never sees (used for scoring)."""
        self.t += 1
        if self.collapsed:
            # unconscious: no action, no drain, the world goes on around it
            self.collapsed -= 1
            if (self.grid == FOOD).sum() < self.n_food and self.rng.random() < 0.05:
                self._spawn_food()
            woke = self.collapsed == 0
            if woke:
                for k in self.body:
                    self.body[k] = max(self.body[k], 0.3)
            return {"pushed": False, "consumed": None, "died": False, "true_pos": self.pos,
                    "collapsed": True, "came_round": woke}
        dy, dx = ACTIONS[action]
        ny, nx = self.pos[0] + dy, self.pos[1] + dx
        if self.passable(ny, nx):
            self.pos = (ny, nx)

        # the world acts on the agent
        pushed = False
        if self.rng.random() < self.wind_prob:
            wdy, wdx = ACTIONS[int(self.rng.integers(1, 5))]
            py, px = self.pos[0] + wdy, self.pos[1] + wdx
            if self.passable(py, px):
                self.pos = (py, px)
                pushed = True

        b = self.body
        rate = (0.5 if sleeping else 1.0) * self.drain
        b["energy"] -= rate * (0.004 + (0.002 if action else 0.0))
        b["hydration"] -= rate * 0.006

        cell = self.grid[self.pos]
        consumed = None
        if cell == FOOD:
            b["energy"] = min(1.0, b["energy"] + 0.35)
            self.grid[self.pos] = EMPTY
            consumed = "food"
        elif cell == WATER:
            if b["hydration"] < 0.95:
                consumed = "water"
            b["hydration"] = min(1.0, b["hydration"] + 0.08)
        elif cell == HAZARD:
            b["integrity"] -= 0.15
            consumed = "hazard"
        if b["energy"] > 0.4 and b["hydration"] > 0.4:
            b["integrity"] = min(1.0, b["integrity"] + 0.004)

        if (self.grid == FOOD).sum() < self.n_food and self.rng.random() < 0.05:
            self._spawn_food()

        died = min(b.values()) <= 0.0
        if died and not self.mortal:
            for k in b:
                b[k] = max(b[k], 0.0)
            self.collapsed = self.COLLAPSE_TICKS
            self.collapses += 1
            return {"pushed": pushed, "consumed": consumed, "died": False, "true_pos": self.pos,
                    "collapsed": True, "collapse_started": True}
        if died:
            self.deaths += 1
            self.body = {"energy": 0.8, "hydration": 0.8, "integrity": 1.0}
            self.pos = self._random_empty()

        return {"pushed": pushed, "consumed": consumed, "died": died, "true_pos": self.pos}
