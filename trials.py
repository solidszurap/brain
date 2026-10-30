"""
Many lives per version: the fair way to judge a change to Ember's mind.

One life proves little. A small change once moved a single run from 11 to 42
collapses. So instead of one run, this takes Ember's real saved life, finds
the hard moments in it (winter with the gate shut, two needs low, ponds drying,
just after coming round from a collapse), and starts many copies from each:
every version gets the same starting moments and the same seeds, so the
comparison is paired. The result is a mean, a spread, and a verdict that only
says "better" when the 95% interval of the difference is clear of zero.

The real Ember is never touched: everything runs on copies.

    python trials.py bank                         # find hard moments in Ember's saved life
    python trials.py                              # baseline vs no_workspace
    python trials.py baseline no_workspace --seeds 8 --moments 1500   # slower, tighter
    python trials.py baseline broadcast broadcast_no_workspace       # 3 versions: every pair compared
    python trials.py --list                       # the versions you can compare
    python trials.py --quick                      # 2 seeds x 600 moments, for a first look

Adding a version: write a function that changes a copy of Ember in place and
add it to VERSIONS below. Nothing else needs to change.
"""
import argparse
import copy
import gzip
import json
import os
import pickle
import sys
import time
from datetime import datetime
from multiprocessing import Pool

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from mind.situations import SITUATIONS, HARD, situation, reseed, live   # noqa: E402

LIFE_FILE = os.path.join(HERE, "ember_state", "life.pkl.gz")
BANK_DIR = os.path.join(HERE, "trials", "bank")
OUT_DIR = os.path.join(HERE, "results", "trials")


# ------------------------------------------------------------------ versions
def _baseline(life):
    pass


def _no_workspace(life):
    life.mind.gw.enabled = False


def _broadcast(life):
    """Experimental: the workspace alone decides which behaviour runs (no
    hand-written priority order). See EmberMind._choose_by_broadcast."""
    life.mind.wiring = "broadcast"


def _broadcast_no_workspace(life):
    """The broadcast wiring, with the workspace's threshold and persistence
    removed: whatever is strongest this instant runs."""
    life.mind.wiring = "broadcast"
    life.mind.gw.enabled = False


def _old_senses(life):
    """Its eyes as they were before the light existed: 9 kinds of things, not
    10 (see grow_senses in mind/life.py). Only safe in a world with no light."""
    life.mind.old_senses = True


def _visitor(life):
    """A simulated you (mind/visitor.py) appears as a light 1-2 cells from
    Ember every 300 moments, leaves food in it and stays 150. Ember already
    knows it often finds food in the light (planted, so the comparison tests
    what it does with that, not how fast it learns it)."""
    from mind.visitor import Visitor
    from mind.wideworld import LIGHT
    life.visitor = Visitor(seed=0, every=300, stay=150)    # reseeded with each life's seed
    life.mind.nourishing.add(LIGHT)


VERSIONS = {
    "baseline":     ("Ember as it is now", _baseline),
    "visitor":      ("a simulated you visits as a light and leaves food; Ember knows the light often holds food", _visitor),
    "old_senses":   ("its eyes before the light existed: 9 kinds of things instead of 10", _old_senses),
    "no_workspace": ("workspace without threshold or persistence: the strongest signal of each instant wins at once", _no_workspace),
    "broadcast":    ("experimental wiring: only what the workspace broadcasts decides which behaviour runs", _broadcast),
    "broadcast_no_workspace": ("broadcast wiring, workspace without threshold or persistence", _broadcast_no_workspace),
}

# lower is better for these; higher is better for two_step
LOWER_BETTER = ["need_error", "collapses", "loop_collapses", "lost", "unconscious"]
HIGHER_BETTER = ["two_step", "gifts", "reached"]
SHOWN = ["need_error", "collapses", "loop_collapses", "two_step", "meals", "drinks", "lost", "unconscious",
         "gifts", "reached"]


# ---------------------------------------------------------------------- bank
def _save(obj, path):
    tmp = path + ".tmp"
    with gzip.open(tmp, "wb", compresslevel=6) as f:
        pickle.dump(obj, f, protocol=pickle.HIGHEST_PROTOCOL)
    os.replace(tmp, path)


def _load(path):
    with gzip.open(path, "rb") as f:
        return pickle.load(f)


