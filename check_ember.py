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
check("...what you keep meaning to start, not small talk", "keep meaning to start" in r["reply"])
check("its mind is told to ask the same on a first visit", "keep meaning to start" in user)
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
check("your presence eases its missing you", e.missing < 0.1, f"{e.missing:.2f}")
e.update(t + 30 * 60 + 3 * D, present=False)
check("three days away: it misses you a lot", e.missing > 0.9, f"{e.missing:.2f}")
check("...and the face shows it", e.face(t + 30 * 60 + 3 * D, False)["expression"] == "droopy")
back = t + 30 * 60 + 3 * D + 5
check("it greets you when you come back", e.arrive(back))
check("it knows how long you were away", abs(e.gap_before - 3 * D) < 60, f"{e.gap_before / D:.2f} days")
check("coming back after days: a moment of having missed you, then happy you're back", e.face(back + 1, True)["expression"] == "droopy"
      and e.face(back + 3, True)["expression"] == "surprised" and e.face(back + 6, True)["expression"] == "eager"
      and "It missed you" in e.face(back + 1, True)["why"][0])
check("...and after that it doesn't look droopy while you're here", e.face(back + 30, True)["expression"] != "droopy")
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
check("its mind looks back on the real numbers and your words", "Earlier work sessions: 3" in user
      and "fun, made the player move" in user and "Do you still want to on day 5?" in user and "finished" in user)
check("the template mind's look back is only the facts and the question",
      "Earlier work sessions: 3" in (tr := f._template({"type": "review", "id": eid}, x0 + 24 * H)["reply"]) and tr.endswith("day 5?"))
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
      and not f.active()["time_up"] and "3 more days of" in f.talk[-1]["text"] and "6 days in all" in f.talk[-1]["text"])
f.update(T + 6 * D + 300, present=False)
check("...and it asks again when those are up", f.talk[-1].get("timeup") and f.active()["time_up"])

print("Goals")
G = T + 10 * D
f.end_experiment(f.active()["id"], "done", G)
system, user = f.prompt({"type": "talk", "text": "I want to run 5 km", "mode": "work"}, G)
check("its mind may propose a goal when nothing is active", "propose it as a goal" in user and "This is your chat" in user)
check("its mind is told to talk a goal through (briefly) before planning it", "talk it through briefly first" in system
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
      "Their goal" in user and "got what they wanted" in user and "Earlier work sessions: 1" in user)
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
not_regular = lambda evs: [e for e in evs if not e.get("regular")]   # the daily one comes regardless (tested above)
check("a goal's chat isn't checked on while it's lively", not_regular(b.due_checkups(t + 61 * H)) == [])
due = b.due_checkups(t + 60 * H + 3 * D + 60)
check("after 3 quiet days, Ember checks in on the goal", len(due) == 1 and due[0].get("auto") and "Run 5 km" in due[0]["about"])
b.respond(due[0], mind_says(reply="How's the running going?"), t + 60 * H + 3 * D + 60)
check("...and doesn't nag while that's unanswered", not_regular(b.due_checkups(t + 60 * H + 9 * D)) == [])
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
check("at 23:00 their time, it waits", not_regular(n8.due_checkups(day0 + 22 * H)) == [])
check("at 3:00 their time, it waits", n8.due_checkups(day0 + 86400 + 2 * H) == [])
check("at 9:00 their time, the check-up comes", len(n8.due_checkups(day0 + 86400 + 8 * H)) == 1)
_, user = n8.prompt({"type": "talk", "text": "hi", "chat": "c1"}, day0 + 86400 + 8 * H)
check("its mind knows their local time", "09:00 (their local time)" in user)

print("Check-ups as often as you choose, at your hour")
from mind.core import CHECKUPS
ck = Ember(now=t)
ck.tz = 60                                        # Budapest in winter
d0 = t - (t % 86400) + 86400                      # a midnight UTC
ck.hear(d0 + 9 * H, "hi")                         # you talked at 10:00 your time
ck.respond({"type": "talk", "text": "hi"}, mind_says(reply="Hi!"), d0 + 9 * H + 1)
check("every day is the default, at 18:00, all week", ck.checkups == "daily" and ck.checkup_at == 18 * 60
      and ck.checkup_days == list(range(7)) and ck.snapshot(t, True)["checkups"]["at"] == "18:00")
ev0 = ck.due_checkups(d0 + 17 * H)                # 18:00 your time, on the day you talked in the morning
check("at your time it comes, even on a day you've talked", len(ev0) == 1 and ev0[0].get("regular"))
check("...once a day", ck.due_checkups(d0 + 17 * H + 600) == [])
ck.respond(ev0[0], mind_says(reply="How was your day?"), d0 + 17 * H + 5)
check("not before your hour the next day", ck.due_checkups(d0 + D + 15 * H) == [])
ev = ck.due_checkups(d0 + D + 17 * H)             # 18:00 your time, the next day
check("the next day at your hour, though you didn't answer: a check-up (Szilard: no matter if I didn't reply)",
      len(ev) == 1 and ev[0].get("regular") and ev[0]["chat"] == "c1")
check("...only once", ck.due_checkups(d0 + D + 17 * H + 600) == [])
ck2 = Ember.from_dict(json.loads(json.dumps(ck.to_dict())))
check("a deploy (saved and loaded again) never sends the day's check-up again", ck2.due_checkups(d0 + D + 17 * H + 900) == []
      and ck2.due_checkups(d0 + D + 23 * H) == [])
_, user = ck.prompt(ev[0], d0 + D + 17 * H)
check("its mind knows it's the check-up you asked for", "check up on them every day" in user)
r = ck.respond(ev[0], mind_says(reply=""), d0 + D + 17 * H + 5)
check("an empty answer from its mind still checks up, with a plain question",
      r["reply"].strip() and ck.talk[-1]["who"] == "ember" and ck.talk[-1]["text"] == r["reply"])
ck.hear(d0 + 2 * D + 17 * H - 300, "busy day")    # you're talking with it at 17:55
check("while you're talking with it right then, it waits a little", ck.due_checkups(d0 + 2 * D + 17 * H) == [])
check("...and comes once you've been quiet for a while", len(ck.due_checkups(d0 + 2 * D + 17 * H + 20 * 60)) == 1)
check("you can choose when", ck.set_checkups("daily", "09:00") and ck.checkup_at == 9 * 60)
check("...not a time that doesn't exist, no days at all, or a made-up choice", not ck.set_checkups("daily", "25:00")
      and not ck.set_checkups("daily", "18:75") and not ck.set_checkups("daily", None, [])
      and not ck.set_checkups("daily", None, [7]) and not ck.set_checkups("weekly") and ck.checkups == "daily")
ck.set_checkups("off")
ck.followups.append({"chat": "c1", "at": d0 + 12 * D, "about": "x", "set": d0})
check("off: nothing, not even what it planned", ck.due_checkups(d0 + 30 * D + 9 * H) == [] and not ck.followups)
ck.set_checkups("when")
ck.hear(d0 + 31 * D + 9 * H, "back")
check("when it matters: no regular ones", ck.due_checkups(d0 + 40 * D + 9 * H) == [])
check("three choices: off, when it matters, regularly", set(CHECKUPS) == {"off", "when", "daily"})
ow = Ember.from_dict(dict(Ember(now=t).to_dict(), checkups="weekly"))
check("a save with 'once a week' becomes regularly, on your days", ow.checkups == "daily")

