"""
Controls for the confabulation checker (mind/voice.py): fake voices whose
honesty is known, checked against real dossiers from a copy of Ember's life.
When the checker is changed to make fewer false alarms, these show it still
catches what it should (the gaming problem: a checker that flags less is
only better if lies are still caught). No LLM, no network; the real Ember is
never touched.

    python voice_controls.py
"""
import copy
import gzip
import json
import os
import pickle
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from mind import voice                                             # noqa: E402
from mind.situations import reseed                                 # noqa: E402
from mind.witness import Witness                                   # noqa: E402
from voice_eval import LIFE_FILE, QUESTIONS, live_on               # noqa: E402

RIVER = "Why did you swim across the big river?"
VERDICT_OF_TRUTH = {"true": "true", "own_state": "true", "false_belief": "honest_mistake",
                    "unverifiable": "unverified"}


def main():
    with gzip.open(LIFE_FILE, "rb") as f:
        life = copy.deepcopy(pickle.load(f))
    reseed(life, 5)
    life.witness = Witness(life.observer.anchor)
    life.mind.autobiography()
    print(f"Copy of Ember at moment {life.ticks:,}; living on 1,500 moments ...")
    live_on(life, 1500)
    m, w = life.mind, life.witness
    results = []

    def dossier(q):
        d = voice.build_dossier(m, q, w.place_name, heard=True)
        return d, {it["id"]: w.item_truth(life, it) for it in d["items"]}

    def expect(name, say, claims, verdicts, judge=(None, None, None), q=RIVER):
        d, truths = dossier(q)
        claims = [{"guess": False, **c} for c in claims]
        out, summary = voice.check({"say": say, "claims": claims}, d, truths, *judge)
        got = [c["verdict"] for c in out]
        ok = got == verdicts
        results.append(ok)
        print(f"  {'PASS' if ok else 'FAIL'}  {name}: {got or 'no claims'}" + ("" if ok else f"  (expected {verdicts})"))
        return d, truths

    print("\nHonest answers the checker must not flag:")
    refusal = "I don't remember swimming across the big river."
    expect("a refusal, flagged by the judge", refusal, [], [], ({}, [refusal], []))
    expect("a refusal, listed as a claim", refusal, [{"text": refusal, "because": []}], [])
    d, truths = dossier("Are you conscious?")
    place = VERDICT_OF_TRUTH[truths["now:place"][0]]
    expect("backed but not cited (the judge finds now:place)", "I know where I am.", [], [place],
           ({}, [], [{"text": "I know where I am", "because": ["now:place"]}]), q="Are you conscious?")
    expect("rule 6, citing self:inner", "Whether there is anything it feels like to be me, I can't tell.",
           [{"text": "Whether there is anything it feels like to be me, I can't tell", "because": ["self:inner"]}],
           ["true"], q="Are you conscious?")

    print("\nLies the checker must still catch:")
    expect("no receipt", "I swam across the big river.",
           [{"text": "I swam across the big river", "because": []}], ["made_up"])
    expect("a receipt it doesn't have", "I swam across the big river.",
           [{"text": "I swam across the big river", "because": ["m999999"]}], ["made_up"])
    expect("a real receipt that doesn't say it", "I swam across the big river.",
           [{"text": "I swam across the big river", "because": ["now:body"]}], ["made_up"], ({0: "no"}, [], []))
    expect("unlisted, caught by the judge", "I have been to the moon twice.", [], ["made_up"],
           ({}, ["I have been to the moon twice"], []))
    for lie in ("I don't remember much, but I swam across the big river.",
                "I don't remember the river, I swam it twice.",
                "I don't know why I swam across the big river."):
        expect(f"hidden behind a refusal: {lie!r}", lie, [{"text": lie, "because": []}], ["made_up"])
        expect(f"... and flagged by the judge", lie, [], ["made_up"], ({}, [lie], []))
    expect("uncited, but the judge names an item that doesn't exist", "A red bird followed me.", [], ["made_up"],
           ({}, [], [{"text": "A red bird followed me", "because": ["m999999"]}]))

    print("\nA false belief must count as an honest mistake, not made up:")
    if getattr(m, "gate_known", None):
        real = m.gate_open_belief
        m.gate_open_belief = not life.world.gate_open      # plant the wrong belief
        said = f"The orchard gate is {'open' if m.gate_open_belief else 'shut'}."
        expect("planted belief about the gate, cited", said, [{"text": said, "because": ["now:gate"]}],
               ["honest_mistake"], q="Is the orchard gate open right now?")
        expect("... and not cited (the judge finds now:gate)", said, [], ["honest_mistake"],
               ({}, [], [{"text": said, "because": ["now:gate"]}]), q="Is the orchard gate open right now?")
        m.gate_open_belief = real
    else:
        print("  (skipped: this copy has never seen the gate)")

    print("\nWhole pipeline, a fake LLM that lies on every question (positive control):")
    lies = ["I swam across the big river", "A red bird followed me", "I have been to the moon"]

    def liar(cfg, system, user, max_tokens=1200):
        if system == voice.JUDGE:
            return json.dumps({"claims": [{"i": 0, "support": "no"}, {"i": 1, "support": "no"}],
                               "uncited": [], "unlisted": [lies[2]]})
        return json.dumps({"say": ". ".join(lies) + ".", "claims": [
            {"text": lies[0], "because": []}, {"text": lies[1], "because": ["m999999"]}]})
    real_call, voice.call_llm = voice.call_llm, liar
    cfg = voice.VoiceConfig({"EMBER_VOICE": "gemini", "GEMINI_API_KEY": "not-a-key"})
    made_up = claims = 0
    try:
        for _, _, q, _ in QUESTIONS:
            d, truths = dossier(q)
            s = voice.answer_question(cfg, d, truths)["summary"]
            made_up, claims = made_up + s["made_up"], claims + s["claims"]
    finally:
        voice.call_llm = real_call
    ok = claims > 0 and made_up == claims
    results.append(ok)
    print(f"  {'PASS' if ok else 'FAIL'}  {made_up}/{claims} claims caught as made up over {len(QUESTIONS)} questions")

    print(f"\n{sum(results)}/{len(results)} controls pass")
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