def build_bank(per=2, spacing=1500, gap=300, max_moments=24000, seed=2026):
    """Live a copy of Ember forward (its own luck, seed fixed) and keep a
    snapshot the first `per` times each situation comes up: at least
    `spacing` moments apart within a situation, and at least `gap` moments
    after any other snapshot (so two starts aren't really the same moment).
    Also keeps the saved life itself as 'now'."""
    from mind.life import step_life
    print(f"Loading Ember's saved life from {os.path.relpath(LIFE_FILE, HERE)} ...")
    src = _load(LIFE_FILE)
    os.makedirs(BANK_DIR, exist_ok=True)
    for f in os.listdir(BANK_DIR):
        if f.endswith(".pkl.gz"):
            os.remove(os.path.join(BANK_DIR, f))
    index = {"built": datetime.now().astimezone().isoformat(timespec="seconds"),
             "source_tick": int(src.ticks), "source_mtime": os.path.getmtime(LIFE_FILE),
             "seed": seed, "snapshots": []}

    def keep(life, name, k, at):
        fn = f"{name}_{k}.pkl.gz"
        _save(life, os.path.join(BANK_DIR, fn))
        w = life.world
        index["snapshots"].append({"file": fn, "situation": name, "moment": int(life.ticks),
                                   "forward": int(at), "season": w.season,
                                   "body": [round(float(x), 2) for x in w.interoception()]})
        print(f"  {name:12s} at moment {life.ticks:,} ({w.season}, body "
              f"{[round(float(x), 2) for x in w.interoception()]})")

    keep(src, "now", 0, 0)
    life = copy.deepcopy(src)
    reseed(life, seed)
    count = {s: 0 for s in SITUATIONS}
    last = {s: -10 ** 9 for s in SITUATIONS}
    last_any = 0                                  # the saved life itself was kept at 0
    t0 = time.time()
    for t in range(1, max_moments + 1):
        info, _ = step_life(life)
        life.ticks += 1
        s = situation(life, info)
        if s and count[s] < per and t - last[s] >= spacing and t - last_any >= gap:
            keep(copy.deepcopy(life), s, count[s], t)
            count[s] += 1
            last[s] = last_any = t
        if all(c >= per for c in count.values()):
            break
    missing = [s for s, c in count.items() if c < per]
    if missing:
        print(f"  not found (enough times) in {t:,} moments: {', '.join(missing)}")
    with open(os.path.join(BANK_DIR, "index.json"), "w") as f:
        json.dump(index, f, indent=1)
    print(f"Bank: {len(index['snapshots'])} starting moments in {time.time() - t0:.0f} s, "
          f"in {os.path.relpath(BANK_DIR, HERE)}")
    return index


def load_index():
    p = os.path.join(BANK_DIR, "index.json")
    if not os.path.exists(p):
        return None
    with open(p) as f:
        return json.load(f)


# --------------------------------------------------------------------- trials
_cache = {}


def _one(task):
    version, fn, seed, moments = task
    if fn not in _cache:
        _cache.clear()
        _cache[fn] = _load(os.path.join(BANK_DIR, fn))
    life = copy.deepcopy(_cache[fn])
    VERSIONS[version][1](life)
    reseed(life, seed)
    r = live(life, moments)
    return {"version": version, "file": fn, "seed": seed, **r}


