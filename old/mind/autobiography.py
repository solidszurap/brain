"""
Ember's autobiographical memory: what it can later remember about its own life.

Built the way human autobiographical memory is usually described (Conway &
Pleydell-Pearce 2000, "the self-memory system"), in three layers:

  periods   one per season it lived through: how that season went, as
            counts and its most important moments ("the winter I blacked
            out three times"). Small, so they are kept for its whole life.
  events    single things that happened to it: what reached its workspace,
            what it found out, blacking out and coming round, being hurt,
            the plans it carried out, voices that spoke to it.
  details   where it believed it was, its body, its goal at that moment.

What gets in follows the global workspace idea: only what was broadcast
(it "noticed" it) or what its own learning produced. Things that happened
to it without reaching the workspace aren't remembered, and things that
happened while it was unconscious can't be. That is a second job for the
workspace: deciding what becomes a memory.

Retention, like ours: recent events are kept in detail; older ones fade
unless they mattered (firsts, findings, blackouts, conversations).
Repeated ordinary moments merge ("I was hungry" x 12).

Everything here is Ember's own view. Places are where it *believed* it was,
on its own map. Whether a memory is true is not known here; the scientist's
side keeps that separately (mind/witness.py) and the mind never reads it.
"""
from collections import Counter, deque

# how much a kind of moment matters for keeping it (0..1); >= KEEP is kept for life
IMPORTANCE = {
    "need": 0.2, "percept": 0.15, "recall": 0.2, "curiosity": 0.1, "surprise": 0.3,
    "threat": 0.4, "novel": 0.5, "hearing": 0.4, "plan": 0.45, "self": 0.55, "voice": 0.7,
}
KEEP = 0.6
RECENT = 1500          # detailed recent events
NOTABLE = 1000         # events kept for life (beyond the recent window)
MERGE_WITHIN = 40      # the same ordinary moment again within this many moments merges


def first_person(text):
    """Its learning log speaks of 'it'; memories are in the first person."""
    t = text.strip()
    for a, b in (("no longer hurts it", "no longer hurts me"), ("hurts it", "hurts me"),
                 ("feeds it", "feeds me"),
                 ("recognized the figure that moves with it as itself",
                  "recognized that the figure that moves with me is me")):
        t = t.replace(a, b)
    t = t.replace("dark berry hurts", "dark berries hurt").replace("dark berry no longer", "dark berries no longer")
    return "I " + t + ("" if t.endswith(".") else ".")