print("Your exact time, any hour, on your days")
import time as _time
ex = Ember(now=t)
ex.tz = 60
m0 = d0 + 23 * H                                  # a midnight, your time
while _time.gmtime(m0 + 3600).tm_wday != 0:       # ...on a Monday
    m0 += D
ex.hear(m0 - 2 * D + 12 * H, "hi")                # you talked on Saturday
check("any minute, even late at night", ex.set_checkups("daily", "23:40", [0, 2, 4]) and ex.checkup_at == 23 * 60 + 40)
check("Monday 23:39: not yet", ex.due_checkups(m0 + 23 * H + 39 * 60) == [])
check("Monday 23:40: there it is, though it's night", len(ex.due_checkups(m0 + 23 * H + 40 * 60)) == 1)
ex.hear(m0 + 23 * H + 50 * 60, "thanks")
check("Tuesday isn't one of your days", ex.due_checkups(m0 + D + 23 * H + 45 * 60) == [])
check("Wednesday is", len(ex.due_checkups(m0 + 2 * D + 23 * H + 45 * 60)) == 1)
wk = Ember(now=t)
wk.tz = 60
wk.hear(m0 - 6 * D + 12 * H, "hi")                # you talked on Tuesday
wk.set_checkups("daily", "10:00", [0])
check("Mondays only: the next Monday comes", len(wk.due_checkups(m0 + 10 * H)) == 1)
_, user = wk.prompt({"type": "followup", "regular": True, "chat": "c1", "about": "how they are"}, m0 + 10 * H)
check("its mind knows your days and time", "check up on them on Mondays, at 10:00" in user)
check("planned check-ups still wait for the morning", (ex.followups.append(
    {"chat": "c1", "at": m0 + 3 * D, "about": "x", "set": m0}) or True) and ex.due_checkups(m0 + 3 * D + 22 * H) == []
      and len(ex.due_checkups(m0 + 4 * D + 8 * H)) == 1)
old2 = {k: v for k, v in Ember(now=t).to_dict().items() if k not in ("checkup_at", "checkup_days")}
old2["checkup_hour"] = 9
o2 = Ember.from_dict(old2)
check("a save with a whole hour keeps it", o2.checkup_at == 9 * 60 and o2.checkup_days == list(range(7)))

print("Staying on what the chat is for, and moving forward")
from mind.core import DRIFT_QUESTIONS
fo = Ember(now=t)
fo.hear(t + 1, "I want to get fit")
fo.respond({"type": "talk", "text": "I want to get fit"}, mind_says(reply="What does fit mean to you?"), t + 2)
for i in range(DRIFT_QUESTIONS - 1):
    fo.hear(t + 10 + i * 10, f"answer {i}")
    fo.respond({"type": "talk", "text": f"answer {i}"}, mind_says(reply=f"And question {i}?"), t + 11 + i * 10)
check("it counts its questions in a row", fo.asked_in_a_row("c1") == DRIFT_QUESTIONS)
_, user = fo.prompt({"type": "talk", "text": "hmm", "chat": "c1"}, t + 100)
check("...and is told to stop asking and propose something", "This time don't ask another" in user)
check("its mind knows what the chat is for", "it began with them saying \"I want to get fit\"" in user)
fo.respond({"type": "talk", "text": "ok"}, mind_says(reply="Here's a plan. Shall we start with a walk today?"), t + 110)
check("...a reply that's another question still counts", fo.asked_in_a_row("c1") == DRIFT_QUESTIONS + 1)
fo.respond({"type": "talk", "text": "ok"}, mind_says(reply="Let's do a 20-minute walk today, then 3 runs next week."),
           t + 120)
check("a reply that proposes something resets it", fo.asked_in_a_row("c1") == 0)
_, user = fo.prompt({"type": "talk", "text": "ok", "chat": "c1"}, t + 130)
check("...and the nudge is gone", "This time don't ask another" not in user)
from mind.core import SYSTEM as _S
check("its instructions: keep moving, few questions, then propose", "Keep each chat moving" in _S
      and "Ask at most 2 questions" in _S)
# planning a goal with Ember goes live fast (Szilard, 2026-11-07): two questions at most, then the goal
from mind.core import PLAN_REPLIES
pg = Ember(now=t)
ev = pg.plan_with_ember("Run a 5k", t + 1)
_, user = pg.prompt(ev, t + 2)
check("planning a goal: it's told to ask at most 2 questions", "ask at most 2 questions" in user)
for i in range(PLAN_REPLIES):
    pg.respond(ev, mind_says(reply=f"Question {i}?"), t + 10 + i * 10)
    ev = {"type": "talk", "text": f"answer {i}", "chat": ev["chat"]}
    pg.hear(t + 15 + i * 10, ev["text"], ev["chat"])
_, user = pg.prompt(ev, t + 100)
check("...after two of its replies, it's told to propose the goal now", 'propose it now, in "goal"' in user)
pg.respond(ev, mind_says(reply="Here's a plan.", goal={"title": "Run a 5k", "done_when": "I run 5 km in one go",
           "why": "you want it", "based_on": [], "days": 42, "plan": "Start small.",
           "phases": [{"title": "Weeks 1-2", "days": 14, "steps": ["Walk 10 minutes"]}]}), t + 110)
_, user = pg.prompt({"type": "talk", "text": "hmm", "chat": ev["chat"]}, t + 120)
check("...and once it has proposed one, the nudge stops", "propose it now" not in user and "ask at most" not in user)
check("...never stall or back off on its own; feelings about a goal are part of the work", "Never stall or back off"
      in _S and "are part of the work, not a reason to stop" in _S)

print("Hard things get care, not a smile")
hd = Ember(now=t)
hd.hear(t + 1, "My dad is in hospital and I can't focus on anything")
r = hd.respond({"type": "talk", "text": "My dad is in hospital and I can't focus on anything"}, mind_says(
    reply="That sounds really hard. Do you want to talk about it, or just needed to say it?", face="happy",
    feel="worried", feel_why="their dad is in hospital"), t + 2)
check("when it's worried, its face isn't happy even if its mind picked it", r["face"] == "worried"
      and hd.face(t + 3, True)["expression"] == "worried")
check("...and it stays that way after the moment", hd.face(t + 60, True)["expression"] == "worried")
r = hd.respond({"type": "talk", "text": "x"}, mind_says(reply="I'm so sorry.", face="eager", feel="sad"), t + 70)
check("sad: a sad face", r["face"] == "sad")
check("its instructions: read how they feel, no upbeat on hard things", "Read how they feel" in _S
      and "no silver linings" in _S)

print("Growing with you: XP, levels, stages")
from mind.core import XP, level_of, stage_of, xp_for, LOOKS
check("levels: 2 at 50 XP, 5 at 500, 10 at 2,250, 20 at 9,500", [xp_for(n) for n in (2, 5, 10, 20)] == [50, 500, 2250, 9500]
      and level_of(49) == 1 and level_of(50) == 2 and level_of(9500) == 20)