def run_trials(versions, seeds, moments, workers, situations=None):
    index = load_index()
    snaps = [s for s in index["snapshots"] if situations is None or s["situation"] in situations]
    tasks = [(v, s["file"], 1000 + k, moments) for s in snaps for k in range(seeds) for v in versions]
    tasks.sort(key=lambda x: x[1])          # same snapshot together, so workers load it once
    n = len(tasks)
    print(f"{n} lives of {moments:,} moments ({len(snaps)} starting moments x {seeds} seeds x "
          f"{len(versions)} versions) on {workers} worker(s) ...")
    t0, out = time.time(), []
    with Pool(workers) as pool:
        for i, r in enumerate(pool.imap_unordered(_one, tasks, chunksize=2), 1):
            out.append(r)
            if i % max(1, n // 20) == 0 or i == n:
                el = time.time() - t0
                print(f"  {i}/{n} lives, {el:.0f} s (about {el / i * (n - i):.0f} s left)", flush=True)
    sit = {s["file"]: s["situation"] for s in snaps}
    for r in out:
        r["situation"] = sit[r["file"]]
    return out, index


# ------------------------------------------------------------------- analysis
def _boot_ci(d, clusters, rng, n=4000):
    """95% interval for the mean difference, resampling in two levels:
    starting moments first, then lives within each. Lives started from the
    same moment are not independent (they share everything Ember knew at that
    moment), so treating them as independent would claim too much."""
    d = np.asarray(d, float)
    if len(d) < 2 or np.all(d == d[0]):
        return float(d.mean()), float(d.mean())
    groups = [d[np.asarray(clusters) == c] for c in sorted(set(clusters))]
    means = np.empty(n)
    for i in range(n):
        pick = rng.integers(0, len(groups), len(groups))
        means[i] = np.mean([g[rng.integers(0, len(g), len(g))].mean() for g in (groups[j] for j in pick)])
    return float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def compare(results, a, b):
    """Paired comparison of version b against a, per situation and over all
    hard moments. Pairs are (same starting moment, same seed)."""
    rng = np.random.default_rng(0)
    by = {}
    for r in results:
        by.setdefault((r["file"], r["seed"]), {})[r["version"]] = r
    pairs = [(p[a], p[b]) for p in by.values() if a in p and b in p]
    groups = {}
    for ra, rb in pairs:
        groups.setdefault(ra["situation"], []).append((ra, rb))
        if ra["situation"] in HARD:
            groups.setdefault("ALL HARD", []).append((ra, rb))
        groups.setdefault("ALL", []).append((ra, rb))
    table = {}
    for g, ps in groups.items():
        row = {"n": len(ps), "starts": len({x["file"] for x, _ in ps})}
        for m in SHOWN:
            ok = [(x, y) for x, y in ps if x[m] is not None and y[m] is not None]
            if not ok:
                continue
            va = [x[m] for x, _ in ok]
            vb = [y[m] for _, y in ok]
            d = [y[m] - x[m] for x, y in ok]
            lo, hi = _boot_ci(d, [x["file"] for x, _ in ok], rng)
            verdict = ""
            if m in LOWER_BETTER or m in HIGHER_BETTER:
                verdict = "can't tell"
                sign = -1 if m in LOWER_BETTER else 1      # +: b is better
                if lo > 0 or hi < 0:
                    verdict = f"{b} better" if sign * (lo + hi) > 0 else f"{a} better"
            row[m] = {"a_mean": float(np.mean(va)), "a_sd": float(np.std(va)),
                      "b_mean": float(np.mean(vb)), "b_sd": float(np.std(vb)),
                      "diff": float(np.mean(d)), "ci": [lo, hi], "verdict": verdict}
        table[g] = row
    return table


def _fmt(x, m):
    if m in ("need_error", "lost", "unconscious", "reached"):
        return f"{x:.3f}"
    return f"{x:.2f}"


def report(table, a, b, seeds, moments, index):
    order = [s for s in ["now"] + list(SITUATIONS) if s in table] + [g for g in ("ALL HARD", "ALL") if g in table]
    L = [f"# {b} vs {a}", "",
         f"{datetime.now().astimezone().isoformat(timespec='seconds')}. "
         f"Ember's saved life at moment {index['source_tick']:,}; starting moments found by living a copy forward "
         f"(bank built {index['built']}). Each starting moment x {seeds} seeds x {moments:,} moments, "
         f"both versions with the same seeds (paired).", "",
         f"- **{a}**: {VERSIONS.get(a, ('no longer in trials.py',))[0]}",
         f"- **{b}**: {VERSIONS.get(b, ('no longer in trials.py',))[0]}", "",
         "Numbers: mean ± spread (sd) across lives. Diff = " + b + " − " + a +
         ", with a 95% bootstrap interval that resamples starting moments, then lives within them "
         "(lives from the same moment aren't independent). With only 1-2 starting moments in a "
         "situation the interval is honest but wide. A verdict says \"better\" only when the interval "
         "is clear of zero; otherwise \"can't tell\".", "",
         "Lower is better: need-error (how far its needs are from satisfied, averaged), collapses, "
         "loop collapses (collapsed again within 150 moments of coming round), lost (wrong about where it is), "
         "unconscious (share of moments). Higher is better: two-step plans (opened the gate, then ate); "
         "with a visitor, gifts (food you left in the light, eaten) and reached (share of visits it "
         "stepped into the light).", ""]
    for g in order:
        row = table[g]
        title = g if g in ("ALL HARD", "ALL") else f"{g}: {SITUATIONS.get(g, 'the saved life itself, as it is')}"
        L += [f"## {title} ({row['n']} pairs from {row.get('starts', '?')} starting moments)", "", f"| | {a} | {b} | diff | 95% interval | verdict |",
              "|---|---|---|---|---|---|"]
        for m in SHOWN:
            if m not in row:
                continue
            c = row[m]
            L.append(f"| {m} | {_fmt(c['a_mean'], m)} ± {_fmt(c['a_sd'], m)} | {_fmt(c['b_mean'], m)} ± "
                     f"{_fmt(c['b_sd'], m)} | {c['diff']:+.3f} | [{c['ci'][0]:+.3f}, {c['ci'][1]:+.3f}] | "
                     f"{c['verdict']} |")
        L.append("")
    return "\n".join(L)


# ------------------------------------------------------------------------ main
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("what", nargs="*", help="'bank', or two version names to compare (default: baseline no_workspace)")
    ap.add_argument("--seeds", type=int, default=4, help="lives per starting moment per version (default 4)")
    ap.add_argument("--moments", type=int, default=1000, help="how long each life runs (default 1000)")
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    ap.add_argument("--only", nargs="*", help="only these situations, e.g. --only winter_gate came_round")
    ap.add_argument("--per", type=int, default=2, help="bank: starting moments per situation (default 2)")
    ap.add_argument("--quick", action="store_true", help="2 seeds x 600 moments, for a first look")
    ap.add_argument("--list", action="store_true", help="list versions and situations")
    ap.add_argument("--reanalyze", metavar="JSON", help="redo the tables from a saved results .json (no new lives)")
    args = ap.parse_args()

    if args.list:
        print("Versions:")
        for k, (d, _) in VERSIONS.items():
            print(f"  {k:14s} {d}")
        print("Situations:")
        for k, d in SITUATIONS.items():
            print(f"  {k:12s} {d}{'  (hard)' if k in HARD else ''}")
        return

    if args.reanalyze:
        with open(args.reanalyze) as f:
            saved = json.load(f)
        table = compare(saved["lives"], saved["a"], saved["b"])
        md = report(table, saved["a"], saved["b"], saved["seeds"], saved["moments"], saved["bank"])
        saved["table"] = table
        with open(args.reanalyze, "w") as f:
            json.dump(saved, f, indent=1)
        with open(args.reanalyze[:-5] + ".md", "w", encoding="utf-8") as f:
            f.write(md)
        print(md)
        return

    if args.what[:1] == ["bank"]:
        build_bank(per=args.per)
        return

    versions = args.what if len(args.what) >= 2 else (["baseline"] + args.what if args.what else ["baseline", "no_workspace"])
    for v in versions:
        if v not in VERSIONS:
            sys.exit(f"Unknown version '{v}'. Known: {', '.join(VERSIONS)}")
    if args.quick:
        args.seeds, args.moments = 2, 600

    index = load_index()
    if index is None or index["source_mtime"] < os.path.getmtime(LIFE_FILE) - 3600 * 24:
        print("No bank of starting moments yet (or it's more than a day older than Ember's life). Building it.")
        index = build_bank(per=args.per)

    # every version lives once; then each pair is compared (later vs earlier)
    results, index = run_trials(versions, args.seeds, args.moments, args.workers, args.only)
    os.makedirs(OUT_DIR, exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%d_%H%M")
    for i, a in enumerate(versions):
        for b in versions[i + 1:]:
            mine = [r for r in results if r["version"] in (a, b)]
            table = compare(mine, a, b)
            md = report(table, a, b, args.seeds, args.moments, index)
            base = os.path.join(OUT_DIR, f"{stamp}_{b}_vs_{a}")
            with open(base + ".md", "w", encoding="utf-8") as f:
                f.write(md)
            with open(base + ".json", "w") as f:
                json.dump({"a": a, "b": b, "seeds": args.seeds, "moments": args.moments, "table": table,
                           "lives": mine, "bank": index}, f, indent=1)
            print()
            print(md)
            print(f"Saved {os.path.relpath(base, HERE)}.md and .json")


if __name__ == "__main__":
    main()
