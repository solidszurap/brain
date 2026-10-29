"""
v4 experiments: a mind that learns to act, an imagination, and dreaming.

Q1 (idea 2): how far ahead can its latent world model imagine accurately?
Q2 (idea 3): with my planner removed, does it learn to live from experience?
Q3 (both):   does offline learning help, and does it matter whether the
             offline experience is real (replay) or imagined (dreaming)?

Conditions (all use the same learned controller, only offline learning differs):
  learned_nosleep       never sleeps, learns only from what is happening
  learned_replay        sleeps; sleep = re-learning from real memories
  learned_dream         sleeps; sleep = imagined walks over its place model
  learned_awake_replay  never sleeps; a little replay every waking tick
  learned_awake_dream   never sleeps; a little dreaming every waking tick
References: full (v3, my hand-written planner) and random.

    python experiments_v4.py               # 3 seeds x 10000 ticks, 2 worlds
Writes results/v4.json and results/V4.md
"""
import argparse
import json
import os
from multiprocessing import Pool

import numpy as np

from mind.simulate import simulate

CONDS = ["learned_nosleep", "learned_replay", "learned_dream",
         "learned_awake_replay", "learned_awake_dream", "full", "random"]


def _job(a):
    c, w, s, steps = a
    r = simulate(c, seed=s, steps=steps, world=w)
    return {k: v for k, v in r.items() if k not in ("frames", "layout", "stream", "mind")}


def ms(vals):
    vals = [v for v in vals if v is not None and not (isinstance(v, float) and np.isnan(v))]
    return f"{np.mean(vals):.3f} ± {np.std(vals):.3f}" if vals else "—"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=3)
    ap.add_argument("--steps", type=int, default=10000)
    ap.add_argument("--worlds", default="easy,bushes")
    a = ap.parse_args()
    worlds = a.worlds.split(",")
    jobs = [(c, w, s, a.steps) for w in worlds for c in CONDS for s in range(a.seeds)]
    with Pool(os.cpu_count() or 1) as p:
        runs = p.map(_job, jobs)
    os.makedirs("results", exist_ok=True)
    json.dump({"config": vars(a), "runs": runs}, open("results/v4.json", "w"), default=float)

    L = [f"# v4 results ({a.seeds} seeds x {a.steps} ticks)\n"]
    for w in worlds:
        L.append(f"\n## World: {w}\n")
        L.append("| condition | deaths /1k (2nd half) | homeostatic error (2nd half) | error, first 1k | error, last 1k |")
        L.append("|---|---|---|---|---|")
        for c in CONDS:
            rs = [r for r in runs if r["condition"] == c and r["world"] == w]
            L.append(f"| {c} | {ms([r['deaths_late_per_1k'] for r in rs])} | {ms([r['drive_late'] for r in rs])} | "
                     f"{ms([r['curve_drive'][0] for r in rs])} | {ms([r['curve_drive'][-1] for r in rs])} |")
    imag = [r["imagination"] for r in runs if r.get("imagination")]
    if imag:
        lat = np.mean([i["latent_error"] for i in imag], 0)
        body = np.nanmean([i["body_r2"] for i in imag], 0)
        L.append("\n## Imagination accuracy (all learned runs, end of life)\n")
        L.append("| steps ahead | " + " | ".join(str(k + 1) for k in range(len(lat))) + " |")
        L.append("|---" * (len(lat) + 1) + "|")
        L.append("| latent error (0 perfect, 1 = guessing) | " + " | ".join(f"{v:.2f}" for v in lat) + " |")
        L.append("| body-change R² (1 perfect, 0 = guessing) | " + " | ".join(f"{v:.2f}" for v in body) + " |")
    open("results/V4.md", "w").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