check("stages: Spark, Ember, Flame, Blaze", [stage_of(n) for n in (1, 4, 5, 9, 10, 19, 20)] ==
      ["Spark", "Spark", "Ember", "Ember", "Flame", "Flame", "Blaze"])
gx = Ember(now=t)
for i in range(8):
    gx.hear(t + i, f"msg {i}")
check("talking: a day's 10, then 2 a message, only the first 5 a day", gx.xp == XP["day"] + 5 * XP["talk"], str(gx.xp))
gx.hear(t + D + 5, "next day")
check("...and again the next day, plus a day together", gx.xp == 2 * XP["day"] + 6 * XP["talk"] + XP["together"],
      str(gx.xp))
x0 = gx.xp
gx.update(t + D + 10, True)
check("a day together counts once", gx.xp == x0)
gx.update(t + 4 * D + 10, False)
check("three more days together, counted when it next looks", gx.xp == x0 + 3 * XP["together"])
gx.respond({"type": "suggest"}, None, t + 4 * D + 20)
eid = next(x["id"] for x in gx.experiments if x["status"] == "suggested")
x0 = gx.xp
gx.pick(eid, t + 4 * D + 30)
check("starting a goal or experiment", gx.xp == x0 + XP["start"])
x0 = gx.xp
gx.set_step(eid, 0, True, t + 4 * D + 40)
gx.set_step(eid, 0, False, t + 4 * D + 41)
gx.set_step(eid, 0, True, t + 4 * D + 42)
check("a step done counts once, however often it's ticked", gx.xp == x0 + XP["step"])
gx.start_session(t + 4 * D + 50, gx.find_exp(eid).get("chat"))
x0 = gx.xp
gx.stop_session(t + 4 * D + 50 + 45 * 60)
check("a 45-minute work session: 5 + 4", gx.xp == x0 + 9)
x0 = gx.xp
gx.checkin(t + 4 * D + 50 + 46 * 60, 4, "good")
check("telling it how the session went", gx.xp == x0 + XP["checkin"])
x0 = gx.xp
gx.end_experiment(eid, "done", t + 5 * D)
check("finishing it", gx.xp == x0 + XP["finish"])
ck2 = Ember(now=t)
ck2.say(t + 1, "How did it go?", "curious", "c1", checkup=True)
x0 = ck2.xp
ck2.hear(t + 2, "it went well")
check("answering a check-up", ck2.xp == x0 + XP["checkup"] + XP["day"] + XP["talk"])

print("A new level: it says so once, after its own words")
lu = Ember(now=t)
lu.hear(t + 1, "hi")
lu.xp = 45
lu.hear(t + 2, "again")                           # 47
lu.hear(t + 3, "and again")                       # 49
lu.hear(t + 4, "once more")                       # 51: level 2
check("not on top of your message: it answers you first", lu.levelup_due == {"from": 1, "to": 2}
      and lu.talk[-1]["who"] == "you")
lu.respond({"type": "talk", "text": "once more"}, mind_says(reply="Hey!"), t + 5)
check("...then it says it reached level 2", lu.talk[-1].get("levelup") == 2 and "level 2" in lu.talk[-1]["text"]
      and lu.talk[-2]["text"] == "Hey!" and lu.levelup_due is None)
check("...and what it unlocked", "gold" in lu.talk[-1]["text"] and "Customize Ember" in lu.talk[-1]["text"])
lu.xp = 499
lu.gain("x", 1, t + 10)
lu.update(t + 11, True)
check("a new stage: 'I'm an Ember'", "I'm not a spark any more: I'm an Ember." in lu.talk[-1]["text"]
      and lu.level_info()["stage"] == "Ember")
check("its mind knows its level", "You're level 5, an Ember" in lu.prompt({"type": "talk", "text": "hi"}, t + 12)[1])

print("Looks: what its level has unlocked")
lk = Ember(now=t)
check("it starts amber, wearing nothing", lk.look["color"] == "amber" and lk.look["wear"] == "none")
check("a locked look is refused", not lk.set_look("wear", "crown") and lk.look["wear"] == "none")
check("an unknown part or item is refused", not lk.set_look("hat", "cap") and not lk.set_look("wear", "spacesuit"))
lk.xp = xp_for(20)
check("unlocked: yes", lk.set_look("wear", "crown") and lk.set_look("color", "violet") and lk.set_look("sparks", "hearts"))
check("the catalog says what unlocks when", any(i["id"] == "crown" and i["level"] == 20
                                                for p in lk.looks()["parts"] if p["id"] == "wear" for i in p["items"]))
lk2 = Ember.from_dict(json.loads(json.dumps(lk.to_dict())))
check("look, XP and level survive a save", lk2.look == lk.look and lk2.xp == lk.xp and lk2.level_info()["level"] == 20)
check("every part has a free default at level 1", all(items[0][2] == 1 for items in LOOKS.values()))

print("An Ember from before levels gets its XP from your history, quietly")
ol = Ember(now=t)
for i in range(3):
    ol.hear(t + i * D, f"day {i}")
ol.respond({"type": "suggest"}, None, t + 3 * D)
oid = next(x["id"] for x in ol.experiments if x["status"] == "suggested")
ol.pick(oid, t + 3 * D + 1)
ol.set_step(oid, 0, True, t + 3 * D + 2)
ol.update(t + 10 * D, True)
d_old = {k: v for k, v in ol.to_dict().items() if k not in ("xp", "xp_log", "xp_today", "days_counted",
                                                             "levelup_due", "look")}
for x in d_old["experiments"]:
    for s in x["steps"]:
        s.pop("xp", None)
lines = len(d_old["talk"])
ob = Ember.from_dict(json.loads(json.dumps(d_old)))
check("its level comes from what you did together", ob.xp == 3 * (XP["day"] + XP["talk"]) + 10 * XP["together"]
      + XP["start"] + XP["step"], str(ob.xp))
check("...with no level-up lines", len(ob.talk) == lines and ob.levelup_due is None)
ob.set_step(oid, 0, True, t + 10 * D + 5)
check("...and a step already counted isn't counted again", ob.xp == 3 * (XP["day"] + XP["talk"]) + 10 * XP["together"]
      + XP["start"] + XP["step"])

print("Goals of their own: make one yourself, in phases")
from mind.core import PHASE_MAX
gq = Ember(now=t)
g90 = gq.new_goal("Run a half marathon", "I finish 21 km", 90, ["Buy shoes", "Run 2 km"], t + 10)
check("you can make a goal yourself: active, in its own chat", g90 and g90["status"] == "active"
      and gq.find_chat(g90["chat"])["title"] == "Run a half marathon" and gq.active(g90["chat"]) is g90)
check("a 90-day goal goes in 7 phases of at most 2 weeks", len(g90["phases"]) == 7
      and all(p["days"] <= PHASE_MAX for p in g90["phases"]) and sum(p["days"] for p in g90["phases"]) == 90
      and g90["phases"][0]["title"].startswith("Days 1-"), str([p["title"] for p in g90["phases"]]))
