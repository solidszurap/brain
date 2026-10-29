"""
Ablation experiments: what is each brain part *for*?

Switch one module off at a time, run the same worlds and seeds, and
measure what breaks. A module that changes nothing when removed is
decoration; a module whose removal breaks a specific ability is doing
that job. This is the project's main scientific instrument.

    python experiments.py                 # 5 seeds x 3000 steps, both worlds
    python experiments.py --seeds 2 --steps 1500   # quick
Writes results/results.json and results/RESULTS.md
"""
import argparse
import json
import os
from multiprocessing import Pool

import numpy as np

from mind.simulate import simulate, ABLATIONS, WORLDS

METRICS = [
    ("deaths_per_1k", "Deaths /1k", "lower"),
    ("mean_drive", "Homeostatic error", "lower"),
    ("self_location_acc", "Knows where it is", "higher"),
    ("map_accuracy", "Map accuracy", "higher"),
    ("wm_surprise_late", "World-model surprise (late)", "lower"),
    ("push_detection_auc", "Detects 'not me' (AUC)", "higher"),
    ("metacog_calibration", "Metacog calibration (r)", "higher"),
    ("goal_switches_per_1k", "Goal switches /1k", "lower"),
]


def _job(args):
    cond, world, seed, steps = args
    r = simulate(cond, seed=seed, steps=steps, world=world)
    return {k: (None if isinstance(v, float) and np.isnan(v) else v) for k, v in r.items()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--steps", type=int, default=3000)
    args = ap.parse_args()
    jobs = [(c, w, s, args.steps) for w in WORLDS for c in ABLATIONS for s in range(args.seeds)]
    with Pool(min(len(jobs), os.cpu_count() or 1)) as p:
        runs = p.map(_job, jobs)

    summary = {}
    for w in WORLDS:
        for c in ABLATIONS:
            rs = [r for r in runs if r["condition"] == c and r["world"] == w]
            row = {}
            for k, _, _ in METRICS:
                vals = [r.get(k) for r in rs if r.get(k) is not None]
                if vals:
                    row[k] = {"mean": float(np.mean(vals)), "sd": float(np.std(vals))}
            summary.setdefault(w, {})[c] = row

    os.makedirs("results", exist_ok=True)
    with open("results/results.json", "w") as f:
        json.dump({"seeds": args.seeds, "steps": args.steps, "metrics": METRICS,
                   "summary": summary, "runs": runs}, f, indent=1)

    lines = [f"# Ablation results ({args.seeds} seeds x {args.steps} steps)\n"]
    for w in WORLDS:
        lines.append(f"\n## World: {w}\n")
        lines.append("| condition | " + " | ".join(m[1] for m in METRICS) + " |")
        lines.append("|---" * (len(METRICS) + 1) + "|")
        for c in ABLATIONS:
            row = summary[w][c]
            cells = [f"{row[k]['mean']:.3f} ± {row[k]['sd']:.3f}" if k in row else "—" for k, _, _ in METRICS]
            lines.append(f"| {c} | " + " | ".join(cells) + " |")
    with open("results/RESULTS.md", "w") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