class Autobiography:
    def __init__(self, t0):
        self.started_t = int(t0)
        self.next_id = 1
        self.recent = deque(maxlen=RECENT)
        self.notable = deque(maxlen=NOTABLE)
        self.periods = []                 # closed season gists
        self.cur = None                   # the season it is living through now
        self.season = None
        self.new_ids = deque(maxlen=200)  # for the witness (scientist's side) to note the truth; drained there
        self.seen_keys = set()            # workspace contents it has ever noticed
        self.n_learned = 0
        self.ms_seen = (0, 0, 0)          # gate plans: started, gate opened, food reached
        self.was_sleeping = False
        self.was_unsure = False
        self.last_body = None
        self.last_meal_t = self.last_drink_t = None
        self._tail = deque(maxlen=8)      # last few events, for merging repeats
        self.backfilled = False

    # ---------------------------------------------------------------- writing
    def record(self, t, kind, text, place=None, body=None, importance=0.3, key=None, merge=None, **data):
        """Add a memory. Returns the event, or None if it merged into the last one."""
        if merge is not None:
            for last in reversed(getattr(self, "_tail", [])):
                if last.get("merge") == merge and t - last["t_end"] <= MERGE_WITHIN:
                    last["n"] += 1
                    last["t_end"] = int(t)
                    return None
        ev = {"id": f"m{self.next_id}", "t": int(t), "t_end": int(t), "n": 1, "kind": kind, "text": text,
              "place": tuple(int(v) for v in place) if place is not None else None,
              "body": list(body) if body is not None else None, "importance": float(importance),
              "key": key, "merge": merge, "period": self.cur["index"] if self.cur else None,
              "season": self.season, **data}
        self.next_id += 1
        self.recent.append(ev)
        if importance >= KEEP:
            self.notable.append(ev)
            if self.cur is not None:
                self.cur["notable"].append(ev["id"])
        self.new_ids.append(ev["id"])
        if not hasattr(self, "_tail"):
            self._tail = deque(maxlen=8)
        self._tail.append(ev)
        return ev

    def count(self, what, n=1):
        if self.cur is not None:
            self.cur["counts"][what] += n

    def place_seen(self, place):
        if self.cur is not None and place is not None:
            self.cur["places"][(int(place[0]) // 4, int(place[1]) // 4)] += 1

    def new_season(self, t, season):
        """It senses the season change (like day length for animals)."""
        if season == self.season:
            return
        first = self.cur is None
        if not first:
            self.cur["t_end"] = int(t)
            self.periods.append(self.cur)
        self.season = season
        self.cur = {"id": f"p{len(self.periods) + 1}", "index": len(self.periods), "season": season,
                    "t_start": int(t), "t_end": None, "counts": Counter(), "places": Counter(), "notable": []}
        if not first:
            self.record(t, "season", f"{season.capitalize()} came.", importance=0.6, key=f"season:{season}")

    # ---------------------------------------------------------------- reading
    def events(self):
        """Every memory it still has, oldest first."""
        seen, out = set(), []
        for ev in list(self.notable) + list(self.recent):
            if ev["id"] not in seen:
                seen.add(ev["id"])
                out.append(ev)
        out.sort(key=lambda e: (e["t"], int(e["id"][1:])))
        return out

    def by_id(self):
        d = {e["id"]: e for e in self.events()}
        for p in self.periods + ([self.cur] if self.cur else []):
            d[p["id"]] = p
        return d

    def all_periods(self):
        return self.periods + ([self.cur] if self.cur else [])

    def period_label(self, index, now_index=None):
        """'this winter', 'last winter', 'the winter before last', ... from now."""
        ps = self.all_periods()
        if index is None or not ps:
            return None
        now_index = ps[-1]["index"] if now_index is None else now_index
        season = ps[index]["season"] if index < len(ps) else None
        if index == now_index:
            return f"this {season}"
        same = [p["index"] for p in ps if p["season"] == season and p["index"] < now_index]
        rank = len(same) - same.index(index) if index in same else None
        if rank == 1:
            return f"last {season}"
        if rank == 2:
            return f"the {season} before last"
        if rank is not None:
            return f"a {season} {rank} years ago"
        return season

    # ------------------------------------------------------------- backfill
    @classmethod
    def from_older_mind(cls, mind):
        """Ember lived before it had this memory. What it can still recall of
        that time comes only from its own mind: what it found out, the gate
        plans it carried out, and its last few hundred workspace moments.
        These come back vague: no place, no body, no season. Everything else
        from before is gone, a little like infantile amnesia."""
        ab = cls(t0=getattr(mind, "t", 0))
        ab.backfilled = True
        items = []
        for t, txt in getattr(mind, "learned", []):
            items.append((int(t), "learned", first_person(txt), 1.0, None))
        for ms in getattr(mind, "multi_step", []):
            if ms[2] is not None:
                items.append((int(ms[2]), "plan_done", "I opened the gate myself, then got to the food.", 0.8, None))
        for t, content, report in list(getattr(mind, "stream", [])):
            items.append((int(t), "attended", report or content, IMPORTANCE.get(str(content).split(":")[0], 0.25),
                          str(content)))
        items.sort(key=lambda x: x[0])
        for t, kind, text, imp, key in items:
            if key:
                ab.seen_keys.add(key)
            ab.record(t, kind, text, importance=imp, key=key, merge=key if kind == "attended" else None, vague=True)
        ab.n_learned = len(getattr(mind, "learned", []))
        ms = getattr(mind, "multi_step", [])
        ab.ms_seen = (len(ms), sum(1 for x in ms if x[1] is not None), sum(1 for x in ms if x[2] is not None))
        ab.was_sleeping = bool(getattr(mind, "sleeping", False))
        ab.new_ids.clear()                # nothing to witness: these happened before the witness existed
        ab._tail.clear()
        return ab