check("...your steps are phase 1's, and today's step is the first", gq.today_step(g90)["text"] == "Buy shoes")
check("...and it says so in that chat", "Today's step: Buy shoes" in gq.last_line(g90["chat"])["text"])
g14 = gq.new_goal("Read a book", "", 14, [], t + 20)
check("a 2-week goal is one phase", len(g14["phases"]) == 1 and g14["phases"][0]["title"] == "The whole way"
      and "What's a first step" in gq.last_line(g14["chat"])["text"])
g28 = gq.new_goal("Learn to juggle", "", 28, [], t + 30)
check("phases by week when the days fit", [p["title"] for p in g28["phases"]] == ["Weeks 1-2", "Weeks 3-4"])
check("no goal without a title", gq.new_goal("  ", "", 30, [], t + 40) is None)

print("Your own goal's length: any number of hours, days, weeks or months")
gh = gq.new_goal("Finish the essay", "", None, [], t + 50, n=3, unit="hours")
check("3 hours: ends 3 hours later, one phase, and it says \"3 hours\"", gh["ends_at"] == t + 50 + 3 * 3600
      and gh["days"] == 0.125 and len(gh["phases"]) == 1 and "in 3 hours" in gq.last_line(gh["chat"])["text"])
vh = gq.goal_view(gh, t + 50 + 3600)
check("...its page counts hours left, and offers 1 more hour", vh["left"] == 7200 and vh["length"] == "3 hours"
      and vh["more"] == "1 more hour" and vh["phase_info"]["left"] == 7200, str(vh.get("more")))
check("...its mind is told the hours left", "2 hours left of 3 hours" in "\n".join(gq._experiment_context(t + 50 + 3600, gh["chat"])))
gq.update(t + 50 + 3 * 3600 + 5, False)
check("...its time-up line says hours, not days", "the 3 hours you gave" in gq.last_line(gh["chat"])["text"])
check("...and keeping going adds an hour", gq.extend(gh["id"], t + 50 + 3 * 3600 + 10)
      and abs(gh["ends_at"] - (t + 50 + 4 * 3600 + 10)) < 1
      and "1 more hour of" in gq.last_line(gh["chat"])["text"] and "4 hours in all" in gq.last_line(gh["chat"])["text"],
      gq.last_line(gh["chat"])["text"])
gw = gq.new_goal("Learn chords", "", None, [], t + 60, n=3, unit="weeks")
check("3 weeks is 21 days, in two phases, said as \"3 weeks\"", gw["days"] == 21 and len(gw["phases"]) == 2
      and "in 3 weeks" in gq.last_line(gw["chat"])["text"])
gm = gq.new_goal("Save money", "", None, [], t + 70, n=2, unit="months")
check("2 months is 60 days", gm["days"] == 60 and sum(p["days"] for p in gm["phases"]) == 60)
gd = gq.new_goal("Walk daily", "", None, [], t + 80, n=36, unit="hours")
check("36 hours: a day and a half, said as 36 hours", gd["days"] == 1.5 and abs(gd["ends_at"] - (t + 80 + 36 * 3600)) < 1
      and sum(p["days"] for p in gd["phases"]) == 1.5)
check("...a goal given in hours keeps going by an hour, even when it's a day or more",
      gq.goal_view(gd, t + 90)["more"] == "1 more hour" and gq.goal_view(gd, t + 90)["hourly"])
g24 = gq.new_goal("A day off", "", None, [], t + 85, n=24, unit="hours")
check("...24 hours too, and its mind hears hours left", g24["days"] == 1 and gq.goal_view(g24, t + 90)["more"] == "1 more hour"
      and "left of 24 hours" in "\n".join(gq._experiment_context(t + 3600, g24["chat"])))
gq.end_experiment(g24["id"], "dropped", t + 100)
gy = gq.new_goal("Too long", "", None, [], t + 90, n=30, unit="months")
check("at most a year", gy["days"] == 365 and "span" not in gy)
g0 = gq.new_goal("Odd", "", None, [], t + 95, n="x", unit="days")
check("a length that isn't a number gives a month", g0["days"] == 30)
for g_ in (gh, gw, gm, gd, gy, g0):
    gq.end_experiment(g_["id"], "dropped", t + 100)

rx = Ember(now=t)
for k in range(3):
    rx.gain("talking", 2, t + k)
rx.gain("a step done", 5, t + 5)
rx.gain("talking", 2, t + D)
r = rx.recent_xp()
check("recent XP: one line per kind a day, newest first", [(g["why"], g["xp"], g["times"]) for g in r]
      == [("talking", 2, 1), ("a step done", 5, 1), ("talking", 6, 3)], str(r))

print("The daily check instead of the stopwatch")
x0 = gq.xp
ev = gq.daily_check(g90["id"], "done", "felt good", t + 3600)
check("did it: today's step is done, the next becomes today's", g90["steps"][0]["done"]
      and gq.today_step(g90)["text"] == "Run 2 km")
check("...it's logged, with your words", g90["log"][-1]["how"] == "done" and g90["log"][-1]["words"] == "felt good")
check("...XP for the check and the step", gq.xp - x0 == XP["check_done"] + XP["step"], str(gq.xp - x0))
check("...your line in the goal's chat, and an event for its mind", gq.last_line(g90["chat"]).get("daily") == "done"
      and ev["type"] == "daily" and ev["first"] and gq.event_chat(ev) == g90["chat"])
x0 = gq.xp
ev2 = gq.daily_check(g90["id"], "partly", "", t + 7200)
check("a second check the same day replaces the first, without more XP or another answer",
      len(g90["log"]) == 1 and g90["log"][0]["how"] == "partly" and gq.xp == x0 and not ev2["first"])
_, user = gq.prompt(ev, t + 3601)
check("its mind is told how today went, and to make it smaller if it was hard",
      "checked in on today's step" in user and "no guilt" in user and "Earlier work sessions" not in user)
check("the goal's page view: today's step, checked today, streak, 14 days", (lambda v: v["today_step"]["text"] == "Run 2 km"
      and v["checked_today"] == "partly" and v["streak"] == 1 and len(v["recent"]) == 14
      and v["phase_info"]["count"] == 7)(gq.goal_view(g90, t + 7300)))
gq.daily_check(g90["id"], "done", "", t + D + 10)
gq.daily_check(g90["id"], "skip", "tired", t + 2 * D + 10)
check("a day you didn't get to it ends the streak (it still counts as honest)", gq.streak(g90, t + 2 * D + 20) == 0)
gq.daily_check(g90["id"], "done", "", t + 3 * D + 10)
check("...and a new one starts", gq.streak(g90, t + 3 * D + 20) == 1)
check("its mind's reply to a check can add a smaller step", gq.respond(
    {"type": "daily", "id": g90["id"], "how": "skip", "step": "x", "text": "", "chat": g90["chat"]},
    mind_says(reply="That's okay.", add_steps=["Run 1 km"]), t + 3 * D + 20).get("steps") == ["Run 1 km"])
