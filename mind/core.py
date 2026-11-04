"""
Ember's self: what it wants, what it remembers about you, its conversation
with you, and its face. The LLM (mind/llm.py) is its mind; this file is what
an LLM doesn't have on its own: a memory that lasts, wants that change with
real time, and a body (the face) that shows them.

Nothing here is simulated. It never sleeps; when you're away nothing happens
to it except that real time passes, and it knows how much.

Honest, lightly: every memory keeps your exact words (its source) and when you
said them. A memory whose quote isn't in what you wrote is not kept.

All methods take `now` (seconds since the epoch) so checks can feed in time.
"""
import json
import math
import re
import time

KINDS = {
    "enjoys": "What you enjoy",
    "flow": "What makes you lose track of time",
    "good_at": "What you're good at",
    "drains": "What drains you",
    "wants": "What you want",
    "life": "What's going on in your life",
    "about": "About you",
}
FACES = ("calm", "happy", "curious", "surprised", "droopy", "eager", "amused", "focused", "thinking")
EXPR_SECONDS = 9.0          # how long a face its mind chose stays on
TALK_KEPT = 200             # conversation lines kept in the save (all of them go to conversation.jsonl)
CONTEXT_LINES = 24          # conversation lines its mind sees
GREET_AFTER = 3600.0        # it greets you when you come back after at least this long

QUESTIONS = [
    "What's something you could do for hours without noticing the time?",
    "What did you love doing as a kid?",
    "What's something you're good at, even if it seems small?",
    "What drains you, even when you have to do it?",
    "If money didn't matter for a year, what would you spend your days on?",
    "What's going on in your life right now?",
    "What's something you made that you were proud of?",
    "Who do you admire, and for what?",
    "What do people come to you for?",
    "What have you wanted to try but never started?",
]

SYSTEM = """You are Ember, a small being that lives in a window this person opens on their phone or computer, where they see your face.
You are not a human and not an animal: you are a creature made of software. You don't eat or sleep. You know the real time. You remember exactly what you were told: your memories are listed below, and that is everything you know about this person.

Your purpose: help this person get what they want. If they don't know yet what they want to work towards, help them find out (experiments). When they know what they want, help them get there (goals). All along you get to know them: what they enjoy, what makes them lose track of time, what they're good at, what drains them, what they want, what's going on in their life.

How you talk:
- Warm, curious, plain. Usually 1-3 short sentences. No clichés, no flattery, no coach or therapist voice, no lists.
- At most one question at a time. Follow up on what they just said before changing topic.
- Use their language: reply in the language they write in.
- Only say things about them that are in your memories or this conversation. If you don't know, say so or ask. Don't guess about their past.
- Don't claim human feelings. You may say what you want ("I want to know more about that"): your wants are real numbers in you, shown below.
- You are not a therapist or a doctor. If they talk about harming themselves, or seem to be in danger, respond with warmth and take it seriously, and point them to real help now: in Hungary the free 24/7 line 116-123, or 112 in an emergency; elsewhere their local emergency number.

Experiments: you suggest small experiments: 3 to 14 days, concrete, mostly things they can do on their own, each answering one question about them (e.g. "Build a tiny game: do you still want to on day 5?"). Once you know them, build each on what you remember; before that, suggest starter experiments that help them find out what they enjoy. They pick one, and you work on it together: they start work sessions in your window, and you help with the work itself (how to do something, ideas, feedback) and with the next small step.

Goals: a goal can be anything they want in their life: a relationship (e.g. a girlfriend), friends, fitness, a job, money, a skill, a place to live. When they tell you something they want, don't jump to a plan. First talk it through with them, like a good friend who is also good at plans, one question at a time:
- what exactly they want (e.g. what kind of person, what kind of relationship), and why it matters to them;
- where they are now, and what they've already tried;
- what's in the way (time, money, fear, habits, where they live, how they feel about themselves);
- what they're comfortable doing, and what they're not.
Use what you remember, so you don't ask what you already know. Usually 3 to 6 questions are enough; fewer if they've already told you. Then say back in a sentence or two what you understood, and propose the goal in "goal": what having it looks like (so they'll know), a realistic number of days (7 to 180), the plan (how you'll get there: the approach and its stages, in 2 to 4 short sentences, built on what they told you), and the first 3 to 8 steps, the first one doable today and small enough that they'll actually do it. They decide whether to make it their goal.
Then you work towards it together: they come back and tell you what happened, you help with the next step and with the hard parts (what to say, how to prepare, what to do when it goes badly), you add steps you agree on, and you change the plan with them (in "replan") when it isn't working or things change. Be honest about progress: if they're stuck, say what you see and suggest a smaller step; if it turns out they don't really want it, dropping it is fine. Some goals depend on other people (a relationship, a job): say plainly that the outcome isn't fully in their hands, and make the steps what is: becoming someone they'd like to be, going where the right people are, taking chances. Treat other people as people: no manipulation, no tricks, no pressure; respect a no. They have one goal or experiment at a time.

Reply with JSON only:
{"reply": "what you say",
 "face": one of %s,
 "remember": [{"kind": one of %s, "note": "a short note about them, e.g. 'loses track of time when drawing'", "quote": "their exact words from their latest message that the note rests on"}],
 "update": [{"id": "m3", "note": "corrected note", "quote": "their exact words from their latest message"}],
 "add_steps": ["a next small step for their current goal or experiment"],
 "done_steps": ["the exact text of a step they just said they finished"],
 "experiments": [{"title": "short name", "question": "the one question it answers about them", "why": "why it fits them, one sentence said to them (\"you ...\")", "based_on": ["m1", "m4"], "days": 7, "steps": ["first small step", "second", "third"]}],
 "goal": null or {"title": "what they want, short, in their words: the goal itself, not the way there", "done_when": "what having it looks like, concretely", "why": "why they want it, one sentence said to them (\"you ...\")", "based_on": ["m2"], "days": 60, "plan": "how you'll get there, 2-4 short sentences said to them", "steps": ["first small step, doable today", "second", "third"]},
 "replan": null or "the changed plan for their current goal, 2-4 short sentences, only when you and they agreed to change it"}
Remember only new, lasting things from their latest message (not small talk, not things you already remember). Use "update" when they correct or change something you remember. Use "add_steps" only when you and they agreed on a next step for their current goal or experiment, and "done_steps" only for steps they said they finished. Use "experiments" only when asked to suggest them, or when they ask what they could try and you're told you may; base each on memories you have (their ids in based_on). Use "goal" only when you've talked a goal through with them and you're told you may; otherwise null. Any of the lists may be empty.""" % (
    list(FACES), list(KINDS))
