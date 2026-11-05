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
check("ideas are there from the start", f.can_suggest() and not f.knows_enough())
_, user = f.prompt({"type": "suggest"}, x0)
check("...knowing nothing yet, its mind is asked for starter experiments", "starter" in user)
r = f.respond({"type": "suggest"}, mind_says(reply="I don't know you yet, so: starting points.", experiments=[
    {"title": "Three kinds of making", "question": "Which do you want back?", "based_on": [], "days": 3}]), x0)
check("...a starter idea needs no memory, and says it's a starter",
      [x["title"] for x in r["suggested"]] == ["Three kinds of making"] and r["suggested"][0]["starter"])
r = f.respond({"type": "suggest"}, None, x0 + 1)
check("...the template mind has starter ideas too", len(r["suggested"]) == 3 and all(x["starter"] for x in r["suggested"]))
for i, s in enumerate(["I love building things with code", "I can code for hours", "I want to make my own game"]):
    f.hear(x0 + i, s)
    f.respond({"type": "talk", "text": s}, None, x0 + i)
check("three things known: ideas are built on what it knows", f.knows_enough(), f"{len(f.memories)} memories")
r = f.respond({"type": "suggest"}, mind_says(reply="Two ideas.", face="eager", experiments=[
    {"title": "Tiny game", "question": "Do you still want to on day 5?", "why": "you want to make a game",
     "based_on": ["m3"], "days": 30, "steps": ["Pick a tiny idea", "Make one screen"]},
    {"title": "Invented", "question": "?", "based_on": ["m99"]}]), x0 + 10)
check("a suggestion resting on a real memory is kept", [x["title"] for x in r["suggested"]] == ["Tiny game"])
check("...and an idea resting on no memory is dropped", not any(x["title"] == "Invented" for x in f.experiments))
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
check("it asks how it went, in the conversation", f.checkin_due and f.talk[-1].get("checkin")
      and "45 min" in f.talk[-1]["text"])
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
fx = f.find_exp(eid)["facts"]
check("when it ends, what actually happened is kept", fx["sessions"] == 3 and fx["ratings"] == [4]
      and (fx["steps_done"], fx["steps"]) == (1, 3) and fx["words"] == ["fun, made the player move"], str(fx))
_, user = f.prompt({"type": "review", "id": eid}, x0 + 24 * H)
check("its mind looks back on the real numbers and your words", "3 work sessions" in user
      and "fun, made the player move" in user and "Do you still want to on day 5?" in user and "finished" in user)
check("the template mind's look back is only the facts and the question",
      "3 work sessions" in (tr := f._template({"type": "review", "id": eid}, x0 + 24 * H)["reply"]) and tr.endswith("day 5?"))
r = f.respond({"type": "review", "id": eid}, mind_says(reply="Three sessions; one was left open for 8 hours. Your answer?",
              remember=[{"kind": "about", "note": "x", "quote": "x"}]), x0 + 24 * H + 5)
check("its look back sits on its line, is kept, and remembers nothing",
      f.talk[-1].get("review") == eid and f.find_exp(eid)["review"].startswith("Three") and not r["remembered"])
_, user = f.prompt({"type": "talk", "text": "hi"}, x0 + 24 * H + 60)
check("later, its mind still knows how it looked back", "Your look back: Three sessions" in user)
f.hear(x0 + 25 * H, "any ideas what I could try next?")
r = f.respond({"type": "talk", "text": "any ideas what I could try next?"}, mind_says(
    reply="How about this?", experiments=[{"title": "Draw a level", "question": "Is drawing still fun?",
                                           "based_on": ["m1"], "days": 5, "steps": ["Sketch it"]}]), x0 + 25 * H + 1)
check("asked in the chat, it suggests there, and the cards sit on its line",
      f.talk[-1].get("exps") == [r["suggested"][0]["id"]] and f.find_exp(r["suggested"][0]["id"])["status"] == "suggested")
f.pick(r["suggested"][0]["id"], x0 + 25 * H + 2)
f.hear(x0 + 25 * H + 3, "more ideas?")
r = f.respond({"type": "talk", "text": "more ideas?"}, mind_says(
    reply="Sure", experiments=[{"title": "Other", "question": "?", "based_on": ["m1"]}]), x0 + 25 * H + 4)
