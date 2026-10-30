"""
Ember's mind for the wide world: the v3 brain, plus what that world asks of it.

Everything here is *learned from its own life* except the mechanisms that do
the learning:

  taste learning     what each new kind of thing does to its body when it
                     touches it (dark berries make it sick -> it avoids them;
                     like conditioned taste aversion in animals)
  curiosity          new kinds of things attract it until it knows them
  hearing            it hears the gate, from anywhere
  cause and effect   "when I step on X, I hear Y": a rule is learned from
                     repeated co-occurrence (it finds out the lever opens the gate)
  two-step plans     if what it needs is behind the closed gate, and it has
                     learned how the gate opens, it first goes to open it
  seasonal memory    where food appeared in which season; when it is hungry and
                     knows of no food, it goes where food grew this time of year
  reliable landmarks landmarks that have changed (the gate, ponds that dry up)
                     stop being trusted for finding its way
  mirror sense       for things that move, it checks whether their movement is
                     predicted by its own; its reflection is, the other figure
                     isn't (contingency-based self-recognition)
"""
from collections import Counter, deque

import numpy as np

from .agent import Mind
from .cortex import WorldModel
from .metacognition import Metacognition
from .hippocampus import Hippocampus, UNKNOWN
from .prefrontal import Prefrontal
from .workspace import Content
from .world import EMPTY, WALL, FOOD, WATER, HAZARD, ACTIONS, VIEW_R, VIEW, N_ACTIONS
from .wideworld import DARK, GATE, LEVER, FIGURE, N_TYPES_WIDE, TYPE_NAMES_WIDE
from .autobiography import Autobiography, IMPORTANCE, first_person

INNATE = {EMPTY, WALL, FOOD, WATER, HAZARD}   # kinds it was born understanding
NAMES = TYPE_NAMES_WIDE
MAP_SIZE = 96


