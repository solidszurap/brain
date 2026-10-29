"""
Hippocampus: episodic memory, the cognitive map, and self-location.

- Episodic buffer: what happened, when, how surprising, whether it was
  conscious (broadcast in the global workspace). Conscious and
  surprising episodes get replay priority during sleep.
- Cognitive map: an allocentric map of the world built *only* from the
  agent's own egocentric views, written at the place it believes it is.
- Self-location: path integration from efference copies (where my own
  actions should have taken me), corrected by matching the current view
  against the map when the self-model says "that movement wasn't me".

The map is in the agent's own coordinate frame, not the world's. It has
no access to true coordinates.
"""
import numpy as np
from .world import VIEW_R, VIEW, WALL, HAZARD, WATER, EMPTY, FOOD, ACTIONS

UNKNOWN = -1
STATIC = (WALL, HAZARD, WATER)


class Hippocampus:
    def __init__(self, rng, size=48, capacity=4000, map_enabled=True):
        self.rng = rng
        self.size = size
        self.map_enabled = map_enabled
        self.capacity = capacity
        self.episodes = []
        self.reset_map()

    # ------------------------------------------------------------ the map
    def reset_map(self):
        self.map = np.full((self.size, self.size), UNKNOWN, dtype=np.int8)
        self.seen = np.zeros((self.size, self.size), dtype=np.int32)
        self.last_seen = np.zeros((self.size, self.size), dtype=np.int32)
        self.pos = (self.size // 2, self.size // 2)
        self.lost = False
        self.lost_for = 0
        self.map_resets = getattr(self, "map_resets", -1) + 1

    def write_view(self, view, t):
        if not self.map_enabled or self.lost:
            return
        y0, x0 = self.pos
        for dy in range(-VIEW_R, VIEW_R + 1):
            for dx in range(-VIEW_R, VIEW_R + 1):
                y, x = y0 + dy, x0 + dx
                if 0 <= y < self.size and 0 <= x < self.size:
                    self.map[y, x] = view[dy + VIEW_R, dx + VIEW_R]
                    self.seen[y, x] += 1
                    self.last_seen[y, x] = t

    def path_integrate(self, action, view):
        """Efference copy: where should my own action have taken me?
        I can see whether the cell I am moving into is a wall."""
        dy, dx = ACTIONS[action]
        if view[VIEW_R + dy, VIEW_R + dx] != WALL:
            self.pos = (self.pos[0] + dy, self.pos[1] + dx)
        self._clamp()

    def _clamp(self):
        y = min(max(self.pos[0], VIEW_R), self.size - VIEW_R - 1)
        x = min(max(self.pos[1], VIEW_R), self.size - VIEW_R - 1)
        self.pos = (y, x)

    def _match(self, view, y0, x0):
        """How well does what I see fit what I remember at (y0, x0)?
        Only remembered static features count as strong evidence."""
        patch = self.map[y0 - VIEW_R:y0 + VIEW_R + 1, x0 - VIEW_R:x0 + VIEW_R + 1]
        if patch.shape != (VIEW, VIEW):
            return -1e9, 0
        known = patch != UNKNOWN
        stable = np.isin(patch, STATIC) | np.isin(view, STATIC)
        cnt = int((known & stable).sum())
        agree = (patch == view) & known & stable
        disagree = (patch != view) & known & stable
        return float(agree.sum() - 2 * disagree.sum()), cnt

    def mismatch(self, view):
        """Fraction of remembered static cells that contradict the view."""
        if not self.map_enabled or self.lost:
            return 0.0
        y0, x0 = self.pos
        patch = self.map[y0 - VIEW_R:y0 + VIEW_R + 1, x0 - VIEW_R:x0 + VIEW_R + 1]
        known = (patch != UNKNOWN) & (np.isin(patch, STATIC) | np.isin(view, STATIC))
        if known.sum() < 4:
            return 0.0
        return float(((patch != view) & known).sum() / known.sum())

    def relocalize_local(self, view, margin=2.0):
        """Compare where my efference copy says I am with where the view
        says I am. If the view clearly fits a nearby place better, I was
        moved by something that was not me. Returns the correction."""
        if not self.map_enabled or self.lost:
            return (0, 0)
        y0, x0 = self.pos
        s0, _ = self._match(view, y0, x0)
        best, best_off = s0, (0, 0)
        for dy in range(-2, 3):
            for dx in range(-2, 3):
                if (dy, dx) == (0, 0) or abs(dy) + abs(dx) > 2:
                    continue
                s, _ = self._match(view, y0 + dy, x0 + dx)
                s -= 0.5 * (abs(dy) + abs(dx))  # prior: small displacements
                if s > best:
                    best, best_off = s, (dy, dx)
        if best_off != (0, 0) and best - s0 >= margin:
            self.pos = (y0 + best_off[0], x0 + best_off[1])
            self._clamp()
            return best_off
        return (0, 0)

    def relocalize_global(self, view):
        """After waking up somewhere unknown: search the whole map."""
        if not self.map_enabled:
            return True
        ys, xs = np.where(self.seen > 0)
        if len(ys) == 0:
            return False
        scores = []
        for y in range(ys.min(), ys.max() + 1):
            for x in range(xs.min(), xs.max() + 1):
                if self.map[y, x] in (WALL, UNKNOWN):
                    continue
                s, cnt = self._match(view, y, x)
                scores.append((s, cnt, (y, x)))
        if not scores:
            return False
        scores.sort(key=lambda z: -z[0])
        s1, cnt1, p1 = scores[0]
        s2 = scores[1][0] if len(scores) > 1 else -1e9
        if s1 >= 6 and s1 - s2 >= 3 and cnt1 >= 6:
            self.pos = p1
            self.lost = False
            self.lost_for = 0
            return True
        return False

    def known(self, cell_type):
        """Remembered places of a given type (with age)."""
        ys, xs = np.where(self.map == cell_type)
        return list(zip(ys.tolist(), xs.tolist()))

    # --------------------------------------------------------- episodes
    def store(self, episode):
        self.episodes.append(episode)
        if len(self.episodes) > self.capacity:
            self.episodes.pop(0)

    def sample(self, n):
        """Prioritized replay: surprising and conscious episodes first."""
        if not self.episodes:
            return []
        pr = np.array([e["priority"] for e in self.episodes]) + 1e-3
        pr = pr / pr.sum()
        idx = self.rng.choice(len(self.episodes), size=min(n, len(self.episodes)), p=pr)
        return [self.episodes[i] for i in idx]

    def recent_conscious(self, n=8):
        """Moments when something new ignited the workspace."""
        return [e for e in self.episodes if e.get("ignited")][-n:]

    def frontier_size(self):
        """Unknown cells next to known open space: how much is left to explore."""
        if not self.map_enabled or self.lost:
            return 0
        open_ = (self.map != UNKNOWN) & (self.map != WALL)
        nb = np.zeros_like(open_)
        nb[1:] |= open_[:-1]; nb[:-1] |= open_[1:]
        nb[:, 1:] |= open_[:, :-1]; nb[:, :-1] |= open_[:, 1:]
        return int((nb & (self.map == UNKNOWN)).sum())