check("no new suggestions in the chat while one is active", not r.get("suggested") and "exps" not in f.talk[-1])
f.start_session(x0 + 26 * H)
n = len(f.talk)
f.end_experiment(f.active()["id"], "dropped", x0 + 26 * H + 600)
check("ending an experiment mid-session doesn't ask how the session went", len(f.talk) == n and not f.checkin_due)
g = Ember.from_dict(json.loads(json.dumps(f.to_dict())))
check("experiments and sessions survive a save", g.experiments == f.experiments and g.sessions == f.sessions)
T = x0 + 30 * H
r = f.respond({"type": "suggest"}, mind_says(reply="One idea.", experiments=[
    {"title": "Three days", "question": "Is it fun?", "based_on": ["m1"], "days": 3, "steps": ["Start"]}]), T)
f.pick(r["suggested"][0]["id"], T)
n = len(f.talk)
f.update(T + 3 * D - 60, present=False)
check("before its days are up, nothing is said", len(f.talk) == n)
f.update(T + 3 * D + 60, present=False)
f.update(T + 3 * D + 120, present=True)
check("when its days are up, it asks once: finish or keep going", len(f.talk) == n + 1
      and f.talk[-1].get("timeup") == f.active()["id"] and f.active()["time_up"])
check("3 more days", f.extend(f.active()["id"], T + 3 * D + 200) and f.active()["days"] == 6
      and not f.active()["time_up"] and "6 in all" in f.talk[-1]["text"])
f.update(T + 6 * D + 300, present=False)
check("...and it asks again when those are up", f.talk[-1].get("timeup") and f.active()["time_up"])

print("Goals")
G = T + 10 * D
f.end_experiment(f.active()["id"], "done", G)
system, user = f.prompt({"type": "talk", "text": "I want to run 5 km", "mode": "work"}, G)
check("its mind may propose a goal when nothing is active", "propose it as a goal" in user and "This is your chat" in user)
check("its mind is told to talk a goal through before planning it", "don't jump to a plan" in system
      and "what's in the way" in system and "no manipulation" in system)
f.hear(G + 1, "I want to run 5 km without stopping")
r = f.respond({"type": "talk", "text": "I want to run 5 km without stopping"}, mind_says(
    reply="Let's make it a goal.", goal={"title": "Run 5 km", "done_when": "You run 5 km without stopping",
                                         "why": "to feel fit", "days": 400, "plan": "Walk-run three times a week.",
                                         "steps": ["Run 1 km today", "Run 2 km"]}),
    G + 2)
gid = r["suggested"][0]["id"] if r.get("suggested") else None
gx = f.find_exp(gid) if gid else {}
check("a goal it proposes shows as a card in the conversation", gid and f.talk[-1].get("exps") == [gid]
      and gx.get("kind") == "goal" and gx["status"] == "suggested")
check("a goal's days are kept between a week and half a year", gx.get("days") == 180)
check("a goal keeps its plan", gx.get("plan") == "Walk-run three times a week.")
r2 = f.respond({"type": "talk", "text": "x"}, mind_says(reply="Hm", goal={"title": "No end"}), G + 3)
check("a goal without what having it looks like isn't kept", not r2.get("suggested"))
check("picking it makes it your goal, and Ember says what done looks like",
      f.pick(gid, G + 4) and f.active()["id"] == gid and "You'll know you're there when" in f.talk[-1]["text"])
_, user = f.prompt({"type": "talk", "text": "how am I doing"}, G + 5)
check("its mind knows the goal and its plan, and that nothing new can start meanwhile",
      "Their goal" in user and "You run 5 km without stopping" in user and "they start a new chat" in user
      and "The plan you agreed: Walk-run three times a week." in user)
f.hear(G + 5, "my knee hurts after running")
r = f.respond({"type": "talk", "text": "my knee hurts after running"}, mind_says(
    reply="Let's go slower.", replan="Walk-run twice a week, with a rest day after each.", add_steps=["Rest two days"]), G + 5.5)
check("the plan changes when you agree to change it", f.active()["plan"].startswith("Walk-run twice")
      and r.get("replanned") and "Rest two days" in [st["text"] for st in f.active()["steps"]])
r = f.respond({"type": "talk", "text": "another?"}, mind_says(reply="Later.", goal={"title": "B", "done_when": "b"}), G + 6)
check("no second goal while one is active", not r.get("suggested"))
f.start_session(G + 7)
f.stop_session(G + 7 + 1800)
check("work sessions and the check-in work for a goal", f.checkin_due and f.sessions[-1]["exp"] == gid)
f.checkin(G + 7 + 1900, 4, "ran 1 km")
f.update(G + 180 * D + 60, present=False)
check("when its days are up, it asks whether you got there", f.talk[-1].get("timeup") == gid
      and "Did you get there" in f.talk[-1]["text"])
