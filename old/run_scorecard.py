#!/usr/bin/env python3
"""Scorecard: measured properties with fixed pass/fail rules. Run: python run_scorecard.py

READ THIS FIRST: this runs on SYNTHETIC data. It tests that the measurement
machinery works (including a negative control). It says nothing about
consciousness, and nothing about real-world skill until you swap in CSVWorld.
"""
import json
import os
import tempfile

from wholebrain.brain import Agent, PRIMARY_H
from wholebrain.ledger import Ledger
from wholebrain.world import NoiseWorld, SeasonalWorld

N = 3000


def run(agent, world, n):
    for _ in range(n):
        agent.tick(world.step())


def trained(world_cls, effects=True, n=N, seed=1):
    w = world_cls(seed=seed)
    led = Ledger()
    a = Agent(led, w.name, w.synthetic, effects)
    run(a, w, n)
    return a, led, w


def intervention(agent, var, value, trials=40, gap=25):
    """do(var=value) on a CLONE, then check the self-model's prediction against what happens."""
    hits = prev = mode = 0
    for _ in range(trials):
        for _ in range(gap):                       # let the real agent live between trials
            agent.tick(agent.hist[-1])
        base = agent.to_state()
        clone = Agent.from_state(base, ledger=Ledger(), source=agent.source, synthetic=agent.synthetic)
        setattr(clone.home, var, value)
        pw = clone.predict_winner()
        actual = clone.tick(clone.hist[-1])["winner"]
        hits += pw == actual
        prev += base["prev_winner"] == actual
        mode += max(base["winner_counts"], key=base["winner_counts"].get) == actual
    return hits / trials, max(prev, mode) / trials


def main():
    rows = []

    def check(name, value, rule, ok):
        rows.append((name, value, rule, "PASS" if ok else "FAIL"))

    a, led, _ = trained(SeasonalWorld)
    s = led.score(PRIMARY_H)
    check("world skill, structured world", "%.3f" % s["skill"], "> 0.05 vs best of 3 baselines", s["skill"] > 0.05)
    _, nled, _ = trained(NoiseWorld)
    ns = nled.score(PRIMARY_H)
    check("world skill, NOISE control", "%.3f" % ns["skill"], "< 0.05 (no fake edge)", ns["skill"] < 0.05)

    se = led.score_self_error(PRIMARY_H)
    check("self error-prediction skill", "%.3f" % se["skill"], "> 0 vs running-mean baseline", se["skill"] > 0)

    st = a.selfstats
    acc, pacc, macc = st["model"] / st["n"], st["prev"] / st["n"], st["mode"] / st["n"]
    check("self winner-prediction", "%.2f (prev %.2f, mode %.2f)" % (acc, pacc, macc),
          "model > both baselines", acc > max(pacc, macc))

    w2 = SeasonalWorld(seed=1)
    for hv in [("hunger", 1.0), ("energy", 0.1)]:
        acc_i, base_i = intervention(a, hv[0], hv[1])
        check("intervention do(%s=%.1f)" % hv, "%.2f (best baseline %.2f)" % (acc_i, base_i),
              "self-model beats baselines by >= 0.30", acc_i - base_i >= 0.30)

    wins = a.winner_counts
    tot = sum(wins.values())
    check("workspace ignition", ", ".join("%s %.0f%%" % (k, 100 * v / tot) for k, v in sorted(wins.items())),
          "idle < 50% and >= 3 specialists win", wins.get("idle", 0) / tot < 0.5 and len([k for k in wins if k != "idle"]) >= 3)

    ab, abled, _ = trained(SeasonalWorld, effects=False)
    d = led.score(PRIMARY_H)["skill"] - abled.score(PRIMARY_H)["skill"]
    check("ablation: broadcast effects off", "skill delta %+.3f" % d, "informational (>= 0 expected)", d >= -0.02)

    wa, wb = SeasonalWorld(seed=7), SeasonalWorld(seed=7)
    run(Agent(Ledger()), wa, 0)
    train_agent = Agent(Ledger(), "seasonal_structured", True)
    run(train_agent, wa, 2000)
    for _ in range(2000):
        wb.step()
    path = os.path.join(tempfile.gettempdir(), "wholebrain_state.json")
    train_agent.save(path)
    rt = json.dumps(Agent.load(path).to_state(), sort_keys=True) == json.dumps(train_agent.to_state(), sort_keys=True)
    check("persistence: save/load round-trip", str(rt), "identical state", rt)
    l_led, f_led = Ledger(), Ledger()
    loaded = Agent.load(path, ledger=l_led, source="seasonal_structured", synthetic=True)
    fresh = Agent(f_led, "seasonal_structured", True)
    run(loaded, wa, 400)
    run(fresh, wb, 400)
    lm, fm = l_led.score(PRIMARY_H, 0)["mae"], f_led.score(PRIMARY_H, 0)["mae"]
    check("persistence: restart vs fresh", "MAE %.3f vs %.3f" % (lm, fm), "restarted agent is better", lm < fm)

    print("\nSYNTHETIC-DATA MACHINERY TEST - not evidence of consciousness\n")
    for n_, v, r, p in rows:
        print("%-38s %-42s %-44s %s" % (n_, v, r, p))
    print("\nlast self-narration (verbalized state, unverified):\n ", a.monologue[-1] if a.monologue else "-")


if __name__ == "__main__":
    main()