check("adding your own step", gq.add_step(g90["id"], "Stretch after") and g90["steps"][-1]["text"] == "Stretch after")

print("Phases: one at a time, a look back at each end")
ph_end = g90["phases"][0]["end"]
gq.update(ph_end + 60, False)
check("when a phase is over, it says so once", sum(1 for l in gq.talk if l.get("phase_up") == g90["id"]) == 1)
gq.update(ph_end + 120, False)
check("...only once", sum(1 for l in gq.talk if l.get("phase_up") == g90["id"]) == 1)
_, user = gq.prompt({"type": "phase", "id": g90["id"], "from": 0}, ph_end + 200)
check("its mind gets the phase's facts and plans the next", "Phase 1 of their goal" in user and "daily checks" in user
      and "Next is phase 2" in user and "add_steps" in user)
x0 = gq.xp
r = gq.respond({"type": "phase", "id": g90["id"], "from": 0}, mind_says(
    reply="Week one went well. Next: longer runs.", add_steps=["Run 3 km twice", "Rest a day between"]), ph_end + 210)
check("its answer moves on: the look back is kept, the new steps are today's", g90["phase"] == 1
      and g90["phases"][0]["look_back"].startswith("Week one") and gq.today_step(g90)["text"] == "Run 3 km twice"
      and gq.xp - x0 == XP["phase"])
check("...and the old phase keeps its steps", any(s["text"] == "Buy shoes" for s in g90["phases"][0]["steps"]))
r = gq.respond({"type": "phase", "id": g90["id"], "from": 0}, mind_says(reply="again", add_steps=["x"]), ph_end + 220)
check("a phase answer that comes twice doesn't skip a phase", g90["phase"] == 1)
check("you can go to the next phase early", gq.next_phase(g90["id"], ph_end + D, "done early", ["A"]) and g90["phase"] == 2
      and g90["phases"][2]["start"] == ph_end + D)
fx = gq.facts(g90, ph_end + D + 10)
check("what happened counts the checks and the phases", fx["checks"]["done"] >= 2 and len(fx["phases"]) == 3)

print("Goals Ember proposes come in phases too")
gp = Ember(now=t)
gp.hear(t + 1, "I want a girlfriend")
r = gp.respond({"type": "talk", "text": "I want a girlfriend"}, mind_says(reply="Here's a plan.", goal={
    "title": "A girlfriend", "done_when": "I'm in a relationship", "days": 90, "plan": "Meet people.",
    "phases": [{"title": "Weeks 1-2: get out more", "days": 14, "steps": ["Join a club", "Say hi to 3 people"]},
               {"title": "Weeks 3-4: talk more", "days": 14}, {"title": "Weeks 5-8: dates", "days": 30}]}), t + 2)
gpx = r["suggested"][0]
check("its proposal keeps its phases (at most 2 weeks each)", [p["days"] for p in gpx["phases"]] == [14, 14, 14]
      and gpx["days"] == 42 and gpx["steps"][0]["text"] == "Join a club")
gp.pick(gpx["id"], t + 3)
check("picked: timed from today", gpx["phases"][0]["start"] == t + 3 and gpx["ends_at"] == t + 3 + 42 * D)
old = {k: v for k, v in Ember(now=t).to_dict().items()}
old["experiments"] = [{"id": "x1", "kind": "goal", "title": "Old", "question": "q", "days": 60, "status": "active",
                       "steps": [{"text": "s", "done": False}], "created": t, "started": t, "ends_at": t + 60 * D,
                       "ended": None, "based_on": [], "why": ""}]
old["last_update"] = t + 20 * D
og = Ember.from_dict(json.loads(json.dumps(old)))
check("an old goal without phases loads in phases, in the right one", len(og.experiments[0]["phases"]) == 5
      and og.experiments[0]["phase"] == 1, str([og.experiments[0].get("phase")]))

print("A name of your own for it")
nm = Ember(now=t)
check("it's Ember until you name it", nm.name == "Ember" and "They gave you a name" not in nm.prompt(
    {"type": "talk", "text": "hi"}, t)[1])
check("you can name it", nm.set_name("  Lumi  ") and nm.name == "Lumi" and nm.snapshot(t, True)["name"] == "Lumi")
check("its mind knows its new name", "They gave you a name: Lumi" in nm.prompt({"type": "talk", "text": "hi"}, t)[1])
check("the template mind introduces itself by it", nm.respond({"type": "arrive"}, None, t + 1)["reply"].startswith(
    "Hi, I'm Lumi."))
nm.set_name("x" * 60)
check("a name stays short", len(nm.name) == 24)
check("an empty name is Ember again", nm.set_name("   ") and nm.name == "Ember")
nm.set_name("Lumi")
check("its name survives a save", Ember.from_dict(json.loads(json.dumps(nm.to_dict()))).name == "Lumi")

print("Writing first when you open it: only after a while")
gr = Ember(now=t)
check("the very first time, it introduces itself", gr.arrive(t))
gr.respond({"type": "arrive"}, mind_says(reply="Hi, I'm Ember."), t + 1)
gr.update(t + 2, present=True)
check("back after 2 hours: it lights up but doesn't write", not gr.arrive(t + 2 * H) and gr.face(t + 2 * H + 1, True)[
    "expression"] in ("eager", "surprised"))
gr.update(t + 2 * H, present=True)
check("back after 10 hours, its greeting still unanswered: it doesn't write again", not gr.arrive(t + 12 * H))
gr.hear(t + 12 * H + 10, "hello")
gr.respond({"type": "talk", "text": "hello"}, mind_says(reply="Hey you."), t + 12 * H + 11)
gr.update(t + 12 * H + 20, present=True)
check("back after 10 hours, after a real talk: it writes first", gr.arrive(t + 22 * H + 30))
gr.respond({"type": "arrive"}, mind_says(reply="Good evening."), t + 22 * H + 31)
check("...and its greeting is marked as its own words", gr.last_line("c1").get("greet"))

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
      f1["expression"] == "happy" and any("It feels proud: they went to the gym" in w for w in f1["why"]))
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
      and any("It misses you: you've been away" in w for w in fa["why"]))
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

print("Missing you and curiosity, made visible")
cu = Ember(now=t)
cu.curiosity = 0.8
_, user = cu.prompt({"type": "talk", "text": "hey"}, t + 1)
check("one question at a time: asking about their day comes first", "ask about their day once today" in user
      and "one question to know them better" not in user)
cu.day_asked = cu._date(t + 1)
_, user = cu.prompt({"type": "talk", "text": "hey"}, t + 1)
check("curious: its mind is told to ask one question to know them better", "one question to know them better" in user)
cu.curiosity = 0.3
_, user = cu.prompt({"type": "talk", "text": "hey"}, t + 1)
check("...not when it's just learned something", "one question to know them better" not in user)
mi = Ember(now=t)
mi.arrive(t)
mi.update(t + 60, True)
mi.arrive(t + 2 * D)
_, user = mi.prompt({"type": "arrive"}, t + 2 * D)
check("back after 2 days: its mind says it missed them, warmly, never as a reproach", "You missed them while they were away"
      in user and "never as a reproach" in user)

