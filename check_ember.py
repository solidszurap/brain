"""
Quick checks of Ember's self, with fake events and a fake mind (no LLM, no
network, runs in about a second). Run after changing mind/core.py or ember.py:

    python check_ember.py
"""
import json
import os
import tempfile

import ember as program
from mind import llm
from mind.core import Ember

H, D = 3600.0, 86400.0
failed = []


def check(name, ok, detail=""):
    print(("  ok    " if ok else "  FAIL  ") + name + (f"  ({detail})" if detail and not ok else ""))
    if not ok:
        failed.append(name)


def mind_says(**d):
    return json.dumps(d)


t = 1_800_000_000.0
e = Ember(now=t)

print("Meeting for the first time")
check("greets on the first visit", e.arrive(t))
system, user = e.prompt({"type": "arrive"}, t)
check("its mind is told it's the first meeting", "first time" in user)
r = e.respond({"type": "arrive"}, None, t)
check("the template mind introduces itself and asks", "Ember" in r["reply"] and r["reply"].endswith("?"))
check("nothing remembered from a greeting", not e.memories)

print("Remembering what you say, with your words as the source")
msg = "I love drawing. When I draw I can go for hours and forget to eat."
e.hear(t + 10, msg)
cur0 = e.curiosity
r = e.respond({"type": "talk", "text": msg}, mind_says(
    reply="Hours! What do you usually draw?", face="curious",
    remember=[{"kind": "flow", "note": "loses track of time when drawing", "quote": "I can go for hours"},
              {"kind": "enjoys", "note": "loves painting", "quote": "I love painting"},          # not what you said
              {"kind": "enjoys", "note": "loves drawing", "quote": "i love DRAWING"}]), t + 12)
check("a memory with a real quote is kept", any(m["note"] == "loses track of time when drawing" for m in e.memories))
check("a memory whose quote you never said is dropped", not any("painting" in m["note"] for m in e.memories))
check("quotes match regardless of case/punctuation", any(m["note"] == "loves drawing" for m in e.memories))
check("learning something new eases curiosity", e.curiosity < cur0)
check("the face its mind chose shows", e.face(t + 13, True)["expression"] == "curious")
check("...and fades after a while", e.face(t + 40, True)["expression"] != "curious" or e.curiosity > 0.65)

n = len(e.memories)
e.hear(t + 20, "Yeah I love drawing")
r = e.respond({"type": "talk", "text": "Yeah I love drawing"}, mind_says(
    reply="I know!", face="happy", remember=[{"kind": "enjoys", "note": "loves drawing", "quote": "I love drawing"}]),
    t + 21)
check("something it already knows isn't stored twice", len(e.memories) == n)

mid = e.memories[0]["id"]
e.hear(t + 30, "Actually lately I only draw for like 20 minutes")
e.respond({"type": "talk", "text": "Actually lately I only draw for like 20 minutes"}, mind_says(
    reply="Oh, that changed.", update=[{"id": mid, "note": "draws only about 20 minutes lately",
                                        "quote": "lately I only draw for like 20 minutes"}]), t + 31)
check("a correction updates the memory", e.find(mid)["note"] == "draws only about 20 minutes lately")

print("Real time, while you're here and while you're away")
e.update(t + 30 * 60, present=True)
check("your presence eases its want for connection", e.connection < 0.1, f"{e.connection:.2f}")
e.update(t + 30 * 60 + 3 * D, present=False)
check("three days away: connection want is high", e.connection > 0.9, f"{e.connection:.2f}")
check("...and the face shows it", e.face(t + 30 * 60 + 3 * D, False)["expression"] == "droopy")
back = t + 30 * 60 + 3 * D + 5
check("it greets you when you come back", e.arrive(back))
check("it knows how long you were away", abs(e.gap_before - 3 * D) < 60, f"{e.gap_before / D:.2f} days")
check("its face reacts to you coming back", e.face(back + 1, True)["expression"] == "surprised")
_, user = e.prompt({"type": "arrive"}, back)
check("its mind is told how long it's been", "3 days" in user)
check("its mind sees its memories", "draws only about 20 minutes lately" in user)
e.update(back + 1, present=True)
check("a short glance away later isn't a new greeting", not e.arrive(back + 60))

print("Your control over its memory")
check("you can correct a memory", e.edit_memory(mid, "draws a little, most days", back) and e.find(mid)["edited"])
check("you can make it forget", e.forget(mid) and e.find(mid) is None)

print("The template mind (no LLM)")
e.hear(back + 100, "I'm studying physics. My exam is on Friday.")
r = e.respond({"type": "talk", "text": "I'm studying physics. My exam is on Friday."}, "not json at all", back + 101)
check("unusable mind output falls back to the template mind", r["by"] == "template")
check("the template mind keeps what you say about yourself", len(r["remembered"]) == 2)
cfg = llm.LLMConfig(env={})
check("no key: the template mind", cfg.provider == "template" and not cfg.usable)
check("a Gemini key: Gemini is its mind", llm.LLMConfig(env={"GEMINI_API_KEY": "x"}).provider == "gemini")

print("Saving")
e.poke(back + 200)
d = json.loads(json.dumps(e.to_dict()))
e2 = Ember.from_dict(d)
check("everything survives a save", e2.memories == e.memories and e2.talk == e.talk and e2.pokes == 1)
check("the outbox isn't saved in its self", "outbox" not in d)
with tempfile.TemporaryDirectory() as tmp:
    for f in ("life.pkl.gz", "life_log.jsonl", "ember.json"):
        open(os.path.join(tmp, f), "w").close()
    dest = program.archive_old_life(tmp, now=back)
    check("the grid-world life is moved to the archive, not deleted",
          sorted(os.listdir(dest)) == ["life.pkl.gz", "life_log.jsonl"] and os.path.exists(os.path.join(tmp, "ember.json")))
    check("archiving twice does nothing", program.archive_old_life(tmp, now=back) is None)

print()
print("All checks passed." if not failed else f"{len(failed)} FAILED: {failed}")
raise SystemExit(1 if failed else 0)
