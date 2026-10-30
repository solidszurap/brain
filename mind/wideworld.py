"""
The wide world: Ember's valley becomes one region of a 40 x 40 land.

Built so that a mind can't solve it once and stop learning:

  valley    Ember's original home, unchanged (its memories stay true).
            Four passes now lead out of it.
  plains    north. Open and windy, almost no landmarks: being pushed here
            is hard to notice. Summer bushes, one small pond.
  mirror    in the plains' north-west corner: a still pool. Beyond it, two
  pool      figures that look identical. One is Ember's reflection (it moves
            when Ember moves, mirrored); the other wanders on its own.
            Telling them apart is a contingency test for self-recognition.
  woods     west. Rows of trees with gaps. Bushes that fruit in autumn.
            A lever deep in the south-west.
  marsh     south. Ponds that dry out in summer and autumn. Bogs that hurt.
            Dark berries that look like food but make it sick.
  orchard   east, behind a gate. Food all year round, but no water, so it
            can't simply move in. The gate opens for a while when a lever is
            pulled (one far away in the woods, one inside). The gate makes a
            sound Ember can hear anywhere.

Seasons (3,000 moments each): spring, summer, autumn, winter. In winter food
grows only in the orchard: getting through winter needs the two-step plan
(open the gate, then eat).
"""
import numpy as np

from .world import LAYOUT, CHAR, EMPTY, WALL, FOOD, WATER, HAZARD, ACTIONS, VIEW_R, VIEW

DARK, GATE, LEVER, FIGURE = 5, 6, 7, 8
N_TYPES_WIDE = 9
TYPE_NAMES_WIDE = ["empty", "wall", "food", "water", "hazard", "dark berry", "gate", "lever", "figure"]
SEASONS = ["spring", "summer", "autumn", "winter"]
SEASON_LEN = 3000
SIZE = 40
VALLEY_AT = (12, 12)
GATE_OPEN_TIME = 300
MIRROR_POOL_ROW = 3
MIRROR_COLS = (2, 8)