class EmberHippocampus(Hippocampus):
    """The hippocampus plus a sense of how sure it is of where it is.

    Instead of one guess, it keeps a probability spread over where it might
    really be (offsets of up to 3 cells from where it thinks it is; a bigger
    error means it is lost, and it searches more widely, carefully):
      - every moment the spread widens a little, by how often it has learned
        the wind pushes it (much more if its world model was just surprised)
      - every remembered landmark it sees sharpens it: places where what it
        sees fits its map become more likely, places where it doesn't, less
      - if another place becomes clearly more likely, it moves its belief there
    In landmark-poor land (plains, marsh) the spread grows and its confidence
    drops; while unsure it only sketches open ground into blank parts of its
    map, so it never draws landmarks in the wrong place."""

    R = 3
    BLOCKING = (WALL, GATE)
    EVIDENCE = (EMPTY, WALL, WATER, HAZARD, LEVER, GATE)   # kinds that normally stay put

    def init_uncertainty(self):
        n = 2 * self.R + 1
        self.P = np.zeros((n, n))
        self.P[self.R, self.R] = 1.0
        self.confidence = 1.0
        self.uncertainty = 0.0
        self.push_rate = 0.05
        self._evident, self._detected = 20, 1
        self.writes_skipped = 0
        self.sketched = np.zeros(self.map.shape, dtype=bool)
        self._bad_fit = 0
        self._unsure_for = 0
        self.felt = None

    def path_integrate(self, action, view):
        dy, dx = ACTIONS[action]
        moved = view[VIEW_R + dy, VIEW_R + dx] not in self.BLOCKING
        if moved:
            self.pos = (self.pos[0] + dy, self.pos[1] + dx)
        self._clamp()
        self._prev_view = view
        self._own = (dy, dx) if moved else (0, 0)

    FLOW_KINDS = (EMPTY, WALL, WATER, HAZARD, LEVER, GATE)
    LANDMARKS = (WALL, WATER, HAZARD, LEVER, GATE)   # open ground matching open ground proves nothing
    # how common each kind of cell is: seeing a common kind where you expected
    # it is weak evidence, a rare one (a wall, a pond) strong evidence
    BASE_RATE = np.full(16, 0.05)
    BASE_RATE[[EMPTY, WALL, WATER, HAZARD, LEVER, GATE]] = [0.7, 0.12, 0.05, 0.03, 0.01, 0.01]

    def _evidence(self, seen, expected, usable):
        """Log-likelihood ratio (vs knowing nothing) of seeing `seen` where
        memory or prediction says `expected`, summed over usable cells."""
        br = self.BASE_RATE
        match = np.log(0.9 / br[seen])
        mismatch = np.log(0.1 / (1.0 - br[expected]))
        return np.where(usable, np.where(seen == expected, match, mismatch), 0.0)

    def _optic_flow(self, view):
        """How well does the new view fit the old one shifted by my own step
        alone, or by my step plus a push N/S/W/E? Compared on the same cells for
        every option. Returns log-likelihoods for [no push, N, S, W, E]."""
        prev = getattr(self, "_prev_view", None)
        if prev is None:
            return np.zeros(5)
        oy, ox = self._own
        Ds = [(oy + py, ox + px) for (py, px) in ACTIONS]
        i0 = max(max(0, -Dy) for Dy, _ in Ds)
        i1 = min(VIEW - max(0, Dy) for Dy, _ in Ds)
        j0 = max(max(0, -Dx) for _, Dx in Ds)
        j1 = min(VIEW - max(0, Dx) for _, Dx in Ds)
        if i1 <= i0 or j1 <= j0:
            return np.zeros(5)
        out = np.zeros(5)
        a = view[i0:i1, j0:j1]
        for k, (Dy, Dx) in enumerate(Ds):
            b = prev[i0 + Dy:i1 + Dy, j0 + Dx:j1 + Dx]
            ok = np.isin(a, self.FLOW_KINDS) & np.isin(b, self.FLOW_KINDS) \
                & (np.isin(a, self.LANDMARKS) | np.isin(b, self.LANDMARKS))
            out[k] = self._evidence(a, b, ok).sum()
        return out

    def _window(self, arr, fill):
        R, y0, x0 = self.R, self.pos[0], self.pos[1]
        n = 2 * R + 1 + 2 * VIEW_R
        out = np.full((n, n), fill, dtype=arr.dtype)
        ys, xs = y0 - R - VIEW_R, x0 - R - VIEW_R
        a0, b0 = max(ys, 0), max(xs, 0)
        a1, b1 = min(ys + n, self.size), min(xs + n, self.size)
        out[a0 - ys:a1 - ys, b0 - xs:b1 - xs] = arr[a0:a1, b0:b1]
        return np.lib.stride_tricks.sliding_window_view(out, (VIEW, VIEW))

    def relocalize_local(self, view, margin=2.0):
        if not self.map_enabled or self.lost:
            return (0, 0)
        R = self.R
        # 1. was I pushed? optic flow says how likely each push is; with nothing
        #    to see (open ground), every option stays possible and belief spreads
        p = self.push_rate
        flow = self._optic_flow(view)
        prior = np.array([1 - p, p / 4, p / 4, p / 4, p / 4])
        # the body's sense of being moved: right about 80% of pushes, rarely
        # feels one that didn't happen
        felt = getattr(self, "felt", None)
        if felt is None:
            body = np.array([0.99, 0.2, 0.2, 0.2, 0.2])
        else:
            k = ACTIONS.index(tuple(felt))
            body = np.full(5, 0.01 / 4)
            body[k] = 0.8
        w = prior * body * np.exp(flow - flow.max())
        w /= w.sum()
        P = self.P
        S = w[0] * P
        S[:-1, :] += w[1] * P[1:, :]      # pushed north: true position is one row up
        S[1:, :] += w[2] * P[:-1, :]      # pushed south
        S[:, :-1] += w[3] * P[:, 1:]      # pushed west
        S[:, 1:] += w[4] * P[:, :-1]      # pushed east
        # 2. evidence: does what it sees fit its map, at each possible offset?
        win = self._window(self.map, UNKNOWN)
        vol = self._window(self.volatile | self.sketched, True)
        ev = np.isin(win, self.EVIDENCE) & ~vol & np.isin(view, self.EVIDENCE)[None, None] \
            & (np.isin(win, self.LANDMARKS) | np.isin(view, self.LANDMARKS)[None, None])
        same = (win == view[None, None])
        n_match = (same & ev).sum(axis=(2, 3))
        n_mis = (~same & ev).sum(axis=(2, 3))
        # Compare every alternative on the same cells: the ones it can check from
        # where it believes it is. (Otherwise a guess deeper inside the mapped
        # area always "explains" more, just because more of it is known.)
        joint = ev & ev[R, R][None, None]
        seen = np.broadcast_to(view, win.shape)
        here = np.broadcast_to(np.where(ev[R, R], win[R, R], EMPTY), win.shape)
        ll_alt = self._evidence(seen, np.where(joint, win, EMPTY), joint).sum(axis=(2, 3))
        ll_here = self._evidence(seen, here, joint).sum(axis=(2, 3))
        loglik = ll_alt - ll_here
        post = S * np.exp(loglik - loglik.max())
        total = post.sum()
        post = post / total if total > 0 else S / S.sum()
        # 3. move the belief if somewhere else is now clearly more likely
        iy, ix = np.unravel_index(int(post.argmax()), post.shape)
        off = (int(iy - R), int(ix - R))
        shift = (0, 0)
        big_jump = abs(off[0]) + abs(off[1]) > 2
        if off != (0, 0) and post[iy, ix] > 0.5 and post[iy, ix] > 3 * post[R, R] \
                and (not big_jump or self.uncertainty >= 1.0):
            self.pos = (self.pos[0] + off[0], self.pos[1] + off[1])
            self._clamp()
            shifted = np.zeros_like(post)
            dy, dx = off
            shifted[max(0, -dy):post.shape[0] - max(0, dy), max(0, -dx):post.shape[1] - max(0, dx)] = \
                post[max(0, dy):post.shape[0] - max(0, -dy), max(0, dx):post.shape[1] - max(0, -dx)]
            post = shifted / shifted.sum()
            shift = off
        self.P = post
        self.confidence = float(post[R, R])
        yy, xx = np.mgrid[-R:R + 1, -R:R + 1]
        self.uncertainty = float((post * (np.abs(yy) + np.abs(xx))).sum())
        # 4. completely lost for a while? search the whole map for where what it
        #    sees fits (only accepted if one place fits clearly best)
        self._unsure_for = self._unsure_for + 1 if self.confidence < 0.05 else 0
        if self._unsure_for >= 30 and int(np.isin(view, (WALL, WATER, HAZARD)).sum()) >= 4:
            self._unsure_for = 0
            if self._global_search(view):
                shift = (1, 1)   # any non-zero value: it moved its belief
        # 5. learn how windy its world is, from places where pushes are visible
        evidence_here = int(ev[R, R].sum())
        if evidence_here >= 6:
            self._evident += 1
            self._detected += shift != (0, 0)
            self.push_rate = min(0.3, self._detected / self._evident)
            best_fit = (n_match - n_mis).max()
            self._bad_fit = self._bad_fit + 1 if best_fit < 0 else 0
            if self._bad_fit >= 10:                 # nothing nearby fits: it is lost
                self.lost, self.lost_for, self._bad_fit = True, 0, 0
                self.P[:] = 0.0
                self.P[R, R] = 1.0
        return shift

    SEARCH_RADIUS = 10

    def _global_search(self, view):
        """Lost: look for where what it sees fits its map, but only within
        SEARCH_RADIUS cells of where it believes it is (drift is never larger),
        and only accept one place that fits clearly better than any other."""
        y0, x0 = self.pos
        r = self.SEARCH_RADIUS
        scores = []
        for y in range(max(VIEW_R, y0 - r), min(self.size - VIEW_R - 1, y0 + r) + 1):
            for x in range(max(VIEW_R, x0 - r), min(self.size - VIEW_R - 1, x0 + r) + 1):
                if self.map[y, x] in (WALL, UNKNOWN):
                    continue
                sc, cnt = self._match(view, y, x)
                scores.append((sc, cnt, (y, x)))
        if len(scores) < 2:
            return False
        scores.sort(key=lambda z: -z[0])
        (s1, c1, p1), (s2, _, _) = scores[0], scores[1]
        if s1 >= 6 and s1 - s2 >= 3 and c1 >= 6:
            self.pos = p1
            self.P[:] = 0.0
            self.P[self.R, self.R] = 1.0
            self.confidence, self.uncertainty = 1.0, 0.0
            self.probation = 30          # don't draw on the map until this is confirmed
            self.global_finds = getattr(self, "global_finds", 0) + 1
            return True
        return False

    def relocalize_global(self, view):
        found = self._global_search(view)
        if found:
            self.lost = False
            self.lost_for = 0
        return found

    def write_view(self, view, t):
        # Draw on the map only when sure of where it is, and when what it sees
        # mostly agrees with what it remembers (a few changed cells are the
        # world changing: a pond dried up). Drawing from a wrong position would
        # put landmarks in the wrong place, and a wrong map makes every later
        # correction wrong too.
        win = self._window(self.map, UNKNOWN)[self.R, self.R]
        vol = self._window(self.volatile | self.sketched, True)[self.R, self.R]
        ev = np.isin(win, self.EVIDENCE) & ~vol & np.isin(view, self.EVIDENCE) \
            & (np.isin(win, self.LANDMARKS) | np.isin(view, self.LANDMARKS))
        agrees = self._evidence(view, np.where(ev, win, EMPTY), ev).sum() >= 0
        n_changed = int(((win != view) & ev).sum())
        n_anchor = int(((win == view) & ev & np.isin(view, self.LANDMARKS)).sum())
        probation = getattr(self, "probation", 0)
        if probation:
            self.probation = probation - 1 if agrees else 30
        if self.confidence >= 0.9 and (agrees or n_changed <= 4) and not probation:
            y0, x0 = self.pos
            self.sketched[y0 - VIEW_R:y0 + VIEW_R + 1, x0 - VIEW_R:x0 + VIEW_R + 1] = False
            if n_changed and n_anchor < 6:
                # a landmark seems to have changed, but too little else here
                # confirms where it is: don't redraw it (it may be the one who's off)
                keep = (win != view) & ev
                saved = self.map[y0 - VIEW_R:y0 + VIEW_R + 1, x0 - VIEW_R:x0 + VIEW_R + 1].copy()
                vol = self.volatile[y0 - VIEW_R:y0 + VIEW_R + 1, x0 - VIEW_R:x0 + VIEW_R + 1].copy()
                super().write_view(view, t)
                self.map[y0 - VIEW_R:y0 + VIEW_R + 1, x0 - VIEW_R:x0 + VIEW_R + 1][keep] = saved[keep]
                self.volatile[y0 - VIEW_R:y0 + VIEW_R + 1, x0 - VIEW_R:x0 + VIEW_R + 1] = vol
                return
            super().write_view(view, t)
            return
        # unsure: only sketch open ground into blank parts of the map ...
        self.writes_skipped += 1
        y0, x0 = self.pos
        # ... but a dried-up pond or eaten food is plain to see even when it is
        # a little unsure exactly where it stands: update those (and never
        # count such changes as evidence about where it is)
        if self.confidence >= 0.6:
            RES = (WATER, FOOD, DARK)
            for dy in range(-VIEW_R, VIEW_R + 1):
                for dx in range(-VIEW_R, VIEW_R + 1):
                    y, x = y0 + dy, x0 + dx
                    seen = view[dy + VIEW_R, dx + VIEW_R]
                    if 0 <= y < self.size and 0 <= x < self.size and self.map[y, x] in RES \
                            and seen in (EMPTY,) + RES and seen != self.map[y, x]:
                        if self.map[y, x] == WATER or seen == WATER:
                            self.volatile[y, x] = True       # water here comes and goes
                        self.map[y, x] = seen
                        self.last_seen[y, x] = t
        for dy in range(-VIEW_R, VIEW_R + 1):
            for dx in range(-VIEW_R, VIEW_R + 1):
                y, x = y0 + dy, x0 + dx
                if 0 <= y < self.size and 0 <= x < self.size and self.map[y, x] == UNKNOWN \
                        and view[dy + VIEW_R, dx + VIEW_R] == EMPTY:
                    self.map[y, x] = EMPTY
                    self.sketched[y, x] = True
                    self.seen[y, x] += 1
                    self.last_seen[y, x] = t


