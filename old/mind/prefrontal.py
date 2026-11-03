"""
Prefrontal cortex: working memory, goals, and deliberate planning.

The PFC does not decide what matters; the global workspace does. The
PFC turns the broadcast content into a goal, holds it in working
memory, and plans a route to it by searching its *own* cognitive map
(model-based control). When it has no usable plan it says so, and the
basal ganglia fall back on habit.
"""
import heapq
import numpy as np
from .world import ACTIONS, WALL, HAZARD, WATER, FOOD, EMPTY, VIEW_R
from .hippocampus import UNKNOWN

TARGET_TYPE = {"water": WATER, "food": FOOD}


class Prefrontal:
    def __init__(self):
        self.goal = None          # "water" | "food" | "rest" | "explore" | "avoid"
        self.goal_since = 0
        self.plan = []            # list of (y, x) in map coordinates
        self.goal_switches = 0

    def set_goal_from(self, content, t):
        if content is None:
            return
        if content.kind in ("need", "percept", "recall"):
            g = {"energy": "food", "hydration": "water", "integrity": "rest"}.get(content.target, content.target)
        elif content.kind == "threat":
            g = "avoid"
        elif content.kind == "curiosity":
            g = "explore"
        else:
            return  # surprise etc. do not change the goal; they change beliefs
        if g != self.goal:
            self.goal = g
            self.goal_since = t
            self.goal_switches += 1
            self.plan = []

    # ------------------------------------------------------------ planning
    @staticmethod
    def _dijkstra(grid, start, is_target):
        H, W = grid.shape
        dist = {start: 0.0}
        prev = {}
        pq = [(0.0, start)]
        while pq:
            d, (y, x) = heapq.heappop(pq)
            if d > dist.get((y, x), 1e18):
                continue
            if (y, x) != start and is_target(y, x):
                path = [(y, x)]
                while path[-1] in prev and prev[path[-1]] != start:
                    path.append(prev[path[-1]])
                return path[::-1]
            if d > 400:
                break
            for dy, dx in ACTIONS[1:]:
                ny, nx = y + dy, x + dx
                if not (0 <= ny < H and 0 <= nx < W):
                    continue
                c = grid[ny, nx]
                if c == WALL:
                    continue
                step = 30.0 if c == HAZARD else (2.0 if c == UNKNOWN else 1.0)
                nd = d + step
                if nd < dist.get((ny, nx), 1e18):
                    dist[(ny, nx)] = nd
                    prev[(ny, nx)] = (y, x)
                    heapq.heappush(pq, (nd, (ny, nx)))
        return []

    def act(self, grid, pos, view, intero_needs, last_seen=None):
        """Propose an action toward the current goal, or None."""
        g = self.goal
        if g is None:
            return None
        here = view[VIEW_R, VIEW_R]
        if g == "water" and here == WATER and intero_needs[1] > 0.02:
            return 0  # drink
        if g == "rest":
            return 0
        if g == "avoid":
            # step to the neighbour farthest from visible hazards
            hz = np.argwhere(view == HAZARD) - VIEW_R
            best, best_a = -1, None
            for a, (dy, dx) in enumerate(ACTIONS):
                if view[VIEW_R + dy, VIEW_R + dx] in (WALL, HAZARD):
                    continue
                d = min([abs(dy - h[0]) + abs(dx - h[1]) for h in hz] or [9])
                if d > best:
                    best, best_a = d, a
            return best_a
        H, W = grid.shape

        def frontier(y, x):
            return grid[y, x] == UNKNOWN and any(
                0 <= y + dy < H and 0 <= x + dx < W and grid[y + dy, x + dx] not in (UNKNOWN, WALL)
                for dy, dx in ACTIONS[1:])

        searches = []
        if g in TARGET_TYPE:
            tt = TARGET_TYPE[g]
            searches.append(lambda y, x: grid[y, x] == tt)
        searches.append(frontier)  # don't know where it is: explore
        if last_seen is not None and (g in TARGET_TYPE or g == "explore"):
            # map is complete: forage where I haven't looked for a while
            cutoff = np.percentile(last_seen[grid == EMPTY], 25) if (grid == EMPTY).any() else 0
            searches.append(lambda y, x: grid[y, x] == EMPTY and last_seen[y, x] <= cutoff)
        path = []
        for is_target in searches:
            path = self._dijkstra(grid, pos, is_target)
            if path:
                break
        self.plan = path
        if not path:
            return None
        ny, nx = path[0]
        for a, (dy, dx) in enumerate(ACTIONS):
            if (pos[0] + dy, pos[1] + dx) == (ny, nx):
                return a
        return None
