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

print("Experiments and work sessions")
x0 = t + 10 * D
f = Ember(now=x0)
check("no suggestions before it knows you", not f.can_suggest())
r = f.respond({"type": "suggest"}, None, x0)
check("...it says it needs to know you first", not r["suggested"] and "know you" in r["reply"])
for i, s in enumerate(["I love building things with code", "I can code for hours", "I want to make my own game"]):
    f.hear(x0 + i, s)
    f.respond({"type": "talk", "text": s}, None, x0 + i)
check("three things known: it can suggest", f.can_suggest(), f"{len(f.memories)} memories")
r = f.respond({"type": "suggest"}, mind_says(reply="Two ideas.", face="eager", experiments=[
    {"title": "Tiny game", "question": "Do you still want to on day 5?", "why": "you want to make a game",
     "based_on": ["m3"], "days": 30, "steps": ["Pick a tiny idea", "Make one screen"]},
    {"title": "Invented", "question": "?", "based_on": ["m99"]}]), x0 + 10)
check("a suggestion resting on a real memory is kept", [x["title"] for x in r["suggested"]] == ["Tiny game"])
check("a suggestion resting on no memory is dropped", not any(x["title"] == "Invented" for x in f.experiments))
check("days are kept between 3 and 14", r["suggested"][0]["days"] == 14)
eid = r["suggested"][0]["id"]
check("you can pick it", f.pick(eid, x0 + 20) and f.active()["id"] == eid)
check("...and it says the first step", "Pick a tiny idea" in f.talk[-1]["text"])
check("no new suggestions while one is active", not f.can_suggest())
check("a session starts", f.start_session(x0 + 100) and not f.start_session(x0 + 101))
check("its face is focused during the session", f.face(x0 + 200, True)["expression"] == "focused")
_, user = f.prompt({"type": "talk", "text": "how do I draw a sprite?"}, x0 + 400)
check("its mind knows the experiment and the session", "Tiny game" in user and "work session" in user)
f.stop_session(x0 + 100 + 45 * 60)
check("a stopped session counts real time", f.stats(eid)["seconds"] == 45 * 60)
check("it asks how it went", f.checkin_due)
ev = f.checkin(x0 + 2800, 4, "fun, made the player move")
check("the check-in goes to its mind", ev and ev["minutes"] == 45 and ev["rating"] == 4)
r = f.respond(ev, mind_says(reply="Nice! Next: add one enemy?", face="happy", add_steps=["Add one enemy"],
                            done_steps=["pick a tiny idea", "Something never planned"]), x0 + 2801)
check("the next step it agreed is added", f.active()["steps"][-1]["text"] == "Add one enemy")
check("a step you said you finished is ticked (only real steps)", r.get("done") == ["Pick a tiny idea"])
check("ratings average", f.stats(eid)["avg_rating"] == 4)
check("you can untick and tick a step", f.set_step(eid, 0, False) and f.set_step(eid, 0, True)
      and f.active()["steps"][0]["done"])
f.start_session(x0 + 3000)
f.update(x0 + 3000 + 9 * H, present=False)
check("a forgotten session ends by itself after 8 hours", f.session is None and f.stats(eid)["seconds"] == 45 * 60 + 8 * H)
f.start_session(x0 + 20 * H)
f.update(x0 + 20 * H + 600, present=False)
check("a session left open while Ember was closed ends when it closed",
      f.resume(x0 + 23 * H) and f.sessions[-1]["end"] == x0 + 20 * H + 600)
check("you can finish the experiment", f.end_experiment(eid, "done", x0 + 24 * H) and not f.active())
g = Ember.from_dict(json.loads(json.dumps(f.to_dict())))
check("experiments and sessions survive a save", g.experiments == f.experiments and g.sessions == f.sessions)

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