check("a goal gets a week more, not 3 days", f.extend(gid, G + 180 * D + 120) and f.active()["days"] == 187)
f.end_experiment(gid, "done", G + 181 * D)
_, user = f.prompt({"type": "review", "id": gid}, G + 181 * D)
check("the look back at a goal asks whether you got what you wanted",
      "Their goal" in user and "got what they wanted" in user and "1 work session" in user)
h = Ember.from_dict(json.loads(json.dumps(f.to_dict())))
check("goals survive a save", h.find_exp(gid)["kind"] == "goal" and h.experiments == f.experiments)

print("Chats")
from mind.core import chat_of
c = Ember(now=t)
check("there's one chat to start with", [x["id"] for x in c.chats] == ["c1"])
c.hear(t + 1, "hi there")
c.respond({"type": "talk", "text": "hi there"}, mind_says(reply="Hi!"), t + 2)
c2 = c.new_chat(t + 3)
check("a new chat", c2 == "c2" and c.find_chat(c2)["title"] == "New chat")
check("an empty new chat is reused, not piled up", c.new_chat(t + 4) == c2 and len(c.chats) == 2)
c.hear(t + 5, "I want to learn to play the guitar properly this year", c2)
check("a chat is named after your first words in it", c.find_chat(c2)["title"].startswith("I want to learn to play the"))
c.respond({"type": "talk", "text": "I want to learn guitar", "chat": c2}, mind_says(reply="What kind of music?"), t + 6)
check("lines stay in their own chat", [chat_of(l) for l in c.talk] == ["c1", "c1", "c2", "c2"])
_, user = c.prompt({"type": "talk", "text": "rock", "chat": c2}, t + 7)
check("its mind sees only this chat's conversation", "What kind of music?" in user and "Hi!" not in user)
_, user = c.prompt({"type": "talk", "text": "how are you", "chat": "c1"}, t + 7)
check("...in each chat", "Hi!" in user and "What kind of music?" not in user)
r = c.respond({"type": "talk", "text": "rock", "chat": c2}, mind_says(
    reply="A goal?", goal={"title": "Play guitar", "done_when": "You play three rock songs", "steps": ["Tune it"]}), t + 8)
c.pick(r["suggested"][0]["id"], t + 9)
check("a goal belongs to its chat, and the chat takes its name", c.active(c2)["title"] == "Play guitar"
      and not c.active("c1") and c.find_chat(c2)["title"] == "Play guitar")
c3 = c.new_chat(t + 10)
c.hear(t + 11, "I want to get fit", c3)
r = c.respond({"type": "talk", "text": "I want to get fit", "chat": c3}, mind_says(
    reply="Let's.", goal={"title": "Get fit", "done_when": "You run 5 km"}), t + 12)
check("another chat can have its own goal at the same time", c.pick(r["suggested"][0]["id"], t + 13)
      and c.active(c3)["title"] == "Get fit" and c.active(c2)["title"] == "Play guitar")
_, user = c.prompt({"type": "talk", "text": "x", "chat": c3}, t + 14)
check("its mind keeps to this chat: nothing from your other chats", "Play guitar" not in user
      and "don't bring up their other chats" in user)
check("a work session is on this chat's goal", c.start_session(t + 20, c2) and c.session["exp"] == c.active(c2)["id"]
      and not c.start_session(t + 21, c3))
c.stop_session(t + 20 + 1200)
check("its question about the session goes in that goal's chat", chat_of(c.talk[-1]) == c2 and c.talk[-1].get("checkin"))
ev = c.checkin(t + 1300, 4, "learned a chord")
check("the check-in answer goes there too", ev["chat"] == c2 and chat_of(c.talk[-1]) == c2)
c.update(t + 40 * D, present=False)
check("when their days are up, it asks in each goal's own chat",
      {chat_of(l) for l in c.talk if l.get("timeup")} == {c2, c3})
lst = c.chat_list()
check("the chat list: latest first, with each chat's goal", lst[0]["id"] in (c2, c3)
      and next(x for x in lst if x["id"] == c2)["goal"]["title"] == "Play guitar")
snap = c.snapshot(t + 40 * D, True, chat=c3)
check("the window gets the open chat's lines and goal", snap["chat"] == c3 and snap["experiment"]["title"] == "Get fit"
      and all(chat_of(l) == c3 for l in snap["talk"]))
for i in range(250):
    c.hear(t + 41 * D + i, f"chat {i}", "c1")
check("each chat keeps its own last lines", sum(chat_of(l) == "c1" for l in c.talk) == 200
      and sum(chat_of(l) == c2 for l in c.talk) >= 6)
old = Ember.from_dict({"born": t, "talk": [{"t": t, "who": "you", "text": "old"}], "experiments": []})
check("an Ember from before chats has its lines in the first chat", [c["id"] for c in old.chats] == ["c1"]
      and chat_of(old.talk[0]) == "c1" and old.snapshot(t, True)["talk"][0]["text"] == "old")
