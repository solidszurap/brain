"""
Does the dreaming mechanism itself work, in isolation?

A mind lives awake for 5000 ticks. Then we take its learned place model and
give a *fresh* value system nothing but dreams (no real experience at all).
Question: after dreaming, when thirsty, does its first step at each known
place lead toward water? Compared with the awake-trained values.

    python dream_mechanism.py
"""
from collections import deque
from multiprocessing import Pool

import numpy as np

from mind.world import World, WATER, ACTIONS
from mind.dreamer import DreamingMind
from mind.striatum import Striatum, map_dream
from mind.hippocampus import UNKNOWN
from overnight import live


def toward_water(Q, place_model, own_map, water):
    """Fraction of known places where the thirsty-greedy action shortens the
    route to water, measured on the mind's own map."""
    H = own_map.shape[0]
    dist = {p: 0 for p in water}
    dq = deque(water)
    while dq:
        y, x = dq.popleft()
        for dy, dx in ACTIONS[1:]:
            q = (y + dy, x + dx)
            if 0 <= q[0] < H and 0 <= q[1] < H and own_map[q] not in (UNKNOWN, 1) and q not in dist:
                dist[q] = dist[(y, x)] + 1
                dq.append(q)
    ok = n = 0
    for p, d in dist.items():
        if d == 0 or d > 8 or place_model.N[p].sum() == 0:
            continue
        a = int(np.argmax(Q[p[0], p[1], 1]))  # context 1 = thirsty
        q = (p[0] + ACTIONS[a][0], p[1] + ACTIONS[a][1])
        ok += dist.get(q, 99) < d
        n += 1
    return ok / n if n else float("nan")


def run(seed):
    world = World(seed=seed)
    mind = DreamingMind(seed=seed, sleep_mode="none")
    live(mind, world, 5000)
    water = [tuple(p) for p in mind.hippo.known(WATER)]
    starts = list({e[0] for e in mind.real if e[0] is not None})
    out = {"awake-trained": toward_water(mind.striatum.Q, mind.place_model, mind.hippo.map, water)}
    for n in (20000, 200000):
        fresh = Striatum(mind.hippo.size, np.random.default_rng(seed), n_view=125)
        map_dream(mind.place_model, fresh, starts, np.random.default_rng(seed + 1), n)
        out[f"dreams only ({n // 1000}k)"] = toward_water(fresh.Q, mind.place_model, mind.hippo.map, water)
    return out


if __name__ == "__main__":
    with Pool(2) as p:
        res = p.map(run, range(4))
    print("Thirsty first step leads toward water (chance is about 0.3-0.4):")
    for k in res[0]:
        v = [r[k] for r in res]
        print(f"  {k:22s} {np.mean(v):.2f} ± {np.std(v):.2f}")