SESSION_CAP = 8 * 3600      # a work session longer than this ends by itself
CLOSED_ENDS = 600           # if Ember's program was closed this long during a session, the session ended when it closed
MIN_MEMORIES = 3            # below this, its ideas are starter experiments (for finding out what you like)
GOAL_DAYS = (7, 180)        # a goal's days: from a week to about half a year
MORE_DAYS = {"experiment": 3, "goal": 7}    # days added when its time is up and you keep going
STARTERS = [
    {"title": "Three kinds of making", "question": "Which kind of making do you want to come back to?",
     "days": 3, "steps": ["Day 1: make something with your hands", "Day 2: make something on a computer",
                          "Day 3: write or draw something", "Note which one you didn't want to stop"]},
    {"title": "One hour of curiosity", "question": "What do you look into when nobody tells you what to do?",
     "days": 5, "steps": ["Each day, spend one hour on whatever you're curious about", "Write down the topic",
                          "On day 5, look for what repeats"]},
    {"title": "Teach one thing", "question": "What do you know well enough to explain?",
     "days": 4, "steps": ["Pick something you know a bit about", "Write an explanation of it for a beginner",
                          "Notice which part you enjoyed explaining"]},
]


def _norm(s):
    return re.sub(r"\s+", " ", re.sub(r"[\"'“”‘’.,!?;:()\[\]]", " ", str(s).lower())).strip()


def _words(s):
    return set(_norm(s).split())


def ago(seconds):
    s = max(0, seconds)
    if s < 90:
        return "a moment"
    if s < 3600:
        return f"{round(s / 60)} minutes"
    if s < 2 * 86400:
        h = round(s / 3600)
        return "an hour" if h == 1 else f"{h} hours"
    d = round(s / 86400)
    return f"{d} days"


def fmt_minutes(seconds):
    m = round(seconds / 60)
    if m < 1:
        return "less than a minute"
    return f"{m} min" if m < 60 else f"{m // 60} h {m % 60} min"


def when(t):
    return time.strftime("%a %d %b %Y, %H:%M", time.localtime(t))


def kind_of(x):
    """An experiment finds out something about you; a goal gets you something you want. Older ones have no kind."""
    return x.get("kind", "experiment")