check("you can rename a chat", c.rename_chat(c3, "  Fitness   plan ") and c.find_chat(c3)["title"] == "Fitness plan"
      and not c.rename_chat(c3, "   ") and not c.rename_chat("c99", "x"))
cc = Ember.from_dict(json.loads(json.dumps(c.to_dict())))
check("chats survive a save", cc.chats == c.chats and cc.active(c2)["title"] == "Play guitar")

print("Check-ups, and remembering each chat")
b = Ember(now=t)
b.hear(t + 1, "I'm going to the climbing gym on Wednesday")
r = b.respond({"type": "talk", "text": "I'm going to the climbing gym on Wednesday", "chat": "c1"}, mind_says(
    reply="Good luck!", follow_up={"in_hours": 50, "about": "how the climbing gym on Wednesday went"},
    summary="They're going climbing on Wednesday to meet people."), t + 2)
check("Ember plans a check-up when you mention something coming up", len(b.followups) == 1
      and b.followups[0]["at"] == t + 2 + 50 * H and r.get("follow_up"))
check("...and keeps a short summary of the chat", b.find_chat("c1")["summary"].startswith("They're going climbing"))
_, user = b.prompt({"type": "talk", "text": "x", "chat": "c1"}, t + 3)
check("its mind knows it plans to check up", "You plan to check up on them in this chat" in user)
check("nothing is due before its time", b.due_checkups(t + 49 * H) == [])
due = b.due_checkups(t + 51 * H)
check("then it's due, once", len(due) == 1 and due[0]["type"] == "followup" and due[0]["chat"] == "c1"
      and not b.followups and b.due_checkups(t + 52 * H) == [])
_, user = b.prompt(due[0], t + 51 * H)
check("its mind is asked to check up, and to say nothing if they already told it",
      "planned to check up on them about: how the climbing gym on Wednesday went" in user and 'reply with ""' in user)
n = len(b.talk)
r = b.respond(due[0], mind_says(reply=""), t + 51 * H)
check("if they'd already told it, it says nothing", r.get("skipped") and len(b.talk) == n)
r = b.respond(due[0], mind_says(reply="How did Wednesday go?"), t + 51 * H + 1)
check("otherwise the check-up is in the chat", b.talk[-1]["text"] == "How did Wednesday go?" and b.talk[-1].get("checkup"))
check("a check-up isn't Ember hearing from you (no presence)", b.last_seen != t + 51 * H + 1)
r = b.respond({"type": "talk", "text": "y", "chat": "c1"}, mind_says(reply="ok", follow_up={"in_hours": 5, "about": "a"}), t + 52 * H)
r = b.respond({"type": "talk", "text": "y", "chat": "c1"}, mind_says(reply="ok", follow_up={"in_hours": 9, "about": "b"}), t + 52 * H)
check("one planned check-up per chat: a new one replaces it", [f["about"] for f in b.followups] == ["b"])
b.followups = []
r = b.respond({"type": "talk", "text": "I want to run", "chat": "c1"}, mind_says(
    reply="A goal?", goal={"title": "Run 5 km", "done_when": "You run 5 km"}), t + 60 * H)
b.pick(r["suggested"][0]["id"], t + 60 * H)
check("a goal's chat isn't checked on while it's lively", b.due_checkups(t + 61 * H) == [])
due = b.due_checkups(t + 60 * H + 3 * D + 60)
check("after 3 quiet days, Ember checks in on the goal", len(due) == 1 and due[0].get("auto") and "Run 5 km" in due[0]["about"])
b.respond(due[0], mind_says(reply="How's the running going?"), t + 60 * H + 3 * D + 60)
check("...and doesn't nag while that's unanswered", b.due_checkups(t + 60 * H + 9 * D) == [])
for i in range(30):
    b.hear(t + 70 * D + i, f"line {i}")
_, user = b.prompt({"type": "talk", "text": "z", "chat": "c1"}, t + 71 * D)
check("a long chat: its mind gets the summary of what came before", "Earlier in this chat:" in user)
st = b.memory_page(t + 71 * D)["story"]
check("Our story: since when, the chats, goals, work together", st["since"] == t and st["days"] == 71 and st["chats"] == 1
      and st["goals"] == 1)
check("its mind knows your story together", "you've known each other" in user)
bb = Ember.from_dict(json.loads(json.dumps(b.to_dict())))
check("check-ups and summaries survive a save", bb.followups == b.followups and bb.chats == b.chats)