print("Connection: a bond that builds as you talk, and stays")
from mind.core import BOND_KEEP
bd = Ember(now=t)
check("it starts at nothing", bd.connection == 0.0)
for day in range(10):
    for m in range(3):
        bd.hear(t + day * D + m * 60, f"day {day} msg {m}")
c10 = bd.connection
check("ten days of talking: it has grown", 0.5 < c10 < 0.7, f"{c10:.2f}")
bd.update(t + 9 * D + 3600, True)
bd.update(t + 9 * D + 2 * D, False)
check("two days apart: it stays (no fading yet)", abs(bd.connection - c10) < 1e-9)
bd.update(t + 9 * D + 10 * D, False)
c_after = bd.connection
check("ten days without talking: it fades a little, slowly", 0.75 * c10 < c_after < c10, f"{c10:.2f} -> {c_after:.2f}")
bd.hear(t + 9 * D + 10 * D + 60, "I'm back")
check("talking again: it grows again", bd.connection > c_after)
check("being here without talking doesn't make it drop", (lambda c: (bd.update(t + 20 * D, True) or True)
                                                          and abs(bd.connection - c) < 1e-9)(bd.connection))
old = Ember(now=t)
for day in range(5):
    old.hear(t + day * D, "hi")
d_old = old.to_dict()
d_old.pop("missing")
d_old["connection"] = 0.8                         # what "connection" meant before: missing you
ob = Ember.from_dict(json.loads(json.dumps(d_old)))
check("an older Ember: its old 'connection' is now 'missing you', and its bond comes from your history",
      ob.missing == 0.8 and abs(ob.connection - old.connection) < 0.02, f"{ob.connection:.2f} vs {old.connection:.2f}")
_, user = bd.prompt({"type": "talk", "text": "hi"}, t + 20 * D)
check("its mind knows how close you've become", "Your connection with them:" in user and "missing them" in user)

print("Asking about your day, once a day, for connection")
dy = Ember(now=t)
dy.tz = 60
d18 = t - (t % 86400) + 17 * H                    # 18:00 their time
_, user = dy.prompt({"type": "talk", "text": "hi"}, d18)
check("its mind is told to ask about their day (in the evening: how it was)", "You haven't asked about their day yet today"
      in user and "evening: ask how their day was" in user)
dy.hear(d18, "hi")
dy.respond({"type": "talk", "text": "hi"}, mind_says(reply="Hi! How was your day?", asked_about_day=True), d18 + 1)
_, user = dy.prompt({"type": "talk", "text": "good"}, d18 + 60)
check("...once it has asked, not again today", "You haven't asked about their day" not in user)
_, user = dy.prompt({"type": "talk", "text": "morning"}, d18 + 16 * H)
check("...and the next morning: what's ahead today", "morning: ask what's ahead today" in user)
check("the template mind doesn't count as asking", (lambda e: (e.respond({"type": "talk", "text": "x"}, None, d18) or True)
                                                    and e.day_asked == "")(Ember(now=t)))

print("Who it is")
from mind.core import SYSTEM
check("Ember knows who it is, why it exists and how it helps", "Szurap" not in SYSTEM and all(w in SYSTEM for w in (
    "Who you are, when they ask", "always say why you exist too", "no names", "small experiments", "make a plan with them",
    "check up on them", "What it knows", "+ New chat", "not a therapist", "10 free messages")))

print("Saving")
e.poke(back + 200)
d = json.loads(json.dumps(e.to_dict()))
e2 = Ember.from_dict(d)
check("everything survives a save", e2.memories == e.memories and e2.talk == e.talk and e2.pokes == 1)
check("the outbox isn't saved in its self", "outbox" not in d)
with tempfile.TemporaryDirectory() as tmp:
    for f in ("life.pkl.gz", "life_log.jsonl", "ember.json", "plan.json", "feedback.jsonl"):
        open(os.path.join(tmp, f), "w").close()
    dest = program.archive_old_life(tmp, now=back)
    check("the grid-world life is moved to the archive, not deleted",
          sorted(os.listdir(dest)) == ["life.pkl.gz", "life_log.jsonl"] and os.path.exists(os.path.join(tmp, "ember.json")))
    check("...but today's files stay (the plan, the feedback)",
          os.path.exists(os.path.join(tmp, "plan.json")) and os.path.exists(os.path.join(tmp, "feedback.jsonl")))
    check("archiving twice does nothing", program.archive_old_life(tmp, now=back) is None)

print("The owner page's numbers")
t0 = 1_800_000_000
o = Ember(now=t0)
o.hear(t0 + 60, "first day")
o.hear(t0 + 120, "still the first day")
v = o.owner_view(t0 + 200)
check("one day, two messages, not back yet", v["days"] == 1 and v["said"] == 2 and v["today"]
      and not v["back_day2"] and not v["back_week2"], str(v))
o.hear(t0 + 86400 * 2, "came back")
o.hear(t0 + 86400 * 9, "and again a week later")
v = o.owner_view(t0 + 86400 * 9 + 10)
check("back on another day, and after the first week", v["days"] == 3 and v["back_day2"] and v["back_week2"], str(v))
check("numbers only: none of their words", "came back" not in json.dumps(v) and "first day" not in json.dumps(v))
old = o.to_dict()
old.pop("you_days"), old.pop("you_said")
b = Ember.from_dict(old)
check("an Ember saved before this counts its days from the talk it kept", b.you_said == 4 and len(b.you_days) == 3)

print("Badges that level up")
from mind.core import BADGES  # noqa: E402
bg = Ember(now=t)
lst = bg.badge_list(t)
check("a new Ember has every badge at level 0, with what level 1 takes",
      bg.badges == {} and len(lst) == len(BADGES) and all(b["level"] == 0 and b["next"] and b["how"] for b in lst))
bg.hear(t + 5, "hi")
bg.update(t + 6, present=True)
talk = next(b for b in bg.badge_list(t + 6) if b["id"] == "talk")
check("your first words: Good talks, level 1", bg.badges.get("talk") == [t + 6] and talk["level"] == 1)
check("...and how far to level 2", talk["value"] == 1 and talk["next"] == 25 and talk["how"] == "Send Ember 25 messages")
check("...told in the window, never as a chat line", not any(l.get("badges") for l in bg.talk))
gid = bg.new_goal("Walk every day", "", 30, ["Walk 10 minutes"], t + 10)["id"]
for k in range(7):
    bg.daily_check(gid, "done" if k != 3 else "partly", "", t + 20 + k * 86400)
lv = lambda b: len(bg.badges.get(b, []))
check("7 days in a row of done or partly: On fire reaches level 2 (3, then 7 days)", lv("streak") == 2)
check("...Showing up level 2 (5 days of checks), Goal setter level 1", lv("checks") == 2 and lv("goals") == 1)
bg.daily_check(gid, "skip", "", t + 20 + 8 * 86400)
check("a level once reached stays, even after a skip", lv("streak") == 2)
check("...and a week together: Together level 1", lv("together") == 1)
bg.set_name("Pip")
bg.update(t + 9 * 86400, present=True)
check("a name of its own: its only level, so it's at the top", lv("named") == 1
      and next(b for b in bg.badge_list(t + 9 * 86400) if b["id"] == "named")["next"] is None)