def _layout():
    """The land, as cell types, plus where everything seasonal lives."""
    g = np.full((SIZE, SIZE), EMPTY, dtype=np.int8)
    g[0, :] = g[-1, :] = g[:, 0] = g[:, -1] = WALL
    vy, vx = VALLEY_AT
    for r, row in enumerate(LAYOUT):
        for c, ch in enumerate(row):
            g[vy + r, vx + c] = CHAR[ch]
    for p in [(12, 19), (12, 20), (17, 12), (18, 12), (27, 22), (27, 23), (15, 27), (16, 27)]:
        g[p] = EMPTY                                   # passes out of the valley

    # woods: rows of trees with staggered gaps
    for r in range(13, 38):
        if r % 4 == 1:
            gap = 2 + ((r // 4) % 3) * 3
            for c in range(1, 12):
                if abs(c - gap) > 1:
                    g[r, c] = WALL
    for p in [(15, 5), (19, 9), (23, 3), (27, 7), (31, 10), (35, 5)]:
        g[p] = WALL

    # plains: almost featureless, a few rocks
    # plains: sparse rocks (most views show one, many don't)
    for p in [(3, 14), (7, 21), (9, 31), (5, 36), (8, 12), (2, 26), (10, 18), (2, 11), (6, 16),
              (9, 24), (4, 22), (7, 28), (3, 33), (9, 37), (1, 30), (6, 4), (9, 8), (5, 26),
              (2, 36), (8, 34)]:
        g[p] = WALL
    for p in [(6, 33), (6, 34)]:
        g[p] = WATER                                   # small permanent pond
    for c in range(MIRROR_COLS[0], MIRROR_COLS[1] + 1):
        g[MIRROR_POOL_ROW, c] = WATER                  # the still pool

    # orchard: walled, one gate
    g[11, 29:39] = WALL
    g[28, 29:39] = WALL
    g[11:29, 29] = WALL
    gate = [(16, 29)]
    for p in gate:
        g[p] = GATE
    for p in [(15, 33), (24, 31)]:
        g[p] = WALL
    # (no water inside the orchard: Ember has to leave to drink, and come back)
    levers = [(36, 2), (17, 31)]
    for p in levers:
        g[p] = LEVER

    # marsh
    for p in [(30, 22), (33, 26), (36, 19), (37, 35), (31, 36)]:
        g[p] = HAZARD
    for p in [(34, 13), (30, 29), (33, 17), (37, 26), (32, 30), (29, 34), (35, 22), (31, 25), (37, 31)]:
        g[p] = WALL

    seasonal_ponds = [(31, 15), (31, 16), (32, 15), (32, 16), (35, 30), (35, 31), (36, 30), (36, 31)]
    bushes = []
    for p in [(2, 18), (9, 27), (4, 30)]:
        bushes.append((p, FOOD, {"summer"}, "plains"))
    for p in [(14, 3), (16, 8), (20, 5), (22, 9), (26, 2), (28, 7), (32, 4), (34, 9), (36, 6)]:
        bushes.append((p, FOOD, {"autumn"}, "woods"))
    for p in [(13, 32), (14, 36), (18, 34), (21, 31), (23, 36), (25, 33), (19, 37), (26, 30)]:
        bushes.append((p, FOOD, set(SEASONS), "orchard"))
    for p in [(30, 18), (33, 20), (36, 24), (32, 33), (35, 36), (37, 14)]:
        bushes.append((p, DARK, {"spring", "summer"}, "marsh"))
    for (p, _, _, _) in bushes:
        g[p] = EMPTY
    for p in seasonal_ponds:
        g[p] = WATER
    return g, bushes, seasonal_ponds, gate, levers


def region_of(pos):
    y, x = pos
    vy, vx = VALLEY_AT
    if vy <= y < vy + 16 and vx <= x < vx + 16:
        return "valley"
    if y <= 5 and x <= 9:
        return "mirror pool"
    if y <= 10:
        return "plains"
    if x <= 11:
        return "woods"
    if 29 <= x and 11 <= y <= 28:
        return "orchard"
    if y >= 28:
        return "marsh"
    return "corridor"


class WideWorld:
    def __init__(self, seed=7, valley=None, mortal=False):
        """valley: an existing small World whose terrain, food, bushes, body and
        position are carried over (Ember's home, as it left it)."""
        self.rng = np.random.default_rng(seed + 4242)
        self.grid, bushes, self.seasonal_ponds, self.gate_cells, self.levers = _layout()
        self.H = self.W = SIZE
        self.mortal = mortal
        self.t = 0
        self.deaths = 0
        self.collapsed = 0
        self.collapses = 0
        self.gate_timer = 0
        self.wind_plains, self.wind_elsewhere = 0.10, 0.05
        vy, vx = VALLEY_AT
        if valley is None:
            from .world import World
            valley = World(seed=seed, bushes=10, mortal=False)
        # carry the valley over exactly as it is (including food lying there now)
        self.grid[vy:vy + 16, vx:vx + 16] = valley.grid
        for p in [(12, 19), (12, 20), (17, 12), (18, 12), (27, 22), (27, 23), (15, 27), (16, 27)]:
            self.grid[p] = EMPTY
        self.bushes = [{"pos": (p[0] + vy, p[1] + vx), "kind": FOOD,
                        "seasons": {"spring", "summer", "autumn"}, "region": "valley"}
                       for p in valley.bush_sites]
        self.bushes += [{"pos": p, "kind": k, "seasons": s, "region": r} for p, k, s, r in bushes]
        self.opened_passes = [(12, 19), (12, 20), (17, 12), (18, 12), (27, 22), (27, 23), (15, 27), (16, 27)]
        self.pos = (valley.pos[0] + vy, valley.pos[1] + vx)
        self.body = dict(valley.body)
        self.collapsed = getattr(valley, "collapsed", 0)
        self.collapses = getattr(valley, "collapses", 0)
        self.reflection = None
        self.wanderer = (1, 5)
        self.sounds = []

    # ----------------------------------------------------------------- basics
    @property
    def season(self):
        return SEASONS[(self.t // SEASON_LEN) % 4]

    @property
    def gate_open(self):
        return self.gate_timer > 0

    def passable(self, y, x):
        return 0 <= y < self.H and 0 <= x < self.W and self.grid[y, x] not in (WALL, GATE)

    def view(self):
        y0, x0 = self.pos
        v = np.full((VIEW, VIEW), WALL, dtype=np.int8)
        for dy in range(-VIEW_R, VIEW_R + 1):
            for dx in range(-VIEW_R, VIEW_R + 1):
                y, x = y0 + dy, x0 + dx
                if 0 <= y < self.H and 0 <= x < self.W:
                    v[dy + VIEW_R, dx + VIEW_R] = self.grid[y, x]
        for f in (self.reflection, self.wanderer):
            if f is not None and abs(f[0] - y0) <= VIEW_R and abs(f[1] - x0) <= VIEW_R and f != self.pos:
                v[f[0] - y0 + VIEW_R, f[1] - x0 + VIEW_R] = FIGURE
        return v

    def interoception(self):
        return np.array([self.body["energy"], self.body["hydration"], self.body["integrity"]])

    def in_mirror_zone(self, pos):
        return pos[0] in (4, 5) and MIRROR_COLS[0] <= pos[1] <= MIRROR_COLS[1]

    # ---------------------------------------------------------------- the world
    def _seasons_tick(self):
        season = self.season
        for b in self.bushes:
            p = b["pos"]
            here = self.grid[p]
            if season in b["seasons"]:
                if here == EMPTY and p != self.pos and self.rng.random() < 0.01:
                    self.grid[p] = b["kind"]                 # fruit ripens
            elif here == b["kind"] and self.rng.random() < 0.005:
                self.grid[p] = EMPTY                         # out of season: fruit rots
        wet = season in ("spring", "winter")
        for p in self.seasonal_ponds:
            if p == self.pos:
                continue
            if wet and self.grid[p] == EMPTY and self.rng.random() < 0.003:
                self.grid[p] = WATER
            elif not wet and self.grid[p] == WATER and self.rng.random() < 0.003:
                self.grid[p] = EMPTY

    def _gate_tick(self):
        if self.gate_timer > 0:
            self.gate_timer -= 1
            if self.gate_timer == 0:
                if self.pos in self.gate_cells:
                    self.gate_timer = 1                     # never close on top of it
                else:
                    for p in self.gate_cells:
                        self.grid[p] = GATE
                    self.sounds.append("gate_closed")

    def _figures_tick(self):
        if self.in_mirror_zone(self.pos):
            self.reflection = (2 * MIRROR_POOL_ROW - self.pos[0], self.pos[1])
        else:
            self.reflection = None
        if self.rng.random() < 0.6:
            dy, dx = ACTIONS[int(self.rng.integers(1, 5))]
            ny, nx = self.wanderer[0] + dy, self.wanderer[1] + dx
            if 1 <= ny <= 2 and 1 <= nx <= 9:
                self.wanderer = (ny, nx)

    def step(self, action, sleeping=False):
        self.t += 1
        self.sounds = []
        self._seasons_tick()
        self._gate_tick()
        if self.collapsed:
            self.collapsed -= 1
            self._figures_tick()
            woke = self.collapsed == 0
            if woke:
                for k in self.body:
                    self.body[k] = max(self.body[k], 0.45)
            return {"pushed": False, "consumed": None, "contact": None, "died": False,
                    "true_pos": self.pos, "collapsed": True, "came_round": woke,
                    "sounds": list(self.sounds), "season": self.season, "region": region_of(self.pos)}

        dy, dx = ACTIONS[action]
        ny, nx = self.pos[0] + dy, self.pos[1] + dx
        if self.passable(ny, nx):
            self.pos = (ny, nx)
        pushed = False
        wind = self.wind_plains if region_of(self.pos) in ("plains", "mirror pool") else self.wind_elsewhere
        if self.rng.random() < wind:
            wdy, wdx = ACTIONS[int(self.rng.integers(1, 5))]
            py, px = self.pos[0] + wdy, self.pos[1] + wdx
            if self.passable(py, px):
                self.pos = (py, px)
                pushed = True

        b = self.body
        rate = 0.5 if sleeping else 1.0
        b["energy"] -= rate * (0.004 + (0.002 if action else 0.0))
        b["hydration"] -= rate * 0.006
        cell = int(self.grid[self.pos])
        consumed = None
        if cell == FOOD:
            b["energy"] = min(1.0, b["energy"] + 0.35)
            self.grid[self.pos] = EMPTY
            consumed = "food"
        elif cell == DARK:
            b["energy"] = min(1.0, b["energy"] + 0.08)
            b["integrity"] -= 0.12                           # it makes Ember sick
            self.grid[self.pos] = EMPTY
            consumed = "dark berry"
        elif cell == WATER:
            if b["hydration"] < 0.95:
                consumed = "water"
            b["hydration"] = min(1.0, b["hydration"] + 0.08)
        elif cell == HAZARD:
            b["integrity"] -= 0.15
            consumed = "hazard"
        elif cell == LEVER:
            consumed = "lever"
            if not self.gate_open:
                for p in self.gate_cells:
                    self.grid[p] = EMPTY
                self.sounds.append("gate_opened")
            self.gate_timer = GATE_OPEN_TIME
        if b["energy"] > 0.4 and b["hydration"] > 0.4:
            b["integrity"] = min(1.0, b["integrity"] + 0.004)
        self._figures_tick()

        # the body feels most pushes (like the inner ear), but not all, and now
        # and then it feels one that didn't happen
        felt = None
        if pushed and self.rng.random() < 0.8:
            felt = (wdy, wdx)
        elif not pushed and self.rng.random() < 0.01:
            felt = ACTIONS[int(self.rng.integers(1, 5))]
        info = {"pushed": pushed, "consumed": consumed, "contact": cell, "died": False,
                "true_pos": self.pos, "sounds": list(self.sounds), "season": self.season,
                "region": region_of(self.pos), "felt_push": felt}
        if min(b.values()) <= 0.0:
            for k in b:
                b[k] = max(b[k], 0.0)
            if self.mortal:
                self.deaths += 1
                self.body = {"energy": 0.8, "hydration": 0.8, "integrity": 1.0}
                info["died"] = True
            else:
                self.collapsed = 60
                self.collapses += 1
                info.update({"collapsed": True, "collapse_started": True})
        return info
