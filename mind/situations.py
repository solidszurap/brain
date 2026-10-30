"""
Hard moments, and running copies of Ember fairly.

Shared by trials.py (many lives per version) and the copy test in
mind/consciousness.py, so both judge Ember on the same kinds of moments.

Why this exists: a copy of Ember that lives 600 ordinary moments, fed and
watered, can't show whether anything in its mind matters. Both copies just
eat. The interesting question is what happens when life is hard: winter
with the gate shut, two needs low at once, ponds drying up, right after
coming round from a collapse. Those are the moments that ask the mind to
combine things.
"""
import numpy as np

from .wideworld import region_of

# name -> (description, test on a life). Order matters: the first match names
# the moment.
SITUATIONS = {
    "came_round":  "just came round from a collapse (the start of a collapse loop)",
    "winter_gate": "winter, hungry, the orchard gate shut",
    "two_needs":   "hungry and thirsty at the same time",
    "dry_thirsty": "summer or autumn (ponds drying), thirsty",
    "plains":      "out on the windy plains (pushes hard to notice)",
    "ordinary":    "nothing pressing: all needs above 60%",
}
HARD = ("came_round", "winter_gate", "two_needs", "dry_thirsty")


def situation(life, info=None):
    """Which situation Ember is in right now (None if it's none of them)."""
    w = life.world
    if w.collapsed:
        return None
    e, h, i = (float(x) for x in w.interoception())
    if info is not None and info.get("came_round"):
        return "came_round"
    if w.season == "winter" and e < 0.4 and not w.gate_open:
        return "winter_gate"
    if e < 0.45 and h < 0.45:
        return "two_needs"
    if w.season in ("summer", "autumn") and h < 0.4:
        return "dry_thirsty"
    if region_of(w.pos) == "plains":
        return "plains"
    if min(e, h, i) > 0.6:
        return "ordinary"
    return None


def is_hard(life, info=None):
    return situation(life, info) in HARD


def reseed(life, seed):
    """Give a copy of Ember its own luck (wind, the mind's random choices)
    without touching anything it has learned. The generators are changed in
    place, so parts of the mind that share one keep sharing it."""
    for k, g in enumerate((life.world.rng, life.mind.rng)):
        g.bit_generator.state = np.random.default_rng([int(seed), k]).bit_generator.state
    visitor = getattr(life, "visitor", None)           # a simulated you: same visits for paired versions
    if visitor is not None:
        visitor.reseed(seed)


def live(life, n):
    """Run a copy of Ember for n moments, quietly, and measure what happened.
    The real Ember is never passed in here; callers pass copies."""
    from .life import step_life
    w, m = life.world, life.mind
    anchor = getattr(getattr(life, "observer", None), "anchor", None)
    c0 = w.collapses
    done0 = sum(1 for x in getattr(m, "multi_step", []) if x[2] is not None)
    drives, lost, out = [], 0, 0
    meals = drinks = 0
    loop_collapses = 0
    last_came_round = None
    awake = 0
    visitor = getattr(life, "visitor", None)
    v0 = (visitor.visits, visitor.reached) if visitor is not None else None
    gifts = 0
    for t in range(n):
        info, last = step_life(life)
        drives.append(m.drives.drive(life.intero))
        gifts += bool(info.get("gift"))
        if info.get("came_round"):
            last_came_round = t
        if info.get("collapse_started") and last_came_round is not None and t - last_came_round <= 150:
            loop_collapses += 1                     # collapsed again soon after coming round
        if last is None:
            out += 1
            continue
        awake += 1
        c = info.get("consumed")
        meals += c == "food"
        drinks += c == "water"
        if anchor is not None:
            hp = m.hippo.pos
            lost += (hp[0] + anchor[0], hp[1] + anchor[1]) != tuple(w.pos)
    return {
        "need_error": round(float(np.mean(drives)), 4),
        "collapses": int(w.collapses - c0),
        "loop_collapses": int(loop_collapses),
        "two_step": int(sum(1 for x in getattr(m, "multi_step", []) if x[2] is not None) - done0),
        "meals": int(meals),
        "drinks": int(drinks),
        "unconscious": round(out / n, 4),
        "lost": round(lost / max(awake, 1), 4) if anchor is not None else None,
        # with a simulated you (mind/visitor.py): gifts eaten, and the share of visits it stepped into the light
        "gifts": int(gifts) if visitor is not None else None,
        "reached": (round((visitor.reached - v0[1]) / (visitor.visits - v0[0]), 4)
                    if visitor is not None and visitor.visits > v0[0] else None),
    }