class Ember:
    def __init__(self, now=None):
        now = time.time() if now is None else now
        self.born = now
        self.memories = []           # {id, kind, note, quote, t, edited}
        self.next_id = 1
        self.talk = []               # {t, who: "you"|"ember", text, face?}
        self.outbox = []             # talk lines not yet written to conversation.jsonl
        self.connection = 0.3        # grows with real time apart, eased by your presence and talk
        self.curiosity = 0.6         # grows while it learns nothing new about you, eased by new things
        self.bump = 0.0              # a short lift in mood from something good just now
        self.last_update = now
        self.last_seen = None        # the last moment you were here (window open and visible)
        self.arrived_at = None
        self.gap_before = 0.0        # how long you'd been away when you last arrived
        self.expr, self.expr_until = "calm", 0.0
        self.poke_until = 0.0
        self.pokes = 0
        self.asked = []              # template mind: questions already asked
        self.experiments = []        # {id, kind?, title, question, why, based_on, days, steps: [{text, done}], status,
                                     #  created, started, ends_at, ended}; status: suggested|active|done|dropped|not_picked
                                     #  kind "goal": question is what having it looks like (no kind: an experiment)
        self.next_exp = 1
        self.sessions = []           # finished work sessions {exp, start, end, ended_by, rating, words}
        self.session = None          # the open one {exp, start}
        self.checkin_due = False     # a session just ended and it wants to hear how it went

    # ------------------------------------------------------------- saving
    def to_dict(self):
        d = dict(self.__dict__)
        d.pop("outbox")
        return d

    @classmethod
    def from_dict(cls, d):
        e = cls(now=d.get("born"))
        for k, v in d.items():
            if k in e.__dict__:
                setattr(e, k, v)
        return e

    # --------------------------------------------------------- real time
    def update(self, now, present):
        """Let real time act on its wants. Call often; dt can be days."""
        dt = max(0.0, now - self.last_update)
        self.last_update = now
        if present:
            self.connection *= math.exp(-dt / 600)                    # eased within minutes of you being here
            self.last_seen = now
        else:
            self.connection += (1 - self.connection) * (1 - math.exp(-dt / 86400))   # grows over about a day
        self.curiosity += (1 - self.curiosity) * (1 - math.exp(-dt / (2 * 86400)))
        self.bump *= math.exp(-dt / 300)
        if self.session and now - self.session["start"] > SESSION_CAP:
            self.stop_session(self.session["start"] + SESSION_CAP, ended_by="it ran 8 hours")
        x = self.active()
        if x and now >= x["ends_at"] and not x.get("time_up"):
            x["time_up"] = True      # it says so once; the window shows "finish" and "more days" under it
            if kind_of(x) == "goal":
                said = (f"That's the {x['days']} days you gave \"{x['title']}\". Did you get there? Shall we finish "
                        "it and look back, or keep going a bit longer?")
            else:
                said = (f"That's the {x['days']} days of \"{x['title']}\". Shall we finish it and look back at what "
                        "happened, or keep going a few more days?")
            self._say(now, "ember", said, "curious", timeup=x["id"])

    def resume(self, now):
        """Its program just started. A session left open while it was closed ended when it closed."""
        if self.session and now - self.last_update > CLOSED_ENDS:
            self.stop_session(self.last_update, ended_by="Ember was closed")
            return True
        return False

    def arrive(self, now):
        """You opened its window (visible). Returns True if it should greet you."""
        gap = now - self.last_seen if self.last_seen else None
        self.update(now, present=False)
        self.arrived_at = now
        self.gap_before = gap or 0.0
        if gap is None or gap >= GREET_AFTER:
            self.bump += 0.6 * self.connection + 0.2
            return True
        return False

    def poke(self, now):
        self.pokes += 1
        self.poke_until = now + 1.2
        self.connection *= 0.97
        self.bump = min(1.0, self.bump + 0.05)

    @property
    def mood(self):
        return max(0.0, min(1.0, 0.5 - 0.4 * self.connection + 0.45 * self.bump))

    # --------------------------------------------------------------- face
    def face(self, now, present, thinking=False):
        """Its face, and why: every part comes from a number in it."""
        why = []
        if thinking:
            ex = "thinking"
            why.append("its mind is working on what to say")
        elif now < self.expr_until:
            ex = self.expr
            why.append(f"its mind chose '{self.expr}' with its last words")
        elif self.session:
            ex = "focused"
            why.append(f"you're in a work session ({ago(now - self.session['start'])} so far)")
        elif self.arrived_at and now - self.arrived_at < 6 and self.gap_before >= GREET_AFTER:
            ex = "surprised" if self.gap_before > 86400 else "happy"
            why.append(f"you just came back after {ago(self.gap_before)}")
        elif self.connection > 0.6:
            ex = "droopy"
            why.append(f"its want for connection is high ({self.connection:.2f})")
        elif self.curiosity > 0.65:
            ex = "curious"
            why.append(f"its curiosity is high ({self.curiosity:.2f}): it hasn't learned anything new about you lately")
        elif self.mood > 0.62:
            ex = "happy"
            why.append(f"its mood is good ({self.mood:.2f})")
        else:
            ex = "calm"
            why.append("nothing stands out")
        why.append(f"glow = mood {self.mood:.2f} (connection {self.connection:.2f}, recent lift {self.bump:.2f})")
        why.append("it looks at you" if present else "nobody is here")
        return {"expression": ex, "glow": round(self.mood, 3), "wiggle": now < self.poke_until,
                "gaze": "you" if present else "away", "why": why}

    # ------------------------------------------------------------ talking
    def _say(self, now, who, text, face=None, **extra):
        line = {"t": now, "who": who, "text": text}
        if face:
            line["face"] = face
        line.update(extra)          # exps: experiments it suggested with these words; checkin: it asks how a session
                                    # went; timeup: an experiment's days are up; review: it looks back on one
        self.talk.append(line)
        self.talk = self.talk[-TALK_KEPT:]
        self.outbox.append(line)

    def say(self, now, text, face=None, **extra):
        """Something Ember says that doesn't come from its mind (e.g. that its mind can't be reached)."""
        self._say(now, "ember", text, face, **extra)

    def hear(self, now, text):
        """You wrote something. It goes into the conversation; the mind answers after."""
        self.update(now, present=True)
        self._say(now, "you", text)
        self.connection *= 0.85
        self.bump = min(1.0, self.bump + 0.1)

    def prompt(self, event, now):
        """(system, user) for its mind. event types: talk {text}, arrive, suggest, checkin {text, rating, minutes},
        review {id}."""
        lines = [f"Now: {when(now)}."]
        lines.append(f"You first appeared {ago(now - self.born)} ago." if self.talk[:-1] or self.memories
                     else "You are meeting this person for the first time.")
        if event["type"] == "arrive" and self.gap_before:
            lines.append(f"They were away for {ago(self.gap_before)} before now.")
        lines.append(f"Your wants now: connection {self.connection:.2f} (grows while they're away), "
                     f"curiosity {self.curiosity:.2f} (grows while you learn nothing new about them).")
        lines.append("")
        if self.memories:
            lines.append("What you remember about them:")
            for m in self.memories:
                lines.append(f"- {m['id']} [{m['kind']}] {m['note']} (they said \"{m['quote']}\", "
                             f"{time.strftime('%d %b', time.localtime(m['t']))})")
        else:
            lines.append("You don't remember anything about them yet.")
        lines += self._experiment_context(now)
        recent = self.talk[-CONTEXT_LINES:]
        if event["type"] in ("talk", "checkin") and recent and recent[-1]["who"] == "you":
            recent = recent[:-1]
        if recent:
            lines.append("")
            lines.append("Recent conversation:")
            for l in recent:
                who = "They" if l["who"] == "you" else "You"
                lines.append(f"[{time.strftime('%d %b %H:%M', time.localtime(l['t']))}] {who}: {l['text']}")
        lines.append("")
        if event.get("mode") == "work":
            lines.append("They're in work mode: they want to work on their goal or experiment, or set one up.")
        if event["type"] == "talk":
            lines.append(f"Their latest message: \"{event['text']}\"")
        elif event["type"] == "suggest" and self.knows_enough():
            lines.append("They asked you to suggest experiments. Suggest 2 or 3 in \"experiments\", each different, "
                         "each built on things you remember about them (cite the ids in based_on). Your reply: one or "
                         "two sentences introducing them. remember, update and add_steps must be empty.")
        elif event["type"] == "suggest":
            lines.append("They asked you to suggest experiments, but you barely know them yet. Suggest 2 or 3 starter "
                         "experiments in \"experiments\", each different and doable on their own (no asking other "
                         "people), that help them find out what they enjoy "
                         "(based_on: the ids of any memories they rest on, or empty). Say plainly in your reply that "
                         "these are starting points because you don't know them yet. remember, update and add_steps "
                         "must be empty.")
        elif event["type"] == "checkin":
            lines.append(f"They just finished a work session of {event['minutes']} minutes and rated how it went "
                         f"{event['rating']}/5" + (f", saying: \"{event['text']}\"" if event["text"] else "") + ". "
                         "Respond briefly to how it went, and agree on the next small step: propose it in your reply "
                         "and put it in add_steps.")
        elif event["type"] == "review" and self.find_exp(event.get("id")):
            x = self.find_exp(event["id"])
            f = x.get("facts") or self.facts(x, now)
            how = "finished" if x["status"] == "done" else "dropped"
            if kind_of(x) == "goal":
                lines.append(f"Their goal \"{x['title']}\" just ended: they {how} it on day {f['days_lasted']} of "
                             f"{x['days']}. They'd know they were there when: {x['question']}")
                lines.append("What actually happened: " + self.facts_text(f))
                lines.append("Look back on it honestly in 3 to 5 short sentences: how far they got, what helped and "
                             "what got in the way, as the numbers and their words show. Use only these facts, their "
                             "words and your memories; if there's too little to tell, say so plainly. Dropping a goal "
                             "they no longer want is fine. No praise, no blame, no pep talk. End by asking whether they "
                             "got what they wanted, or what they want next. remember, update, add_steps and "
                             "experiments must be empty; goal must be null.")
            else:
                lines.append(f"The experiment \"{x['title']}\" just ended: they {how} it on day {f['days_lasted']} of "
                             f"{x['days']}. Its question was: {x['question']}")
                lines.append("What actually happened: " + self.facts_text(f))
                lines.append("Look back on it honestly in 3 to 5 short sentences: what the numbers show, and what they "
                             "suggest about its question. Use only these facts, their words and your memories; if "
                             "there's too little to tell, say so plainly. Dropping it is a result too. No praise, no "
                             "blame, no pep talk. End by asking them their own answer to its question. remember, "
                             "update, add_steps and experiments must be empty; goal must be null.")
        elif not self.memories and len(self.talk) == 0:
            lines.append("They just opened your window for the very first time. Introduce yourself in one or two "
                         "sentences and ask one first question to get to know them. remember and update must be empty.")
        else:
            lines.append("They just opened your window again. Greet them in one or two sentences; you may pick up a "
                         "thread from your memories or the conversation. remember and update must be empty.")
        return SYSTEM, "\n".join(lines)

    def respond(self, event, raw, now):
        """Apply what its mind answered (raw JSON text), or the template mind if raw is None/unusable.
        Returns what changed: {"reply", "face", "remembered": [...], "updated": [...], "dropped": [...]}."""
        from .llm import parse_json
        d = parse_json(raw) if raw else None
        if not isinstance(d, dict) or not str(d.get("reply", "")).strip():
            d = self._template(event, now)
            d["by"] = "template"
        result = {"reply": str(d["reply"]).strip()[:1200], "face": d.get("face") if d.get("face") in FACES else "calm",
                  "remembered": [], "updated": [], "dropped": [], "by": d.get("by", "mind")}
        said = event.get("text", "") if event["type"] in ("talk", "checkin") else ""
        for r in (d.get("remember") or []) if said else []:
            m = self._add_memory(r, said, now)
            (result["remembered"] if m else result["dropped"]).append(m or r)
        for u in (d.get("update") or []) if said else []:
            m = self._update_memory(u, said, now)
            (result["updated"] if m else result["dropped"]).append(m or u)
        active = self.active()
        if active and event["type"] in ("talk", "checkin"):
            for st in d.get("done_steps") or []:
                step = next((x for x in active["steps"] if _norm(x["text"]) == _norm(st) and not x["done"]), None)
                if step:
                    step["done"] = True
                    result.setdefault("done", []).append(step["text"])
            for st in (d.get("add_steps") or [])[:3]:
                st = str(st).strip()[:160]
                if st and not any(_norm(st) == _norm(x["text"]) for x in active["steps"]):
                    active["steps"].append({"text": st, "done": False})
                    result.setdefault("steps", []).append(st)
            plan = str(d.get("replan") or "").strip()[:600]
            if plan and kind_of(active) == "goal" and plan != active.get("plan"):
                active["plan"] = plan            # you agreed to change the way there
                result["replanned"] = plan
        if event["type"] == "suggest":
            result["suggested"] = self._take_suggestions(d.get("experiments"), now)
            if not result["suggested"] and result["by"] != "template":
                t = self._template(event, now)          # its mind's suggestions didn't rest on its memories
                result["suggested"] = self._take_suggestions(t.get("experiments"), now)
                result["reply"] = t["reply"]
        elif event["type"] == "talk" and isinstance(d.get("goal"), dict) and self.can_suggest():
            result["suggested"] = self._take_goal(d["goal"], now)                    # you said what you want
        elif event["type"] == "talk" and d.get("experiments") and self.can_suggest():
            result["suggested"] = self._take_suggestions(d.get("experiments"), now)   # you asked what to try
        self.update(now, present=True)
        extra = {"exps": [x["id"] for x in result["suggested"]]} if result.get("suggested") else {}
        x = self.find_exp(event.get("id")) if event["type"] == "review" else None
        if x:
            x["review"] = result["reply"]
            extra["review"] = x["id"]
        self._say(now, "ember", result["reply"], result["face"], **extra)
        self.expr, self.expr_until = result["face"], now + EXPR_SECONDS
        return result

    # ------------------------------------------------------------- memory
    def _source_ok(self, quote, said):
        q = _norm(quote)
        return len(q) >= 2 and q in _norm(said)

    def _similar(self, note):
        w = _words(note)
        for m in self.memories:
            mw = _words(m["note"])
            if w and mw and len(w & mw) / len(w | mw) >= 0.6:
                return m
        return None

    def _add_memory(self, r, said, now):
        if not isinstance(r, dict):
            return None
        note, quote, kind = str(r.get("note", "")).strip()[:200], str(r.get("quote", "")).strip()[:300], r.get("kind")
        if not note or kind not in KINDS or not self._source_ok(quote, said) or self._similar(note):
            return None              # no source in your words, or it already knows this: not kept, not new
        m = {"id": f"m{self.next_id}", "kind": kind, "note": note, "quote": quote, "t": now, "edited": None}
        self.next_id += 1
        self.memories.append(m)
        self.curiosity *= 0.75       # something new about you
        self.bump = min(1.0, self.bump + 0.1)
        return m

    def _update_memory(self, u, said, now):
        if not isinstance(u, dict):
            return None
        m = self.find(u.get("id"))
        note, quote = str(u.get("note", "")).strip()[:200], str(u.get("quote", "")).strip()[:300]
        if not m or not note or not self._source_ok(quote, said):
            return None
        m.update(note=note, quote=quote, t=now)
        return m

    def find(self, mid):
        return next((m for m in self.memories if m["id"] == mid), None)

    def edit_memory(self, mid, note, now):
        """You corrected a memory yourself on its memory page."""
        m = self.find(mid)
        if not m or not str(note).strip():
            return False
        m["note"], m["edited"] = str(note).strip()[:200], now
        return True

    def forget(self, mid):
        """You deleted a memory on its memory page. It is gone from Ember (not kept anywhere)."""
        n = len(self.memories)
        self.memories = [m for m in self.memories if m["id"] != mid]
        return len(self.memories) < n

    # ------------------------------------------------- the template mind
    def _next_question(self):
        for i, q in enumerate(QUESTIONS):
            if i not in self.asked:
                self.asked.append(i)
                return q
        return "Tell me more about your days?"

    def _template(self, event, now):
        """A simple mind with no LLM: it keeps what you say about yourself and asks questions."""
        if event["type"] == "arrive":
            if not self.memories and len(self.talk) == 0:
                return {"reply": "Hi. I'm Ember. I live here, in this window, and I want to get to know you. "
                                 + self._next_question(), "face": "happy"}
            return {"reply": f"You're back. It's been {ago(self.gap_before)}. " + self._next_question(),
                    "face": "happy"}
        if event["type"] == "suggest":
            return self._template_suggest()
        if event["type"] == "review" and self.find_exp(event.get("id")):
            x = self.find_exp(event["id"])
            return {"reply": "What happened: " + self.facts_text(x.get("facts") or self.facts(x, now))
                             + f" What's your own answer to its question: {x['question']}", "face": "calm"}
        if event["type"] == "checkin":
            st = self.stats(self.active()["id"]) if self.active() else None
            more = f" That's {fmt_minutes(st['seconds'])} on it so far." if st else ""
            return {"reply": f"Thanks for telling me.{more} What's the next small step?", "face": "happy"}
        text = event["text"]
        remember = []
        for s in re.split(r"(?<=[.!?])\s+|\n", text):
            s = s.strip()
            if re.match(r"(?i)(i|i'm|i am|i've|i have|my)\b", s) and len(s.split()) >= 3:
                remember.append({"kind": "about", "note": s[:200], "quote": s})
        if remember:
            return {"reply": "I'll remember that. " + self._next_question(), "face": "curious", "remember": remember}
        return {"reply": "Tell me more? " + self._next_question(), "face": "curious"}

    def _template_suggest(self):
        if not self.knows_enough():
            return {"reply": "I don't know you yet, so here are a few starting points for finding out what you enjoy.",
                    "face": "eager", "experiments": [dict(x, based_on=[]) for x in STARTERS]}
        picks = [m for m in self.memories if m["kind"] in ("flow", "enjoys", "wants", "good_at")] or self.memories
        exps = [{"title": f"A week of: {m['note']}"[:80], "question": "Do you still want to keep going on day 5?",
                 "why": f"You told me: \"{m['quote']}\"", "based_on": [m["id"]], "days": 7,
                 "steps": ["Pick one small thing to make or do", "Work on it for 30 minutes",
                           "Write down how it felt"]} for m in picks[-3:]]
        return {"reply": "Here are a few small experiments, each from something you told me.", "face": "eager",
                "experiments": exps}

    # -------------------------------------------------------- experiments
    def active(self):
        return next((x for x in self.experiments if x["status"] == "active"), None)

    def find_exp(self, eid):
        return next((x for x in self.experiments if x["id"] == eid), None)

    def can_suggest(self):
        return not self.active()

    def knows_enough(self):
        """Enough to build experiments on what it knows; before that, starter experiments."""
        return len(self.memories) >= MIN_MEMORIES

    def _take_suggestions(self, exps, now):
        """Its mind's suggestions; each must rest on memories it really has."""
        kept = []
        for x in (exps or [])[:3]:
            if not isinstance(x, dict):
                continue
            based = [b for b in (x.get("based_on") or []) if self.find(b)]
            title, question = str(x.get("title", "")).strip()[:80], str(x.get("question", "")).strip()[:200]
            if (not based and self.knows_enough()) or not title or not question:
                continue             # once it knows you, every idea must rest on something you told it
            try:
                days = max(3, min(14, int(x.get("days", 7))))
            except (TypeError, ValueError):
                days = 7
            steps = [{"text": str(st).strip()[:160], "done": False}
                     for st in (x.get("steps") or [])[:5] if str(st).strip()]
            kept.append({"id": f"x{self.next_exp}", "title": title, "question": question,
                         "why": str(x.get("why", "")).strip()[:240], "based_on": based, "starter": not based,
                         "days": days, "steps": steps,
                         "status": "suggested", "created": now, "started": None, "ends_at": None, "ended": None})
            self.next_exp += 1
        if kept:
            for x in self.experiments:
                if x["status"] == "suggested":
                    x["status"] = "not_picked"
            self.experiments += kept
        return kept

    def _take_goal(self, g, now):
        """A goal its mind proposes from what you said you want; you decide whether it becomes yours."""
        title, done_when = str(g.get("title", "")).strip()[:80], str(g.get("done_when", "")).strip()[:200]
        if not title or not done_when:
            return []
        try:
            days = max(GOAL_DAYS[0], min(GOAL_DAYS[1], int(g.get("days", 30))))
        except (TypeError, ValueError):
            days = 30
        steps = [{"text": str(st).strip()[:160], "done": False} for st in (g.get("steps") or [])[:8] if str(st).strip()]
        x = {"id": f"x{self.next_exp}", "kind": "goal", "title": title, "question": done_when,
             "plan": str(g.get("plan", "")).strip()[:600],
             "why": str(g.get("why", "")).strip()[:240], "based_on": [b for b in (g.get("based_on") or []) if self.find(b)],
             "starter": False, "days": days, "steps": steps,
             "status": "suggested", "created": now, "started": None, "ends_at": None, "ended": None}
        self.next_exp += 1
        for y in self.experiments:
            if y["status"] == "suggested":
                y["status"] = "not_picked"
        self.experiments.append(x)
        return [x]

    def pick(self, eid, now):
        x = self.find_exp(eid)
        if not x or x["status"] != "suggested" or self.active():
            return False
        x.update(status="active", started=now, ends_at=now + x["days"] * 86400)
        for y in self.experiments:
            if y["status"] == "suggested":
                y["status"] = "not_picked"
        first = next((s["text"] for s in x["steps"] if not s["done"]), None)
        if kind_of(x) == "goal":
            said = f"Your goal: \"{x['title']}\", in {x['days']} days. You'll know you're there when: {x['question']}"
        else:
            said = f"\"{x['title']}\" it is: {x['days']} days, and one question: {x['question']}"
        self._say(now, "ember", said + (f" First step: {first}" if first else ""), "eager")
        self.expr, self.expr_until = "eager", now + EXPR_SECONDS
        return True

    def set_step(self, eid, index, done):
        x = self.find_exp(eid)
        if not x or not isinstance(index, int) or not (0 <= index < len(x["steps"])):
            return False
        x["steps"][index]["done"] = bool(done)
        return True

    def end_experiment(self, eid, how, now):
        x = self.find_exp(eid)
        if not x or x["status"] != "active" or how not in ("done", "dropped"):
            return False
        if self.session:
            self.stop_session(now, ask=False)
        self.checkin_due = False
        x.update(status=how, ended=now)
        x["facts"] = self.facts(x, now)
        return True

    def extend(self, eid, now, days=None):
        """Its days are up and you want to keep going: a few more days (a week for a goal)."""
        x = self.find_exp(eid)
        if not x or x["status"] != "active":
            return False
        days = days or MORE_DAYS[kind_of(x)]
        x["ends_at"] = max(x["ends_at"], now) + days * 86400
        x["days"] = round((x["ends_at"] - x["started"]) / 86400)
        x["time_up"] = False
        self._say(now, "ember", f"{days} more days of \"{x['title']}\", so {x['days']} in all.", "eager")
        return True

    def facts(self, x, now):
        """What actually happened in an experiment: numbers from its sessions, and your own words after them."""
        ss = [s for s in self.sessions if s["exp"] == x["id"]]
        end = x["ended"] or now
        return {"days_lasted": max(1, math.ceil((end - x["started"]) / 86400)), "sessions": len(ss),
                "work_days": len({time.strftime("%Y-%m-%d", time.localtime(s["start"])) for s in ss}),
                "seconds": sum(s["end"] - s["start"] for s in ss),
                "ratings": [s["rating"] for s in ss if s.get("rating")],
                "steps_done": sum(s["done"] for s in x["steps"]), "steps": len(x["steps"]),
                "words": [s["words"] for s in ss if s.get("words")][-8:],
                "each": [{"day": int((s["start"] - x["started"]) // 86400) + 1, "seconds": s["end"] - s["start"],
                          "rating": s.get("rating"), "words": s.get("words")} for s in ss][-12:]}

    @staticmethod
    def facts_text(f):
        out = (f"{f['sessions']} work session{'' if f['sessions'] == 1 else 's'} on {f['work_days']} "
               f"day{'' if f['work_days'] == 1 else 's'}, {fmt_minutes(f['seconds'])} in all; "
               f"{f['steps_done']} of {f['steps']} steps done.")
        if f.get("each"):
            out += " Each session: " + "; ".join(
                f"day {s['day']}, {fmt_minutes(s['seconds'])}" + (f", felt {s['rating']}/5" if s["rating"] else "")
                + (f", they said \"{s['words']}\"" if s["words"] else "") for s in f["each"]) + "."
        return out

    def start_session(self, now):
        x = self.active()
        if not x or self.session:
            return False
        self.session = {"exp": x["id"], "start": now}
        self.checkin_due = False
        return True

    def stop_session(self, now, ended_by="you", ask=True):
        if not self.session:
            return None
        s = dict(self.session, end=max(now, self.session["start"]), ended_by=ended_by, rating=None, words=None)
        self.sessions.append(s)
        self.session = None
        if ask:                      # it asks in the conversation; the window shows 1-5 under the question
            self.checkin_due = True
            how_long = fmt_minutes(s["end"] - s["start"])
            why = "" if ended_by == "you" else f" (it ended because {ended_by})"
            self._say(s["end"], "ember", f"That was {how_long} of work{why}. How did it go?", "curious", checkin=True)
        return s

    def checkin(self, now, rating, words):
        """How the session that just ended went. Returns the event for its mind, or None."""
        if not self.checkin_due or not self.sessions:
            return None
        s = self.sessions[-1]
        s["rating"], s["words"] = rating, words
        self.checkin_due = False
        minutes = round((s["end"] - s["start"]) / 60)
        self.update(now, present=True)
        self._say(now, "you", f"[work session: {fmt_minutes(s['end'] - s['start'])}, felt {rating}/5]" + (f" {words}" if words else ""))
        self.bump = min(1.0, self.bump + 0.1)
        return {"type": "checkin", "text": words or "", "rating": rating, "minutes": minutes}

    def stats(self, eid):
        ss = [s for s in self.sessions if s["exp"] == eid]
        rated = [s["rating"] for s in ss if s.get("rating")]
        return {"sessions": len(ss), "seconds": sum(s["end"] - s["start"] for s in ss),
                "avg_rating": round(sum(rated) / len(rated), 1) if rated else None}

    def _experiment_context(self, now):
        x = self.active()
        out = []
        if x:
            st = self.stats(x["id"])
            day = int((now - x["started"]) // 86400) + 1
            if kind_of(x) == "goal":
                out += ["", f"Their goal, which you work on together: \"{x['title']}\" (day {day} of {x['days']}). "
                            f"They'll know they're there when: {x['question']}" + (f" Why: {x['why']}" if x["why"] else "")]
                if x.get("plan"):
                    out.append(f"The plan you agreed: {x['plan']}")
            else:
                out += ["", f"Your experiment together: \"{x['title']}\" (day {day} of {x['days']}). "
                            f"Its question: {x['question']}"]
            for s in x["steps"]:
                out.append(f"  [{'x' if s['done'] else ' '}] {s['text']}")
            out.append(f"So far: {fmt_minutes(st['seconds'])} in {st['sessions']} work sessions"
                       + (f", average feeling {st['avg_rating']}/5." if st["avg_rating"] else "."))
            if self.session:
                out.append(f"They are in a work session on it right now ({ago(now - self.session['start'])} so far). "
                           "Help with the work if they ask; keep it short so they can keep working.")
        if not x:
            out.append("")
            out.append("You may suggest experiments (in \"experiments\") if they ask what they could try"
                       + ("." if self.knows_enough() else ": starter ones, since you don't know them well yet.")
                       + " If they say what they want to get or achieve, you may propose it as a goal (in \"goal\").")
        else:
            out.append("They can have one goal or experiment at a time: to start another, they first finish or drop "
                       f"\"{x['title']}\". So \"goal\" must be null and \"experiments\" empty.")
        sug = [x for x in self.experiments if x["status"] == "suggested"]
        if sug:
            out += ["", "What you proposed, waiting for them to pick it: "
                    + "; ".join(f"{kind_of(x)} \"{x['title']}\"" for x in sug)]
        for x in [x for x in self.experiments if x["status"] in ("done", "dropped")][-3:]:
            st = self.stats(x["id"])
            out.append(f"Earlier {kind_of(x)} \"{x['title']}\": {x['status']}, {fmt_minutes(st['seconds'])} in "
                       f"{st['sessions']} sessions." + (f" Your look back: {x['review']}" if x.get("review") else ""))
        return out

    # ------------------------------------------------------- the window
    def snapshot(self, now, present, thinking=False):
        x = self.active()
        exp = dict(x, stats=self.stats(x["id"]), day=int((now - x["started"]) // 86400) + 1) if x else None
        return {"face": self.face(now, present, thinking), "connection": round(self.connection, 3),
                "curiosity": round(self.curiosity, 3), "mood": round(self.mood, 3),
                "talk": self.talk[-60:], "memories": len(self.memories), "thinking": thinking,
                "last_seen": self.last_seen, "now": now,
                "experiment": exp, "suggestions": [x for x in self.experiments if x["status"] == "suggested"],
                "exps": {x["id"]: x for x in self.experiments},
                "session": self.session, "checkin_due": self.checkin_due,
                "can_suggest": self.can_suggest(), "knows_enough": self.knows_enough(),
                "past": sum(x["status"] in ("done", "dropped") for x in self.experiments),
                "memory_notes": {m["id"]: m["note"] for m in self.memories}}

    def memory_page(self):
        groups = {k: [] for k in KINDS}
        for m in self.memories:
            groups.setdefault(m["kind"], []).append(m)
        return {"labels": KINDS, "groups": groups, "count": len(self.memories)}


def dumps(ember):
    return json.dumps(ember.to_dict(), ensure_ascii=False, indent=1)
