"""Run a mind in its world and score it on functional markers."""
import numpy as np
from .world import World, FOOD, WALL
from .agent import Mind
from .hippocampus import UNKNOWN

ABLATIONS = {
    "full": {},
    "no_workspace": {"workspace": False},
    "no_hippocampus": {"hippocampus": False},
    "no_self_other": {"self_other": False},
    "no_sleep": {"sleep": False},
    "no_metacognition": {"metacognition": False},
    "random": {"random": True},
}

# v4: learned controller; the only difference between them is what sleep does
DREAM_CONDITIONS = {
    "learned_nosleep": {"learned": "none"},
    "learned_replay": {"learned": "replay"},
    "learned_dream": {"learned": "dream"},
    "learned_both": {"learned": "both"},
    "learned_awake_replay": {"learned": "awake_replay"},
    "learned_awake_dream": {"learned": "awake_dream"},
    # the first attempt: value network on the latent state, dreams in latent space
    "neural_replay": {"learned": "replay", "controller": "neural"},
    "neural_dream": {"learned": "dream", "controller": "neural"},
}
CONDITIONS = {**ABLATIONS, **DREAM_CONDITIONS}


def _auc(scores, labels):
    scores, labels = np.asarray(scores), np.asarray(labels, bool)
    pos, neg = scores[labels], scores[~labels]
    if len(pos) == 0 or len(neg) == 0:
        return float("nan")
    order = np.argsort(np.concatenate([pos, neg]))
    ranks = np.empty(len(order))
    ranks[order] = np.arange(1, len(order) + 1)
    return float((ranks[:len(pos)].sum() - len(pos) * (len(pos) + 1) / 2) / (len(pos) * len(neg)))


def map_accuracy(mind, world, anchor):
    """Fraction of remembered static cells that are actually right,
    using the alignment between the agent's frame and the world."""
    if anchor is None:
        return float("nan")
    oy, ox = anchor
    m = mind.hippo.map
    ys, xs = np.where((m == WALL) | (m == 3) | (m == 4))
    ok = n = 0
    for y, x in zip(ys, xs):
        wy, wx = y + oy, x + ox
        truth = world.grid[wy, wx] if (0 <= wy < world.H and 0 <= wx < world.W) else WALL
        ok += truth == m[y, x]
        n += 1
    return ok / n if n else float("nan")


WORLDS = {
    "easy": {},
    "harsh": {"n_food": 3, "drain": 1.6, "wind_prob": 0.08},
    # same as easy, but food regrows only at 10 fixed bushes: the world has
    # structure that memory and imagination can exploit
    "bushes": {"bushes": 10},
}


def simulate(condition="full", seed=0, steps=4000, trace=False, world="easy"):
    cfg = dict(CONDITIONS[condition])
    world_name = world
    world = World(seed=seed, **WORLDS[world_name])
    if "learned" in cfg:
        from .dreamer import DreamingMind
        mode = cfg.pop("learned")
        ctrl = cfg.pop("controller", "map")
        mind = DreamingMind(seed=seed, sleep_mode=mode, controller=ctrl, **cfg)
    else:
        mind = Mind(seed=seed, **cfg)
    death_ticks = []
    view, intero = world.view(), world.interoception()
    drive_trace, surpr, z_scores, pushed, located = [], [], [], [], []
    anchor = None
    map_resets_seen = 0
    frames = []
    died = False
    for t in range(steps):
        a = mind.decide(view, intero)
        info = world.step(a, sleeping=mind.sleeping)
        view, intero = world.view(), world.interoception()
        last = mind.experience(view, intero, info["died"])
        drive_trace.append(mind.drives.drive(intero))
        if info["died"]:
            death_ticks.append(t)
        if cfg.get("random"):
            continue
        # alignment between the agent's own frame and the world's frame
        if mind.hippo.map_resets != map_resets_seen:
            map_resets_seen, anchor = mind.hippo.map_resets, None
        if not mind.hippo.lost:
            off = (info["true_pos"][0] - mind.hippo.pos[0], info["true_pos"][1] - mind.hippo.pos[1])
            if anchor is None:
                anchor = off
            located.append(off == anchor)
        if not info["died"]:
            surpr.append(last["surprise"])
            z_scores.append(last["z"])
            pushed.append(info["pushed"])
        if trace:
            frames.append({
                "t": t, "pos": list(info["true_pos"]),
                "belief": None if mind.hippo.lost else [int(mind.hippo.pos[0]), int(mind.hippo.pos[1])],
                "anchor": list(anchor) if anchor else None,
                "body": [round(float(v), 3) for v in intero],
                "food": [list(map(int, p)) for p in np.argwhere(world.grid == FOOD)],
                "a": int(a), "pushed": info["pushed"], "died": info["died"],
                "consumed": info["consumed"],
                "broadcast": last.get("broadcast"), "ignited": last.get("ignited"),
                "report": last.get("report"), "goal": last.get("goal"),
                "sleeping": last.get("sleeping") or mind.sleeping,
                "surprise": last.get("surprise"), "expected": last.get("expected"),
                "z": last.get("z"), "external": last.get("external"),
                "valence": round(mind.drives.valence, 3),
            })
            if t % 20 == 0:
                frames[-1]["map"] = mind.hippo.map.tolist()

    n = len(surpr)
    k = min(400, n // 4) or 1
    res = {
        "condition": condition, "world": world_name, "seed": seed, "steps": steps,
        "deaths_per_1k": 1000 * world.deaths / steps,
        "mean_drive": float(np.mean(drive_trace)),
        "deaths_late_per_1k": 1000 * sum(d >= steps // 2 for d in death_ticks) / (steps - steps // 2),
        "drive_late": float(np.mean(drive_trace[steps // 2:])),
        "curve_drive": [float(np.mean(drive_trace[k:k + 1000])) for k in range(0, steps, 1000)],
        "curve_deaths": [sum(k <= d < k + 1000 for d in death_ticks) for k in range(0, steps, 1000)],
    }
    if hasattr(mind, "wm"):
        from .dreamer import imagination_accuracy
        acc = imagination_accuracy(mind)
        res["imagination"] = acc
        res["sleeps"] = mind.sleeps
        res["dream_eat_events"] = sum(d["eat_events"] for d in mind.dream_stats)
    if not cfg.get("random"):
        res.update({
            "wm_surprise_early": float(np.mean(surpr[:k])),
            "wm_surprise_late": float(np.mean(surpr[-k:])),
            "push_detection_auc": _auc(z_scores[n // 2:], pushed[n // 2:]),
            "metacog_calibration": mind.meta.calibration(1500),
            "self_location_acc": float(np.mean(located)) if located else float("nan"),
            "map_accuracy": map_accuracy(mind, world, anchor),
            "ignitions_per_1k": 1000 * mind.gw.ignitions / steps,
            "goal_switches_per_1k": 1000 * mind.pfc.goal_switches / steps,
            "sleeps": mind.sleeps,
            "map_resets": mind.hippo.map_resets,
        })
    if trace:
        res["frames"] = frames
        res["layout"] = world.grid.tolist()
        res["stream"] = list(mind.stream)[-200:]
        res["mind"] = mind
    return res
