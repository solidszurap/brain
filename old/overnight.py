"""
The overnight experiment: does one night of dreaming change waking behaviour?

Same design as human sleep studies (learn, then sleep or stay awake, then
retest):
  1. A mind lives and learns awake for a while (no sleep).
  2. It is copied three times, at the same moment, in the same world.
  3. Copy A gets no night. Copy B gets a night of *replay* (re-learning from
     real memories). Copy C gets a night of *dreaming* (imagined walks over
     its learned place model, with imagined body states). B and C get exactly
     the same number of learning updates.
  4. All three wake up in identical copies of the world and live on.
     We measure what changed.

    python overnight.py                # 6 seeds, both worlds
    python overnight.py --seeds 2      # quick
Writes results/overnight.json and results/OVERNIGHT.md
"""
import argparse
import copy
import json
import os
from collections import deque
from multiprocessing import Pool

import numpy as np

from mind.world import World, WATER, FOOD, WALL, ACTIONS
from mind.dreamer import DreamingMind
from mind.simulate import WORLDS

NIGHTS = ["no night", "replay night", "dream night"]


def true_distance(world, targets):
    """BFS distance from every cell to the nearest target cell (true world)."""
    H, W = world.grid.shape
    dist = np.full((H, W), 999)
    dq = deque()
    for p in targets:
        dist[p] = 0
        dq.append(p)
    while dq:
        y, x = dq.popleft()
        for dy, dx in ACTIONS[1:]:
            ny, nx = y + dy, x + dx
            if 0 <= ny < H and 0 <= nx < W and world.grid[ny, nx] != WALL and dist[ny, nx] == 999:
                dist[ny, nx] = dist[y, x] + 1
                dq.append((ny, nx))
    return dist


def live(mind, world, steps, learn=True):
    view, intero = world.view(), world.interoception()
    water_dist = true_distance(world, list(zip(*np.where(world.grid == WATER))))
    out = {"deaths": 0, "deaths_hunger": 0, "deaths_thirst": 0, "drive": [], "toward_water": []}
    for _ in range(steps):
        prev = intero.copy()
        pos = world.pos
        a = mind.decide(view, intero)
        info = world.step(a, sleeping=mind.sleeping)
        view, intero = world.view(), world.interoception()
        mind.experience(view, intero, info["died"])
        out["drive"].append(mind.drives.drive(intero))
        if prev[1] < 0.5 and a != 0 and not info["died"] and not info["pushed"] and water_dist[pos] > 0:
            out["toward_water"].append(water_dist[world.pos] < water_dist[pos])
        if info["died"]:
            out["deaths"] += 1
            if prev.argmin() == 0:
                out["deaths_hunger"] += 1
            elif prev.argmin() == 1:
                out["deaths_thirst"] += 1
    return {
        "deaths_per_1k": 1000 * out["deaths"] / steps,
        "hunger_deaths_per_1k": 1000 * out["deaths_hunger"] / steps,
        "thirst_deaths_per_1k": 1000 * out["deaths_thirst"] / steps,
        "mean_drive": float(np.mean(out["drive"])),
        "thirsty_moves_toward_water": float(np.mean(out["toward_water"])) if out["toward_water"] else None,
    }


def run(args):
    world_name, seed, day_steps, night_updates, after_steps = args
    world = World(seed=seed, **WORLDS[world_name])
    mind = DreamingMind(seed=seed, sleep_mode="none", controller="map")
    live(mind, world, day_steps)

    results = {}
    for night in NIGHTS:
        m, w = copy.deepcopy(mind), copy.deepcopy(world)
        m.rng = np.random.default_rng(seed + 777)       # same randomness after waking
        w.rng = np.random.default_rng(seed + 999)
        m.striatum.rng = m.rng
        if night == "replay night":
            m._offline_map(night_updates, "replay")
        elif night == "dream night":
            m._offline_map(night_updates, "dream")
        results[night] = live(m, w, after_steps)
    return {"world": world_name, "seed": seed, "results": results}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=6)
    ap.add_argument("--day", type=int, default=6000)
    ap.add_argument("--night", type=int, default=100000)
    ap.add_argument("--after", type=int, default=3000)
    ap.add_argument("--worlds", default="easy,bushes")
    a = ap.parse_args()
    jobs = [(w, s, a.day, a.night, a.after) for w in a.worlds.split(",") for s in range(a.seeds)]
    with Pool(min(len(jobs), os.cpu_count() or 1)) as p:
        runs = p.map(run, jobs)
    os.makedirs("results", exist_ok=True)
    json.dump({"config": vars(a), "runs": runs}, open("results/overnight.json", "w"), indent=1)

    keys = ["deaths_per_1k", "hunger_deaths_per_1k", "thirst_deaths_per_1k", "mean_drive", "thirsty_moves_toward_water"]
    lines = [f"# Overnight experiment ({a.seeds} seeds; {a.day} ticks awake, a night of {a.night} updates, then {a.after} ticks)\n"]
    for w in a.worlds.split(","):
        lines.append(f"\n## World: {w}\n")
        lines.append("| night | " + " | ".join(keys) + " |")
        lines.append("|---" * (len(keys) + 1) + "|")
        rs = [r for r in runs if r["world"] == w]
        for night in NIGHTS:
            cells = []
            for k in keys:
                vals = [r["results"][night][k] for r in rs if r["results"][night][k] is not None]
                cells.append(f"{np.mean(vals):.3f} ± {np.std(vals):.3f}")
            lines.append(f"| {night} | " + " | ".join(cells) + " |")
    open("results/OVERNIGHT.md", "w").write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