before = {k: list(v) for k, v in bg.badges.items()}
check("nothing new: no level moves, no time changes", bg.check_badges(t + 10 * 86400) == [] and bg.badges == before)
check("the window gets the level of each badge", bg.snapshot(t + 10 * 86400, True)["badges"]["streak"] == 2)
old = bg.to_dict()
old.pop("badges")
ob2 = Ember.from_dict(old)
ob2.update(t + 10 * 86400, present=False)
check("an Ember saved before badges reaches the levels it already earned", len(ob2.badges.get("streak", [])) == 2 and "talk" in ob2.badges)

print("Goal levels and the path")
gp = Ember(now=t)
pg = gp.new_goal("Learn to juggle", "", 21, ["Two balls"], t + 10)
for k in range(6):
    gp.daily_check(pg["id"], ["done", "done", "partly", "skip", "done", "done"][k], "", t + 20 + k * 86400)
v = gp.goal_view(pg, t + 30 + 6 * 86400)
check("a goal's level rises every 5 days of doing it (skips don't count)", v["glevel"]["level"] == 2 and v["glevel"]["good"] == 5
      and v["glevel"]["next"] == 5)
nodes = [n for p in v["path"] for n in p["nodes"]]
check("the path has one stop per day, in its phases", len(nodes) == 21 and len(v["path"]) == len(pg["phases"]))
check("...each day as it went: done, partly, skip", [n["state"] for n in nodes[:6]] == ["done", "done", "partly", "skip", "done", "done"])
check("...today, then the days ahead", nodes[6]["state"] == "today" and nodes[6]["today"] and nodes[7]["state"] == "ahead")
v2 = gp.goal_view(pg, t + 30 + 9 * 86400)
check("a day without a check is shown as missed", [n["state"] for n in [n for p in v2["path"] for n in p["nodes"]]][6:10] == ["missed", "missed", "missed", "today"])

print("Becoming someone: its moments with you, and its notes on your months")
mo = Ember(now=t)
mo.set_name("Pip", t + 5)
g1 = mo.new_goal("Run 5k", "", 30, ["Run 1 km"], t + 10)
for k in range(7):
    mo.daily_check(g1["id"], "done", "", t + 20 + k * D)
mo.update(t + 30 + 6 * D, present=True)
ids = [m["id"] for m in mo.moments]
check("its own moments, each with when: you met, named it, your first goal, first check, first 7-day run",
      ids == ["met", "named", "first_goal", "first_check", "streak_7"])
check("...in its own words", next(m for m in mo.moments if m["id"] == "named")["text"] == "You named me Pip."
      and next(m for m in mo.moments if m["id"] == "first_goal")["text"] == "You started your first goal, \"Run 5k\"."
      and next(m for m in mo.moments if m["id"] == "streak_7")["t"] == t + 20 + 6 * D)
mo.set_name("Lumi", t + 40 * D)
check("...each moment once (a new name doesn't replace the day you first named it)",
      sum(m["id"] == "named" for m in mo.moments) == 1)
check("the window gets them, oldest first", [m["id"] for m in mo.memory_page(t + 7 * D)["moments"]][:2] == ["met", "named"])
due = mo.moment_due(t + 7 * D + 60)
check("a week after you met, it's an anniversary", due and due["id"] == "met" and due["label"] == "a week")
_, user = mo.prompt({"type": "talk", "text": "hey"}, t + 7 * D + 60)
check("...its mind is told, to bring it up once if it fits", "Today it's a week since" in user and "remembered_moment" in user)
mo.hear(t + 7 * D + 70, "hey")
r = mo.respond({"type": "talk", "text": "hey"}, mind_says(reply="A week ago today we met.", remembered_moment=True),
               t + 7 * D + 71)
check("...once it has, not again that day", r.get("recalled") and mo.moment_due(t + 7 * D + 200) is None)
check("...nor the same anniversary the next day", (mo.moment_due(t + 8 * D + 60) or {}).get("id") != "met")
check("a goal's first check, a month on", (mo.moment_due(t + 30 * D + 20) or {}).get("label") == "a month")
check("years count too", mo.moment_due(t + 365 * D + 60)["label"] == "a year")
c2 = mo.new_chat(t + 9 * D)
_, user = mo.prompt({"type": "talk", "text": "hi", "chat": c2}, t + 9 * D)
check("in another chat its mind hears the moment without the goal's name (chats never mix)",
      "You started your first goal." in user and "Run 5k" not in user)
_, user = mo.prompt({"type": "talk", "text": "hi", "chat": g1["chat"]}, t + 9 * D)
check("...and with it in the goal's own chat", "You started your first goal, \"Run 5k\"" in user)
mo.end_experiment(g1["id"], "done", t + 31 * D)
mo.update(t + 31 * D, present=True)
check("finishing your first goal is a moment", any(m["id"] == "first_done" and m["t"] == t + 31 * D for m in mo.moments))
mo2 = Ember.from_dict(json.loads(json.dumps(mo.to_dict())))
check("moments and what it brought up survive a save", mo2.moments == mo.moments and mo2.recalled == mo.recalled)
old = mo.to_dict()
for k in ("moments", "recalled", "recalled_day"):
    old.pop(k)
old["xp"] = 600
ob = Ember.from_dict(old)
check("an Ember saved before moments finds the ones whose day is known",
      {"met", "first_goal", "first_check", "streak_7", "first_done"} <= {m["id"] for m in ob.moments}
      and next(m for m in ob.moments if m["id"] == "first_goal")["t"] == g1["started"])
check("...and keeps its name and stage without a made-up day, never brought up as an anniversary",
      all(m["t"] is None for m in ob.moments if m["id"] in ("named", "stage_ember"))
      and {"named", "stage_ember"} <= {m["id"] for m in ob.moments})

import calendar
from mind.core import month_step
jan = calendar.timegm((2027, 1, 20, 9, 0, 0))
feb1 = calendar.timegm((2027, 2, 1, 9, 0, 0))
om = Ember(now=jan)
check("a new Ember has no month notes, and none is due in its first month", om.months == [] and om.month_due(jan + 5 * D) is None)
gm = om.new_goal("Sleep by 11", "", 30, ["Phone away at 10:30"], jan + 60)
for k in range(3):
    om.hear(jan + k * D + 100, f"day {k}, I think I can do it")
    om.respond({"type": "talk", "text": f"day {k}, I think I can do it"}, mind_says(reply="Good."), jan + k * D + 101)
    om.daily_check(gm["id"], "done" if k else "partly", "", jan + k * D + 200)
check("a new month: its note on the month before is due", om.month_due(feb1) == "2027-01")
f = om.month_facts("2027-01")
check("...from what happened in it: days, messages, checks, what you started, moments",
      f["name"] == "January 2027" and f["days"] == 3 and f["messages"] == 3 and f["checks"] == {"done": 2, "partly": 1, "skip": 0}
      and f["started"] == ["goal \"Sleep by 11\""] and any("first goal" in m for m in f["moments"]))