class MirrorSense:
    """Tracks moving figures it sees and asks: does this one move when I move?"""

    def __init__(self):
        self.tracks = []
        self.classified = []      # results, in order
        self.n_self = self.n_other = 0

    @property
    def n_classified(self):
        return self.n_self + self.n_other

    def observe(self, t, my_disp, figures):
        """my_disp: my own movement this moment, or None if I don't know it
        (something pushed me). figures: believed positions of figures I see.
        Returns the figures it has just made up its mind about."""
        unmatched = list(figures)
        for tr in self.tracks:
            if not unmatched:
                tr["miss"] += 1
                continue
            d = [abs(f[0] - tr["pos"][0]) + abs(f[1] - tr["pos"][1]) for f in unmatched]
            j = int(np.argmin(d))
            if d[j] <= 2:
                ambiguous = sum(1 for x in d if x <= d[j] + 1) > 1     # two figures close by: which is which?
                f = unmatched.pop(j)
                if my_disp is not None and not ambiguous:
                    tr["pairs"].append((tuple(int(v) for v in my_disp),
                                        (int(f[0] - tr["pos"][0]), int(f[1] - tr["pos"][1]))))
                tr.update(pos=f, miss=0, last_t=t)
            else:
                tr["miss"] += 1
        for f in unmatched:
            self.tracks.append({"pos": f, "pairs": [], "miss": 0, "born": t, "last_t": t, "label": None})
        results = []
        for tr in self.tracks:
            if tr["label"] is None:
                r = self._classify(tr, final=tr["miss"] >= 2)
                if r:
                    tr["label"] = r["label"]
                    results.append(r)
        self.tracks = [tr for tr in self.tracks if tr["miss"] < 2]
        return results

    def _classify(self, tr, final=False):
        pairs = [(m, f) for m, f in tr["pairs"] if m != (0, 0)]
        if len({m for m, _ in pairs}) < 2:
            return None          # I didn't move in enough different ways to tell
        by_mine = {}
        for m, f in pairs:
            by_mine.setdefault(m, Counter())[f] += 1
        predictable = sum(c.most_common(1)[0][1] for c in by_mine.values()) / len(pairs)
        overall = Counter(f for _, f in pairs)
        baseline = overall.most_common(1)[0][1] / len(pairs)
        moved = sum(f != (0, 0) for _, f in pairs) / len(pairs)
        is_me = predictable >= 0.9 and predictable - baseline >= 0.25 and moved >= 0.5
        if is_me and len(pairs) >= 8:
            label = "self"
        elif len(pairs) >= 12 or (final and len(pairs) >= 6):
            label = "self" if is_me else "other"
        else:
            return None          # not enough evidence yet
        res = {"label": label, "n": len(pairs), "predictable": round(predictable, 2),
               "baseline": round(baseline, 2), "last_pos": tuple(int(v) for v in tr["pos"]), "last_t": tr["last_t"]}
        self.classified.append(res)
        if label == "self":
            self.n_self += 1
        else:
            self.n_other += 1
        return res


