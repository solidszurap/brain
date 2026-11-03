"""
Run one mind, print its stream of consciousness, save a replay for the viewer.

    python run.py                          # full mind, easy world, 1500 steps
    python run.py --world harsh --condition no_self_other
    MIND_LLM=1 ANTHROPIC_API_KEY=... python run.py --ask "Why did you turn back?"

Then open viewer.html (serve the folder: python -m http.server 8000).
"""
import argparse
import json
import os

import numpy as np

from mind.simulate import simulate, ABLATIONS, WORLDS
from mind.world import FOOD, EMPTY


def export(res, path):
    """Compact replay file: static layout + one small record per tick.
    The agent's map snapshots are cropped to the area it ever knew."""
    frames = res["frames"]
    layout = np.array(res["layout"])
    layout[layout == FOOD] = EMPTY
    snaps = [(i, np.array(f["map"])) for i, f in enumerate(frames) if "map" in f]
    known = np.zeros_like(snaps[0][1], dtype=bool)
    for _, m in snaps:
        known |= m >= 0
    ys, xs = np.where(known) if known.any() else (np.array([24]), np.array([24]))
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    char = {-1: ".", 0: "0", 1: "1", 2: "2", 3: "3", 4: "4"}
    out_frames = []
    for f in frames:
        g = dict(f)
        if "map" in g:
            m = np.array(g.pop("map"))[y0:y1, x0:x1]
            g["map"] = ["".join(char[int(v)] for v in row) for row in m]
        out_frames.append(g)
    meta = {k: v for k, v in res.items() if k not in ("frames", "layout", "stream", "mind")}
    data = {"meta": meta, "layout": layout.tolist(), "map_origin": [int(y0), int(x0)],
            "frames": out_frames}
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w") as fh:
        json.dump(data, fh, separators=(",", ":"), default=lambda o: o.item() if hasattr(o, "item") else str(o))
    return data


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--condition", default="full", choices=list(ABLATIONS))
    ap.add_argument("--world", default="easy", choices=list(WORLDS))
    ap.add_argument("--steps", type=int, default=1500)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", default="runs/latest.json")
    ap.add_argument("--ask", default="What have you been doing, and why?")
    args = ap.parse_args()

    res = simulate(args.condition, seed=args.seed, steps=args.steps, trace=True, world=args.world)
    mind = res["mind"]
    print("== stream of consciousness (last 25 ignitions) ==")
    for t, content, report in res["stream"][-25:]:
        print(f"  t={t:5d}  [{content:18s}] {report}")
    print("\n== scores ==")
    for k, v in res.items():
        if k not in ("frames", "layout", "stream", "mind"):
            print(f"  {k:22s} {v}")
    print("\n== self-model ==")
    print(json.dumps(mind.self_model(), indent=2, default=str))
    print(f"\nQ: {args.ask}\nA: {mind.ask(args.ask)}")
    export(res, args.out)
    print(f"\nReplay saved to {args.out}; open viewer.html to watch it.")


if __name__ == "__main__":
    main()