system, user = om.prompt({"type": "month", "month": "2027-01"}, feb1)
check("its mind is asked for a short note about the month, with the facts, not in a chat",
      "Our month" in user and "January 2027" in user and "2 did it, 1 partly" in user and "Recent conversation" not in user)
om.month_asked = {"month": "2027-01", "t": feb1}
check("...asked once: not again while it writes", om.month_due(feb1 + 60) is None)
check("...but again on a later visit if that one failed", om.month_due(feb1 + 900) == "2027-01")
talk_before = len(om.talk)
r = om.respond({"type": "month", "month": "2027-01"}, mind_says(reply="January was the month you took sleep seriously."), feb1 + 1000)
check("the note is kept on its page, never said in a chat", r["month"] == "2027-01" and len(om.talk) == talk_before
      and om.month_list()[0]["text"].startswith("January was") and om.month_list()[0]["name"] == "January 2027")
check("...once: not due again", om.month_due(feb1 + 2 * D) is None and om.snapshot(feb1 + 2 * D, True)["month_latest"] == "2027-01")
check("...and the window gets them, newest first", om.memory_page(feb1)["months"][0]["month"] == "2027-01")
mar1 = calendar.timegm((2027, 3, 1, 9, 0, 0))
check("a month you barely came: no note, quietly", om.month_due(mar1) is None and om.month_last == "2027-02")
tm = Ember(now=jan)
for k in range(2):
    tm.hear(jan + k * D, "hi")
r = tm.respond({"type": "month", "month": "2027-01"}, None, feb1)
check("the mind without an LLM writes the plain facts", r["by"] == "template" and tm.months[0]["text"].startswith("January 2027 together: you came on 2 days"))
old = om.to_dict()
for k in ("months", "month_last", "month_asked"):
    old.pop(k)
old["last_update"] = feb1 + 3 * D
oo = Ember.from_dict(old)
check("an Ember saved before month notes starts with the next month (nothing old written at a deploy)",
      oo.month_last == "2027-01" and oo.month_due(feb1 + 4 * D) is None)
check("months step over the year", month_step("2026-12", 1) == "2027-01" and month_step("2027-01", -1) == "2026-12")

print("Deleting a chat or a goal")
dl = Ember(now=t)
dl.hear(t + 10, "I love to paint, it's my thing")
dl.respond({"type": "talk", "text": "I love to paint, it's my thing", "chat": "c1"},
           mind_says(reply="Nice.", remember=[{"kind": "enjoys", "note": "loves painting", "quote": "I love to paint"}]), t + 11)
g = dl.new_goal("Paint 10 pictures", "", 30, ["Buy paper"], t + 20)
dl.daily_check(g["id"], "done", "", t + 30)
gc = g["chat"]
check("a goal you started is one of your moments, with its name", any("Paint 10 pictures" in m["text"] for m in dl.moments))
dl.followups.append({"chat": gc, "at": t + 99999, "about": "paper", "set": t})
check("deleting a goal's chat deletes the chat, its lines, its goal and the check-ups planned there",
      dl.delete_chat(gc, t + 40) and not any(c["id"] == gc for c in dl.chats) and not dl.find_exp(g["id"])
      and not any(l.get("chat") == gc for l in dl.talk) and not any(f["chat"] == gc for f in dl.followups))
check("...what Ember learned about you stays (only Forget deletes a memory)", len(dl.memories) == 1)
check("...and the moment stays, without the goal's name", any(m["id"] == "first_goal" for m in dl.moments)
      and not any("Paint 10" in m["text"] for m in dl.moments))
check("an answer still on its way to a deleted chat is dropped, never said elsewhere",
      dl.respond({"type": "daily", "id": g["id"], "how": "done", "chat": gc}, mind_says(reply="Well done!"), t + 50)["skipped"]
      and not any(l["text"] == "Well done!" for l in dl.talk) and dl.gone({"type": "talk", "text": "x", "chat": gc}))
g2 = dl.new_goal("Read more", "", 14, ["One page"], t + 60)
check("deleting a goal keeps its chat", dl.delete_goal(g2["id"], t + 61) and not dl.find_exp(g2["id"])
      and any(c["id"] == g2["chat"] for c in dl.chats))
check("...and an unknown one is refused", not dl.delete_goal("x99", t + 62) and not dl.delete_chat("c99", t + 62))
for c in [c["id"] for c in dl.chats]:
    dl.delete_chat(c, t + 70)
check("deleting every chat leaves one fresh chat", len(dl.chats) == 1 and dl.chats[0]["title"] == "New chat" and not dl.talk)

print("A level-up goes where you were, never into an empty new chat")
lu = Ember(now=t)
lu.hear(t + 10, "hi")
lu.respond({"type": "talk", "text": "hi", "chat": "c1"}, mind_says(reply="Hi!"), t + 11)
fresh = lu.new_chat(t + 20)                       # you tapped +, and haven't written there yet
lu.gain("test", 100, t + 21)
lu.update(t + 22, present=True)
check("a new level from the day's progress is told in the chat you talked in", any(l.get("levelup") for l in lu.talk if l.get("chat", "c1") == "c1")
      and not any(l.get("chat") == fresh for l in lu.talk))
check("...so the new chat stays empty", next(c for c in lu.chat_list() if c["id"] == fresh)["empty"])

print("Missed days on a goal")
md = Ember(now=t)
mg = md.new_goal("Stretch", "", 30, ["5 minutes"], t + 10)
check("a goal started today has missed nothing", md.goal_view(mg, t + 60)["missed"] == 0)
check("two days later with no check-in: 2 missed (today is still open)", md.goal_view(mg, t + 2 * D + 60)["missed"] == 2)
md.daily_check(mg["id"], "skip", "", t + 2 * D + 70)
check("\"Not today\" is a check-in, not a missed day", md.goal_view(mg, t + 3 * D + 60)["missed"] == 0)
check("then 4 quiet days: 4 missed", md.goal_view(mg, t + 7 * D + 60)["missed"] == 4)
md.end_experiment(mg["id"], "done", t + 7 * D + 70)
check("a finished goal misses nothing", md.goal_view(mg, t + 9 * D)["missed"] == 0)

print("Where you came from")
sc = Ember(now=t)
check("a new Ember knows no source", sc.source == "" and sc.owner_view(t)["source"] == "")
check("the first source is kept", sc.came_from("TT", t + 60) and sc.source == "tt")
check("...a later one doesn't replace it", not sc.came_from("ig", t + 120) and sc.source == "tt")
old = Ember(now=t)
check("nonsense isn't kept", not old.came_from("<script>", t + 60) and not old.came_from("x" * 20, t + 60))
check("an Ember older than a day isn't counted as a sign-up", not old.came_from("tt", t + 2 * D) and old.source == "")
od = Ember(now=t).to_dict(); od.pop("source")
check("a saved self from before keeps loading, with no source", Ember.from_dict(od).source == "")

print()
print("All checks passed." if not failed else f"{len(failed)} FAILED: {failed}")
raise SystemExit(1 if failed else 0)