class EmberMind(Mind):
    # ------------------------------------------------------------------ birth
    @classmethod
    def newborn(cls, seed):
        m = cls(seed=seed)
        m.cortex = WorldModel(m.rng, n_types=N_TYPES_WIDE)
        m.meta = Metacognition(n_in=m.cortex.n_in)
        m.hippo = EmberHippocampus(m.rng, size=MAP_SIZE)
        m.escape_reflex = True
        m.init_extras()
        return m

    def init_extras(self):
        if not isinstance(self.hippo, EmberHippocampus):
            self.hippo.__class__ = EmberHippocampus
        self.hippo.volatile = np.zeros(self.hippo.map.shape, dtype=bool)
        self.hippo.init_uncertainty()
        self.relocalize_patience = 10 ** 9     # never throw its map away; keep trying to find itself
        self.effects = {}                 # kind -> mean body change on contact, relative to plain ground
        self.effect_n = Counter()
        self.ground = np.array([-0.005, -0.006, 0.002])
        self.harmful, self.nourishing = set(), set()
        self.learned = []                 # (tick, what it found out)
        self.sightings = Counter()
        self.heard = []
        self.cooccur = Counter()          # (kind, sound) -> times heard right after touching kind
        self.contact_count = Counter()
        self.rules = {}                   # (kind, sound) -> tick learned
        self.gate_known, self.levers_known = set(), set()
        self.gate_open_belief = False
        self.season = None
        self.season_memory = {}           # map cell -> Counter(season -> food sightings)
        self._food_counted = {}
        self.subgoal = None
        self.multi_step = []              # [tick started, tick gate opened, tick goal reached, goal]
        self.investigate_target, self.investigate_until = None, -1
        self.jiggle = 0
        self.mirror = MirrorSense()
        self.knows_reflection = False
        self.pending_self = None
        self.anticipating = set()
        self.anticipations = []           # (tick, cell): trips to where food grew this season before
        self.candidates_posted = 0
        self.new_classifications = []

    # ----------------------------------------------------------------- senses
    def sense(self, sounds, season, felt_push=None):
        """Hearing, the feel of the season (like day length for animals), and
        the body's sense of being moved (like the inner ear)."""
        self.heard = list(sounds or [])
        self.season = season
        self.hippo.felt = felt_push
        if "gate_opened" in self.heard:
            self.gate_open_belief = True
            if self.gate_known and self.sightings[GATE] < 200:
                # orient to the sound: go and see what happened
                py, px = self.hippo.pos
                self.investigate_target = min(self.gate_known, key=lambda c: abs(c[0] - py) + abs(c[1] - px))
                self.investigate_until = self.t + 150
        if "gate_closed" in self.heard:
            self.gate_open_belief = False

    def _to_map(self, vy, vx):
        py, px = self.hippo.pos
        return (py + vy - VIEW_R, px + vx - VIEW_R)

    def _note_view(self, view):
        for k in np.unique(view):
            self.sightings[int(k)] += 1
        # Seeing the gate shut beats remembering it open. Its belief used to
        # change only on the gate's sound, which it can't hear while
        # unconscious: if the gate shut during a collapse it kept believing
        # it open, waited in front of it, and collapsed again (winter loops).
        # An open gate is just a gap, so a visible gate is always a shut one.
        if self.gate_open_belief and (view == GATE).any():
            self.gate_open_belief = False
        if self.hippo.lost or self.hippo.confidence < 0.6:
            return
        for vy, vx in np.argwhere(view == GATE):
            self.gate_known.add(self._to_map(vy, vx))
        for vy, vx in np.argwhere(view == LEVER):
            self.levers_known.add(self._to_map(vy, vx))
        for vy, vx in np.argwhere(view == FOOD):
            cell = self._to_map(vy, vx)
            if self.t - self._food_counted.get(cell, -10**9) > 200:
                self.season_memory.setdefault(cell, Counter())[self.season] += 1
                self._food_counted[cell] = self.t
        self._note_letdowns(view)

    def _note_letdowns(self, view):
        """A place where food grew this season before, seen empty: a let-down,
        counted on sight like a sighting. It used to count only when Ember
        stood on the place, which it rarely does: it sees the place is empty
        from two cells away and turns off. So places that only ever had
        autumn's leftovers in winter were never crossed off, and that
        imagined food kept it from trying the gate (winter loops). Seeing
        food at a place clears its let-downs; one it just ate empty isn't
        one (no let-down within 200 moments of food seen there)."""
        counted = getattr(self, "_empty_counted", None)
        if counted is None:
            counted = self._empty_counted = {}
        key = ("empty", self.season)
        for vy in range(view.shape[0]):
            for vx in range(view.shape[1]):
                cell = self._to_map(vy, vx)
                c = self.season_memory.get(cell)
                if not c or c.get(self.season, 0) < 1:
                    continue
                if view[vy, vx] == FOOD:
                    c.pop(key, None)
                elif self.t - self._food_counted.get(cell, -10**9) > 200 \
                        and self.t - counted.get(cell, -10**9) > 200:
                    c[key] += 1
                    counted[cell] = self.t

    def _is_novel(self, k):
        if k == FIGURE:
            return self.mirror.n_classified < 4
        if k == GATE:
            return self.sightings[GATE] < 60
        return self.contact_count[k] < 2

    def season_spots(self):
        """Places where it has seen food in this season before, that it hasn't
        just checked, and that haven't let it down twice (seen empty) since it
        last saw food there."""
        out = []
        for cell, c in self.season_memory.items():
            if c.get(self.season, 0) >= 1 and self.t - self.hippo.last_seen[cell] > 80 \
                    and c.get(("empty", self.season), 0) < 2:
                out.append(cell)
        return out

    # ------------------------------------------------------------- workspace
    def extra_candidates(self, view, intero, needs):
        self._note_view(view)
        for k in set(np.unique(view).tolist()):
            if k in INNATE or k in self.harmful or not self._is_novel(k):
                continue
            self.gw.post(Content("novel", NAMES[k], 0.36, "curiosity", {"type": int(k)}))
        for s in self.heard:
            self.gw.post(Content("hearing", s.replace("_", " "), 0.45, "auditory cortex"))
        if getattr(self, "hearing_voice", None):
            # someone is speaking to it (see ember.py): it competes like any sound
            # (as loud as a strong need: only real urgency, a hazard or a very strong
            # need, keeps it from noticing someone talking to it)
            self.gw.post(Content("voice", "someone speaking", 1.0, "auditory cortex"))
        if self.pending_self is not None:
            self.gw.post(self.pending_self)
            self.pending_self = None
        if self.subgoal:
            sal = 0.55
            if getattr(self, "wiring", "direct") == "broadcast":
                # a plan is as urgent as the need it serves (plus a little,
                # so it can hold its own against that need's own signal)
                i = {"food": 0, "water": 1}.get(self.subgoal["for"], 0)
                sal = 0.15 + 1.2 * float(needs[i]) ** 0.8
            self.gw.post(Content("plan", "open the gate", sal, "PFC", {"for": self.subgoal["for"]}))
        if self.hippo.uncertainty >= 1.5:
            self.gw.post(Content("self", "unsure where I am", 0.5, "self-model",
                                 {"uncertainty": round(self.hippo.uncertainty, 1)}))
        if needs[0] > 0.25 and not (view == FOOD).any() and not self.hippo.known(FOOD):
            spots = self.season_spots()
            if spots:
                py, px = self.hippo.pos
                d = min(abs(y - py) + abs(x - px) for y, x in spots)
                self.gw.post(Content("recall", "food", 0.05 + float(needs[0]) ** 0.8, "hippocampus",
                                     {"dist": d, "season": self.season}))
        self.candidates_posted += len(self.gw.candidates) + 1

    # --------------------------------------------------------------- planning
    def planning_grid(self, needs, view=None):
        """The map as it should be used for planning: what it believes, not just
        what it last saw. What it sees right now overrides memory around it
        (true even when it is unsure exactly where it is on its map)."""
        g = self.hippo.map.copy()
        if view is not None:
            py, px = self.hippo.pos
            y0, x0 = py - VIEW_R, px - VIEW_R
            ys, xs = slice(max(0, y0), y0 + VIEW), slice(max(0, x0), x0 + VIEW)
            g[ys, xs] = view[max(0, -y0):, max(0, -x0):][:g[ys, xs].shape[0], :g[ys, xs].shape[1]]
        g[g == FIGURE] = EMPTY
        for k in self.harmful:
            g[g == k] = HAZARD
        if self.gate_open_belief:
            for c in self.gate_known:
                g[c] = EMPTY
        else:
            g[g == GATE] = WALL
            for c in self.gate_known:
                g[c] = WALL
        self.anticipating = set()
        if needs[0] > 0.25 and not (g == FOOD).any():
            spots = [c for c in self.season_spots() if g[c] == EMPTY]
            for c in spots:
                g[c] = FOOD                     # "food grows there this time of year"
            self.anticipating = set(spots)
        return g

    def _step_toward(self, pos, nxt):
        for a, (dy, dx) in enumerate(ACTIONS):
            if (pos[0] + dy, pos[1] + dx) == tuple(nxt):
                return a
        return None

    def knows_how_to_open_gate(self):
        for (k, s) in self.rules:
            if s == "gate_opened":
                return k
        return None

    def _consider_gate_plan(self, grid, pos, goal):
        kind = self.knows_how_to_open_gate()
        if kind is None or not self.gate_known or self.gate_open_belief:
            return None
        openers = {tuple(c) for c in np.argwhere(self.hippo.map == kind)} | (self.levers_known if kind == LEVER else set())
        if not openers:
            return None
        target = FOOD if goal == "food" else WATER
        g_open = grid.copy()
        for c in self.gate_known:
            g_open[c] = EMPTY
        H, W = g_open.shape

        def worth_it(y, x):
            # what it needs, or land it has never seen (behind the gate)
            if g_open[y, x] == target:
                return True
            return g_open[y, x] == UNKNOWN and any(
                0 <= y + dy < H and 0 <= x + dx < W and g_open[y + dy, x + dx] not in (UNKNOWN, WALL)
                for dy, dx in ACTIONS[1:])
        if not Prefrontal._dijkstra(g_open, pos, worth_it):
            return None
        path = Prefrontal._dijkstra(grid, pos, lambda y, x: (y, x) in openers)
        if not path:
            return None
        self.subgoal = {"for": goal, "since": self.t, "lever": path[-1]}
        self.multi_step.append([self.t, None, None, goal])
        return self._step_toward(pos, path[0])

    def _pursue_subgoal(self, grid, pos):
        sg = self.subgoal
        if self.gate_open_belief:
            if self.multi_step and self.multi_step[-1][1] is None:
                self.multi_step[-1][1] = self.t
            self.subgoal = None
            return None
        if self.t - sg["since"] > 400:
            self.subgoal = None                  # gave up
            return None
        path = Prefrontal._dijkstra(grid, pos, lambda y, x: (y, x) == tuple(sg["lever"]))
        if not path:
            self.subgoal = None
            return None
        return self._step_toward(pos, path[0])

    def _investigate(self, view, grid, content):
        pos = self.hippo.pos
        k = content.data.get("type") if content is not None and content.kind == "novel" else None
        if k == FIGURE:
            figs = np.argwhere(view == FIGURE)
            if len(figs):
                near = figs[np.argmin(np.abs(figs - VIEW_R).sum(1))]
                if abs(near[0] - VIEW_R) <= 2:
                    # contingency testing: move side to side and watch what moves with me
                    self.jiggle += 1
                    return 3 if self.jiggle % 2 else 4
                tgt = self._to_map(*near)
                path = Prefrontal._dijkstra(grid, pos, lambda y, x: abs(y - tgt[0]) + abs(x - tgt[1]) <= 2 and y > tgt[0])
                return self._step_toward(pos, path[0]) if path else None
            return None
        if k is not None:
            cells = [self._to_map(vy, vx) for vy, vx in np.argwhere(view == k)]
            if k == GATE:
                pred = lambda y, x: any(abs(y - c[0]) + abs(x - c[1]) == 1 for c in cells)
            else:
                pred = lambda y, x: (y, x) in cells
            path = Prefrontal._dijkstra(grid, pos, pred)
            return self._step_toward(pos, path[0]) if path else None
        if self.investigate_target is not None and self.t < self.investigate_until:
            tgt = self.investigate_target
            g2 = grid.copy()
            if self.gate_open_belief:
                g2[tgt] = EMPTY
            path = Prefrontal._dijkstra(g2, pos, lambda y, x: abs(y - tgt[0]) + abs(x - tgt[1]) <= 1)
            if path:
                return self._step_toward(pos, path[0])
            self.investigate_target = None
        return None

    def _directly_reachable(self, grid, pos, goal):
        """Is any known food/water reachable without the gate? (rechecked every
        15 moments; route-finding is the expensive part of thinking)"""
        key = (goal, self.t // 15, self.gate_open_belief)
        if getattr(self, "_reach_key", None) != key:
            target = FOOD if goal == "food" else WATER
            self._reach_key = key
            self._reach = bool(Prefrontal._dijkstra(grid, pos, lambda y, x: grid[y, x] == target))
        return self._reach

    def _try_things(self, grid, pos):
        """Stuck: what it needs can't be reached and it knows no way round.
        Trial and error, like an animal in a puzzle box: go and touch the
        kind of thing it understands least (but knows doesn't hurt)."""
        kinds = [k for k in (LEVER, DARK) if k not in self.harmful]
        cells = {}
        for k in kinds:
            for c in np.argwhere(self.hippo.map == k):
                cells[tuple(c)] = k
        if not cells:
            return None
        least = min(self.contact_count[k] for k in set(cells.values()))
        targets = {c for c, k in cells.items() if self.contact_count[k] <= least + 2}
        if tuple(pos) in targets:
            # standing on it: step off so it can be stepped on again
            for a in range(1, N_ACTIONS):
                dy, dx = ACTIONS[a]
                if grid[pos[0] + dy, pos[1] + dx] not in (WALL, GATE, HAZARD):
                    return a
        path = Prefrontal._dijkstra(grid, pos, lambda y, x: (y, x) in targets)
        if path:
            self.tried = getattr(self, "tried", 0) + 1
            return self._step_toward(pos, path[0])
        return None

    def _seek_landmarks(self, grid, pos):
        hp = self.hippo
        stable = (np.isin(hp.map, (WALL, WATER, HAZARD)) & ~hp.volatile).astype(int)
        if not stable.any():
            return None
        c = np.cumsum(np.cumsum(np.pad(stable, ((1, 0), (1, 0))), 0), 1)
        n = hp.size
        y0 = np.clip(np.arange(n) - 2, 0, n)
        y1 = np.clip(np.arange(n) + 3, 0, n)
        rich = (c[y1[:, None], y1[None, :]] - c[y0[:, None], y1[None, :]]
                - c[y1[:, None], y0[None, :]] + c[y0[:, None], y0[None, :]]) >= 5
        path = Prefrontal._dijkstra(grid, pos, lambda y, x: rich[y, x])
        return self._step_toward(pos, path[0]) if path else None

    def _release(self, proposals, view):
        """Final gate before acting: never into walls or the closed gate, never
        onto something that hurts, never stand still on something that hurts."""
        bad = {HAZARD} | self.harmful
        for a in proposals:
            if a is None:
                continue
            dy, dx = ACTIONS[a]
            tgt = int(view[VIEW_R + dy, VIEW_R + dx])
            if a != 0 and (tgt in (WALL, GATE) or tgt in bad):
                continue
            if a == 0 and int(view[VIEW_R, VIEW_R]) in bad:
                continue
            return int(a)
        safe = [b for b in range(1, N_ACTIONS)
                if int(view[VIEW_R + ACTIONS[b][0], VIEW_R + ACTIONS[b][1]]) not in ({WALL, GATE} | bad)]
        return int(self.rng.choice(safe)) if safe else 0

    def choose_action(self, view, intero, needs):
        if self.hippo.lost:
            return super().choose_action(view, intero, needs)
        if getattr(self, "wiring", "direct") == "broadcast":
            return self._choose_by_broadcast(view, intero, needs)
        pos = self.hippo.pos
        grid = self.planning_grid(needs, view)
        cur = self.gw.current
        a = None
        investigating = (cur is not None and cur.kind == "novel") or (
            self.investigate_target is not None and self.t < self.investigate_until and needs.max() < 0.4)
        if cur is not None and cur.kind == "self" and cur.target == "unsure where I am":
            a = self._seek_landmarks(grid, pos)
        elif investigating:
            a = self._investigate(view, grid, cur)
        if a is None and self.subgoal:
            a = self._pursue_subgoal(grid, pos)
        if a is None and self.pfc.goal in ("food", "water") and not self.subgoal \
                and not self._directly_reachable(grid, pos, self.pfc.goal):
            # what it needs can't be reached as things are: is the gate the way?
            a = self._consider_gate_plan(grid, pos, self.pfc.goal)
        if a is None:
            a = self.pfc.act(grid, pos, view, needs, self.hippo.last_seen)
            if a is None and self.pfc.goal in ("food", "water"):
                a = self._consider_gate_plan(grid, pos, self.pfc.goal)
                if a is None and needs.max() > 0.4:
                    a = self._try_things(grid, pos)
        habit_a = self.bg.habit(self._ctx["s"])
        return self._release([a, habit_a], view), a

    def _choose_by_broadcast(self, view, intero, needs):
        """Experimental wiring (not Ember's default; see trials.py). In the
        direct wiring above, a hand-written order decides what Ember does when
        several things want its behaviour at once: being unsure where it is
        beats investigating, which beats an unfinished gate plan, which beats
        the current goal; and some of those read its needs directly. Here,
        only the workspace decides: the behaviour that runs is the one for
        what is broadcast now. With nothing broadcast, the goal held in
        prefrontal working memory carries on (it too was set by a broadcast).
        Habits and reflexes still act without the workspace, as in brains."""
        pos = self.hippo.pos
        grid = self.planning_grid(needs, view)
        cur = self.gw.current
        kind = cur.kind if cur is not None else None
        a = None
        if kind == "self" and cur.target == "unsure where I am":
            a = self._seek_landmarks(grid, pos)
        elif kind == "novel":
            a = self._investigate(view, grid, cur)
        elif kind == "hearing" and cur.target == "gate opened" and self.gate_known:
            py, px = pos
            self.investigate_target = min(self.gate_known, key=lambda c: abs(c[0] - py) + abs(c[1] - px))
            self.investigate_until = self.t + 150
            a = self._investigate(view, grid, None)
        elif kind == "plan" and self.subgoal:
            a = self._pursue_subgoal(grid, pos)
        if a is None and self.pfc.goal in ("food", "water"):
            if self.subgoal is None and not self._directly_reachable(grid, pos, self.pfc.goal):
                a = self._consider_gate_plan(grid, pos, self.pfc.goal)   # the plan competes from next moment
            if a is None:
                a = self.pfc.act(grid, pos, view, needs, self.hippo.last_seen)
            if a is None and self.subgoal is None:
                a = self._consider_gate_plan(grid, pos, self.pfc.goal)
            if a is None and needs.max() > 0.4:
                a = self._try_things(grid, pos)
        elif a is None:
            a = self.pfc.act(grid, pos, view, needs, self.hippo.last_seen)
        habit_a = self.bg.habit(self._ctx["s"])
        return self._release([a, habit_a], view), a

    # ------------------------------------------------------------- learning
    def _learn_contact(self, kind, d):
        self.contact_count[kind] += 1
        if kind == EMPTY:
            self.ground = 0.98 * self.ground + 0.02 * d
        else:
            rel = d - self.ground
            n = self.effect_n[kind] = self.effect_n[kind] + 1
            prev = self.effects.get(kind, np.zeros(3))
            self.effects[kind] = prev + max(1.0 / n, 0.2) * (rel - prev)
            e = self.effects[kind]
            if kind not in INNATE:
                if e[2] < -0.05 and kind not in self.harmful:
                    self.harmful.add(kind)
                    self.learned.append((self.t, f"learned that {NAMES[kind]} hurts it"))
                elif kind in self.harmful and e[2] > -0.02 and n > 10:
                    self.harmful.discard(kind)
                    self.learned.append((self.t, f"learned that {NAMES[kind]} no longer hurts it"))
                if e[0] > 0.1 and e[2] > -0.02 and kind not in self.nourishing:
                    self.nourishing.add(kind)
                    self.learned.append((self.t, f"learned that {NAMES[kind]} feeds it"))
        self.total_contacts = getattr(self, "total_contacts", 0) + 1
        for s in self.heard:
            self.cooccur[(kind, s)] += 1
            self.sound_count = getattr(self, "sound_count", Counter())
            self.sound_count[s] += 1
            key = (kind, s)
            # learned when the sound is far more likely right after touching this
            # kind of thing than after touching anything at all ("lift" >= 10)
            p_after_kind = self.cooccur[key] / self.contact_count[kind]
            p_any = self.sound_count[s] / self.total_contacts
            if key not in self.rules and kind != EMPTY and self.cooccur[key] >= 2 and p_after_kind >= 10 * p_any:
                self.rules[key] = self.t
                effect = {"gate_opened": "opens the gate", "gate_closed": "closes the gate"}.get(s, f"is followed by {s}")
                self.learned.append((self.t, f"learned that stepping on the {NAMES[kind]} {effect}"))

    def _figures_seen(self, view):
        return [self._to_map(vy, vx) for vy, vx in np.argwhere(view == FIGURE)]

    def experience(self, next_view, next_intero, died):
        c = self._ctx
        pos0 = tuple(self.hippo.pos)
        last = super().experience(next_view, next_intero, died)
        self.new_classifications = []
        if self.hippo.lost or "a" not in c:
            self._remember(None, c, next_intero)
            return last
        own = (not self.sleeping and self.agency == "self")
        steady = tuple(self.hippo.pos) == (pos0[0] + ACTIONS[c["a"]][0], pos0[1] + ACTIONS[c["a"]][1]) \
            or tuple(self.hippo.pos) == pos0
        sure = steady and self.hippo.confidence >= 0.9
        if own:
            a, view = c["a"], c["view"]
            dy, dx = ACTIONS[a]
            tgt = int(view[VIEW_R + dy, VIEW_R + dx])
            kind = int(view[VIEW_R, VIEW_R]) if (a == 0 or tgt in (WALL, GATE)) else tgt
            self._learn_contact(kind, next_intero - c["intero"])
            # its own movement, only when it is sure of it (no correction to its
            # belief this moment): otherwise a figure's movement can't be compared
            my_disp = (self.hippo.pos[0] - pos0[0], self.hippo.pos[1] - pos0[1]) if sure else None
            if kind == FOOD and self.multi_step and self.multi_step[-1][1] is not None \
                    and self.multi_step[-1][2] is None and self.t - self.multi_step[-1][1] < 400:
                self.multi_step[-1][2] = self.t       # reached food after opening the gate itself
            if self.anticipating and tuple(self.hippo.pos) in self.anticipating:
                # went where food grew this season before (a let-down, if it was
                # empty, was already counted on sight: _note_letdowns)
                self.anticipations.append((self.t, tuple(self.hippo.pos)))
                self.anticipating = set()
        else:
            my_disp = None
        for res in self.mirror.observe(self.t, my_disp, self._figures_seen(next_view)):
            self.new_classifications.append(res)
            if res["label"] == "self":
                self.pending_self = Content("self", "reflection", 0.7, "self-model", {"n": res["n"]})
                if self.mirror.n_self >= 2 and not self.knows_reflection:
                    self.knows_reflection = True
                    self.learned.append((self.t, "recognized the figure that moves with it as itself"))
        self._remember(kind if own else None, c, next_intero)
        return last

    # ------------------------------------------------------- autobiography
    def autobiography(self):
        ab = getattr(self, "autobio", None)
        if ab is None:
            ab = self.autobio = Autobiography.from_older_mind(self)
        return ab

    def _place(self):
        hp = self.hippo
        if hp.lost or getattr(hp, "confidence", 1.0) < 0.6:
            return None                       # it doesn't know where it is, so it can't remember where
        return tuple(int(v) for v in hp.pos)

    def _remember(self, kind, c, next_intero):
        """What of this moment becomes a memory (see mind/autobiography.py).
        Only what it noticed (reached its workspace) or found out itself."""
        ab = self.autobiography()
        t = self.t
        if self.season is not None:
            ab.new_season(t, self.season)
        place = self._place()
        body = [round(float(v), 2) for v in next_intero]
        prev = c.get("intero")
        ab.place_seen(place)
        lw = self.last or {}
        if lw.get("ignited") and lw.get("broadcast"):
            key = lw["broadcast"]
            report = lw.get("report") or key
            if key not in ab.seen_keys:
                ab.seen_keys.add(key)
                ab.record(t, "attended", "For the first time: " + (report if report[:2] in ("I ", "I'") else report[0].lower() + report[1:]), place, body,
                          importance=0.9, key=key, first=True, goal=self.pfc.goal)
            else:
                ab.record(t, "attended", report, place, body, importance=IMPORTANCE.get(key.split(":")[0], 0.25),
                          key=key, merge=key, goal=self.pfc.goal)
            if key.startswith("surprise:"):
                ab.count("pushes_felt")
        for _, txt in self.learned[ab.n_learned:]:
            ab.record(t, "learned", first_person(txt), place, body, importance=1.0, key="learned")
        ab.n_learned = len(self.learned)
        ms = self.multi_step
        started, opened, done = len(ms), sum(1 for x in ms if x[1] is not None), sum(1 for x in ms if x[2] is not None)
        s0, o0, d0 = ab.ms_seen
        if started > s0:
            ab.record(t, "plan", "What I needed was behind the gate, so I went to open it first.", place, body,
                      importance=0.5, key="plan:start")
        if opened > o0:
            ab.record(t, "plan", "The gate opened.", place, body, importance=0.5, key="plan:opened")
        if done > d0:
            ab.record(t, "plan_done", "I opened the gate myself, then got to the food.", place, body,
                      importance=0.8, key="plan:done")
            ab.count("plans_done")
        ab.ms_seen = (started, opened, done)
        if kind is not None and prev is not None:
            d = next_intero - prev
            if kind == FOOD and d[0] > 0:
                ab.count("meals")
                ab.last_meal_t = t
                if prev[0] < 0.25:
                    ab.record(t, "relief", "I ate at last; I had been very hungry.", place, body, importance=0.5,
                              key="relief:food", merge="relief:food")
            elif kind == WATER and d[1] > 0:
                ab.count("drinks")
                ab.last_drink_t = t
                if prev[1] < 0.25:
                    ab.record(t, "relief", "I drank at last; I had been very thirsty.", place, body, importance=0.5,
                              key="relief:water", merge="relief:water")
            elif kind == DARK and d[2] < -0.02:
                ab.count("sick")
                ab.record(t, "sick", "I ate a dark berry and it made me sick.", place, body, importance=0.8,
                          key="sick", merge="sick")
        if prev is not None and next_intero[2] < prev[2] - 0.05 and kind != DARK:
            ab.count("hurt")
            what = NAMES[kind] if kind is not None else "something"
            ab.record(t, "hurt", f"Something hurt me. I was on {('a ' + what) if what != 'something' else what}.",
                      place, body, importance=0.5, key="hurt", merge="hurt")
        if self.sleeping and not ab.was_sleeping:
            ab.count("sleeps")
        ab.was_sleeping = bool(self.sleeping)
        unsure = self.hippo.lost or getattr(self.hippo, "uncertainty", 0.0) >= 1.5
        if unsure and not ab.was_unsure:
            ab.record(t, "unsure", "I lost track of where I was.", place, body, importance=0.5, key="self:unsure")
        elif ab.was_unsure and not unsure:
            ab.record(t, "unsure", "I worked out where I was again.", place, body, importance=0.4, key="self:found")
        ab.was_unsure = unsure
        for res in self.new_classifications:
            mine = res.get("label") == "self"
            ab.record(t, "mirror", "A figure by the pool moved exactly when I moved. I think it was me." if mine
                      else "A figure by the pool moved on its own. It wasn't me.", place, body, importance=0.7,
                      key="mirror:self" if mine else "mirror:other")
        ab.last_body = body

    def on_came_round(self, intero):
        """Coming round after a collapse. It didn't experience the collapse
        itself, only the gap: it was very low on something, then it was
        coming round, weak."""
        ab = self.autobiography()
        before = ab.last_body
        need = None
        if before is not None:
            i = int(min(range(3), key=lambda k: before[k]))
            need = ["hungry", "thirsty", "hurt"][i]
        text = "I blacked out. When I came round I was weak." + (f" Before it went dark I was very {need}." if need else "")
        ab.count("came_round")
        ab.record(self.t, "came_round", text, self._place(), [round(float(v), 2) for v in intero],
                  importance=0.85, key="came_round", need=need)

    # ------------------------------------------------------------- self-model
    def self_model(self, intero=None):
        sm = super().self_model(intero)
        sm.update({
            "season": self.season,
            "knows_reflection": self.knows_reflection,
            "avoids": [NAMES[k] for k in sorted(self.harmful)],
            "knows_gate_opener": NAMES[self.knows_how_to_open_gate()] if self.knows_how_to_open_gate() is not None else None,
            "subgoal": "open the gate" if self.subgoal else None,
        })
        return sm