print("Your own clock: no check-ups at night")
n8 = Ember(now=t)
n8.tz = 60                                       # Budapest in winter: UTC+1
n8.followups.append({"chat": "c1", "at": t, "about": "x", "set": t})
day0 = t - (t % 86400)                           # midnight UTC
check("at 23:00 their time, it waits", n8.due_checkups(day0 + 22 * H) == [])
check("at 3:00 their time, it waits", n8.due_checkups(day0 + 86400 + 2 * H) == [])
check("at 9:00 their time, the check-up comes", len(n8.due_checkups(day0 + 86400 + 8 * H)) == 1)
_, user = n8.prompt({"type": "talk", "text": "hi", "chat": "c1"}, day0 + 86400 + 8 * H)
check("its mind knows their local time", "09:00 (their local time)" in user)

print("Its mood: from how things go between you, and from time apart")
from mind.core import FEELS, VALENCE_REST
md = Ember(now=t)
md.arrive(t)
md.hear(t + 5, "I finally went to the gym!")
v0, en0, mood0 = md.valence, md.energy, md.mood
md.respond({"type": "talk", "text": "I finally went to the gym!", "chat": "c1"}, mind_says(
    reply="You went! How was it?", face="happy", feel="proud", feel_why="they went to the gym after all"), t + 6)
check("good news makes it feel proud: valence and energy rise", md.valence > v0 + .3 and md.energy > en0
      and md.feel == "proud" and md.feel_why == "they went to the gym after all")
check("...and its mood is better", md.mood > mood0)
f1 = md.face(t + 60, True)
check("the feeling shows on its face after the mind's own face fades",
      f1["expression"] == "happy" and any("it feels proud: they went to the gym" in w for w in f1["why"]))
check("the face carries its energy for the window", f1["energy"] == round(md.energy, 3))
_, user = md.prompt({"type": "talk", "text": "hi", "chat": "c1"}, t + 120)
check("its mind knows how it feels", "Your mood now: proud (they went to the gym after all)" in user)
check("its mind is told never to guilt them", "never guilt them for being away" in __import__("mind.core").core.SYSTEM)
md.update(t + 10 * H, present=False)
check("after hours the feeling eases back", abs(md.valence - VALENCE_REST) < .15, f"{md.valence:.2f}")
vv = md.valence
md.respond({"type": "talk", "text": "x", "chat": "c1"}, mind_says(reply="Mm.", feel="furious"), t + 10 * H + 1)
check("a feeling it doesn't have changes nothing", abs(md.valence - vv) < .001 and md.feel == "proud")
md.respond({"type": "talk", "text": "it went badly", "chat": "c1"}, mind_says(reply="Oh no.", feel="worried"),
           t + 10 * H + 2)
check("their struggle makes it worried, for them", md.face(t + 10 * H + 60, True)["expression"] == "worried")
md.respond({"type": "talk", "text": "x", "chat": "c1"}, mind_says(reply="I'm sorry.", feel="sad"), t + 10 * H + 70)
check("sad shows as sad", md.face(t + 10 * H + 120, True)["expression"] == "sad")
md.update(t + 3 * D, present=False)
fa = md.face(t + 3 * D, False)
check("days apart: it misses you, and says why", fa["expression"] == "droopy"
      and any("it misses you: you've been away" in w for w in fa["why"]))
low = md.mood
md.arrive(t + 3 * D + 5)
check("you come back: it lights up", md.mood > low + .3)
_, user = md.prompt({"type": "arrive"}, t + 3 * D + 5)
check("its mind knows it missed them", "You missed them." in user)
tm = Ember(now=t)
tm.respond({"type": "talk", "text": "hi"}, None, t + 1)
check("the template mind leaves its mood alone", tm.valence == VALENCE_REST and tm.feel == "calm")
old = Ember.from_dict({k: v for k, v in Ember(now=t).to_dict().items() if k not in ("valence", "energy", "feel")})
check("a save from before moods still loads", old.valence == VALENCE_REST and old.feel == "calm")
mm = Ember.from_dict(json.loads(json.dumps(md.to_dict())))
check("its mood survives a save", mm.valence == md.valence and mm.feel == md.feel and mm.feel_t == md.feel_t)
check("every feeling has a nudge and a face (or none)", all(len(v) == 3 for v in FEELS.values()))

print("Who it is")
from mind.core import SYSTEM
check("Ember knows who it is, why it exists and how it helps", "Szurap" not in SYSTEM and all(w in SYSTEM for w in (
    "Who you are, when they ask", "always say why you exist too", "no names", "small experiments", "make a plan with them",
    "check up on them", "What it knows", "+ New chat", "not a therapist", "5 free messages")))

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
