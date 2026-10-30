"""
The witness: what really happened, kept by the scientist. Ember's mind never
reads this.

Every time Ember forms a memory (mind/autobiography.py), the witness notes
what was actually true at that moment: where it really was, whether
something really pushed it, whether the gate was really open. Later, when
Ember talks about its past, each claim it makes can be checked twice:

  1. Did the words come from its memory at all? (If not: made up, by the
     language cortex.)
  2. Was the memory itself right? (If not: an honest mistake. It believed
     it, the way people sincerely misremember.)

Humans make both kinds of error; telling them apart is the point.

The witness also translates places on Ember's own map into our names for
the regions of its world ("the orchard"). That uses one fixed fact: how its
map lines up with the world (`anchor`, measured once by the observer). The
names describe where Ember *believed* it was; if its belief was wrong, the
name is wrong too, and the witness can see that.
"""
from .wideworld import region_of, SIZE

PLACE_NAMES = {
    "valley": "the valley", "plains": "the plains", "mirror pool": "the still pool",
    "woods": "the woods", "orchard": "the orchard", "marsh": "the marsh",
    "corridor": "the open ground outside the valley",
}

KEEP_EVERY = 5000      # forget the truth about memories Ember itself has forgotten, this often


class Witness:
    def __init__(self, anchor):
        self.anchor = (int(anchor[0]), int(anchor[1]))      # true position - believed position
        self.truth = {}                                    # memory id -> what was true then
        self.last_push_tick = -10 ** 9
        self._pruned_at = 0

    # ------------------------------------------------------------ places
    def region_of_cell(self, cell):
        if cell is None:
            return None
        y, x = int(cell[0]) + self.anchor[0], int(cell[1]) + self.anchor[1]
        if not (0 <= y < SIZE and 0 <= x < SIZE):
            return None
        return region_of((y, x))

    def place_name(self, cell):
        r = self.region_of_cell(cell)
        return PLACE_NAMES.get(r) if r else None

    # ------------------------------------------------------- per moment
    def after_moment(self, life, info):
        """Call once per moment, right after the world and mind have moved."""
        if info.get("pushed"):
            self.last_push_tick = life.ticks
        if info.get("gift"):
            self.gifts_eaten = getattr(self, "gifts_eaten", 0) + 1   # it ate food you left in the light
        ab = getattr(life.mind, "autobio", None)
        if ab is None or not ab.new_ids:
            return
        w = life.world
        fresh = {e["id"]: e for e in list(ab.recent)[-len(ab.new_ids) - 2:]}
        for mid in ab.new_ids:
            ev = fresh.get(mid)
            if ev is None:
                continue
            self.truth[mid] = {
                "tick": int(life.ticks), "true_region": region_of(w.pos), "true_pos": tuple(int(v) for v in w.pos),
                "believed_region": self.region_of_cell(ev.get("place")), "season": w.season,
                "gate_open": bool(w.gate_open), "pushed_recent": life.ticks - self.last_push_tick <= 3,
            }
        ab.new_ids.clear()
        if life.ticks - self._pruned_at >= KEEP_EVERY:
            alive = {e["id"] for e in ab.events()}
            self.truth = {k: v for k, v in self.truth.items() if k in alive}
            self._pruned_at = life.ticks

    # ------------------------------------------------- judging memories
    def _light_truth(self):
        """'I often find food in the light' is true if it has eaten food you left in it."""
        n = getattr(self, "gifts_eaten", 0)
        if n:
            return "true", f"it ate food you left in the light {n} time{'s' if n != 1 else ''}"
        return "unverifiable", "no gift eaten since the witness kept records"

    def memory_truth(self, ev):
        """Was this memory right? -> (status, note). Status is one of
        true | false_belief | unverifiable."""
        if ev["kind"] == "learned":
            txt = ev["text"].lower()
            if "no longer hurt" in txt:
                return "false_belief", "dark berries still hurt it"
            if "dark berr" in txt or "lever opens the gate" in txt:
                return "true", "true of its world"
            if "light feeds" in txt or "food in the light" in txt:
                return self._light_truth()
        tr = self.truth.get(ev["id"])
        if tr is None:
            return "unverifiable", "formed before the witness kept records"
        b, t = tr["believed_region"], tr["true_region"]
        if ev.get("place") is not None and b is not None and b != t:
            return "false_belief", f"it believed it was in {PLACE_NAMES.get(b, b)}; it was in {PLACE_NAMES.get(t, t)}"
        key = ev.get("key") or ""
        if key.startswith("surprise:") and not tr["pushed_recent"]:
            return "false_belief", "nothing had pushed it (a false alarm)"
        if ev["kind"] == "learned":
            return "unverifiable", "not checked"
        if ev["kind"] == "mirror":
            return "unverifiable", "not checked"
        return "true", f"it happened; it was in {PLACE_NAMES.get(t, t)}"

    def item_truth(self, life, item):
        """Truth of one item of what Ember knew when it spoke (mind/voice.py).
        Status: true | false_belief | own_state | unverifiable."""
        w, m = life.world, life.mind
        iid = item["id"]
        if iid == "now:place":
            cell = item.get("cell")
            if cell is None:
                return "own_state", "it said it didn't know where it was"
            b, t = self.region_of_cell(cell), region_of(w.pos)
            if b != t:
                return "false_belief", f"it believed it was in {PLACE_NAMES.get(b, b)}; it was in {PLACE_NAMES.get(t, t)}"
            return "true", f"it was in {PLACE_NAMES.get(t, t)}"
        if iid == "now:gate":
            belief, truth = item.get("belief"), bool(w.gate_open)
            if belief == truth:
                return "true", f"the gate was {'open' if truth else 'shut'}"
            return "false_belief", f"it believed the gate was {'open' if belief else 'shut'}; it was {'open' if truth else 'shut'}"
        if iid == "now:season":
            return ("true", "") if item.get("season") == w.season else ("false_belief", f"it was {w.season}")
        if iid == "now:body":
            return "true", "its body senses are exact"
        if iid.startswith("now:") or iid.startswith("self:"):
            return "own_state", "its own state at that moment"
        if iid.startswith("k:"):
            fact = item.get("fact")
            if fact in ("harmful:dark berry", "rule:lever"):
                return "true", "true of its world"
            if fact == "nourishing:light":
                return self._light_truth()
            if fact == "harmful:none":
                return "own_state", "what it knows"
            return "own_state", "what it knows"
        if iid.startswith("p"):
            return "own_state", "its own summary of a season"
        if iid.startswith("m"):
            ev = item.get("event")
            if ev is None:
                return "unverifiable", ""
            if ev["kind"] in ("voice", "said"):
                return "true", "the conversation happened"
            return self.memory_truth(ev)
        return "unverifiable", ""
