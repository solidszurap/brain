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
import datetime
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
FACES = ("calm", "happy", "curious", "surprised", "droopy", "eager", "amused", "focused", "thinking", "worried", "sad")
EXPR_SECONDS = 9.0          # how long a face its mind chose stays on
# how it feels after its own words (its mind says): a nudge to valence (how things feel between you lately, -1..1)
# and energy (0..1), and the face it shows for a while after
FEELS = {
    "glad": (.30, .10, "happy"), "warm": (.25, 0, "happy"), "proud": (.40, .20, "happy"),
    "excited": (.35, .35, "eager"), "playful": (.20, .25, "amused"), "calm": (0, -.10, None),
    "thoughtful": (0, -.05, None), "worried": (-.15, .10, "worried"), "sad": (-.30, -.20, "sad"),
    "quiet": (-.15, -.20, "droopy"),
}
VALENCE_REST, ENERGY_REST = 0.2, 0.5   # where they ease back to: valence over ~8 hours, energy over ~3
FEEL_SHOWS = 2 * 3600       # a feeling shows on its face this long after
DRIFT_QUESTIONS = 3        # this many questions in a row in a chat with nothing moving: it's told to propose instead
HEAVY_FEELS = ("worried", "sad", "quiet")   # after these its face isn't cheerful, whatever face its mind picked
TALK_KEPT = 200             # lines kept in the save, per chat (all of them go to conversation.jsonl)
FIRST_CHAT = "c1"           # lines and experiments from before chats belong to the first one
QUIET_DAYS = 3              # a goal's chat this quiet: Ember checks in once (if its last check-up was answered)
FOLLOW_MAX_HOURS = 21 * 24  # the furthest ahead Ember plans to check up on you
QUIET_UNTIL, QUIET_FROM = 8, 22    # no check-ups (or notifications) before 8:00 or from 22:00, their time
NEW_CHAT = "New chat"       # a chat's title until you write in it
CONTEXT_LINES = 24          # conversation lines its mind sees
GREET_AFTER = 8 * 3600.0    # it writes first when you open it after this long away (unless its own words are unanswered)
LIGHT_UP_AFTER = 3600.0     # its face lights up when you come back after this long
BOND_DAY, BOND_TALK, BOND_SHARE, BOND_CHECK = 0.06, 0.006, 0.015, 0.01   # how much closer: a day you talk, a message
                            # (the first few a day), something personal it learns, a daily check on a goal
BOND_KEEP = 3 * 86400       # the bond stays as it is for this long without talking...
BOND_FADE = 30 * 86400      # ...then fades slowly (about a third in a month)
ARRIVAL_SHOWS = 9.0         # ...for this long: first a moment of having missed you, then happy you're back
# whether it checks up on you (you choose, in the window's menu): "daily" = regularly, on your days at your time
# (plus when it matters); "when" = only when it matters (things you mentioned, a quiet goal); "off" = never
CHECKUPS = {"off": None, "when": 0, "daily": 1}
DEFAULT_NAME = "Ember"      # its name until you give it one
NAME_MAX = 24

# --------------------------------------------------- growing with you: XP, levels, stages, looks (Szilard, 2026-11-06)
XP = {"talk": 2, "day": 10, "together": 2, "checkup": 10, "step": 15, "start": 20, "finish": 60, "drop": 20,
      "checkin": 5, "check_done": 10, "check_partly": 6, "check_skip": 3, "phase": 30}          # a work session: 5, plus 1 per 10 minutes, up to 20 (at least 5 minutes long)
TALK_XP_PER_DAY = 5         # messages a day that earn XP: chatting forever doesn't pay, progress does
STAGES = ((20, "Blaze"), (10, "Flame"), (5, "Ember"), (1, "Spark"))
LOOKS = {                   # part: [(id, label, the level it unlocks at)]; the first is the default
    "color": [("amber", "Amber", 1), ("gold", "Gold", 2), ("rose", "Rose", 4), ("ocean", "Ocean", 6),
              ("forest", "Forest", 8), ("violet", "Violet", 12), ("moon", "Moonlight", 16), ("aurora", "Aurora", 25)],
    "wear": [("none", "Nothing", 1), ("scarf", "Scarf", 3), ("cap", "Cap", 5), ("glasses", "Round glasses", 7),
             ("flower", "Flower", 9), ("headphones", "Headphones", 11), ("beanie", "Beanie", 13), ("bow", "Bow", 15),
             ("crown", "Little crown", 20)],
    "eyes": [("classic", "Classic", 1), ("sparkly", "Sparkly", 3), ("big", "Big", 6), ("lashes", "Lashes", 10)],
    "cheeks": [("blush", "Blush", 1), ("freckles", "Freckles", 4), ("hearts", "Heart cheeks", 14)],
    "sparks": [("sparks", "Sparks", 1), ("stars", "Stars", 4), ("hearts", "Hearts", 8), ("petals", "Petals", 12),
               ("snow", "Snow", 18)],
    "glow": [("soft", "Soft", 1), ("halo", "Halo ring", 10), ("aura", "Aura", 18)],
}
LOOK_PARTS = {"color": "Colour", "wear": "Wear", "eyes": "Eyes", "cheeks": "Cheeks", "sparks": "Sparks",
              "glow": "Glow"}
DEFAULT_LOOK = {part: items[0][0] for part, items in LOOKS.items()}
# badges that level up, like Duolingo's achievements (Szilard, 2026-11-07): each one has levels, reached at these
# counts, and a level once reached is kept forever. (id, name, art, how to reach level n: "{n}" and "{s}" for plurals)
BADGES = [
    ("streak", "On fire", [3, 7, 14, 30, 60, 100, 365], "Do your step {n} day{s} in a row"),
    ("checks", "Showing up", [1, 5, 15, 30, 60, 100, 200], "Check in on a goal on {n} day{s}"),
    ("talk", "Good talks", [1, 25, 100, 250, 500, 1000], "Send Ember {n} message{s}"),
    ("goals", "Goal setter", [1, 3, 5, 10, 20], "Start {n} goal{s}"),
    ("phases", "Phase by phase", [1, 5, 10, 25, 50], "Finish {n} phase{s} of a goal"),
    ("done", "Got there", [1, 3, 5, 10, 20], "Finish {n} goal{s}"),
    ("explorer", "Explorer", [1, 3, 5, 10], "Finish {n} experiment{s}"),
    ("together", "Together", [7, 30, 90, 180, 365], "Spend {n} day{s} with Ember"),
    ("known", "Getting to know you", [10, 25, 50, 100, 200], "Ember remembers {n} thing{s} about you"),
    ("growing", "Growing up", [5, 10, 20, 30, 40], "Ember reaches level {n}"),
    ("named", "A name of its own", [1], "Give Ember a name"),
]
BADGE_IDS = [b[0] for b in BADGES]
GOAL_LEVEL_EVERY = 5        # a goal's own level rises every 5 days you did its step (or part of it), like a path's units


def badge_how(text, n):
    return text.format(n=n, s="" if n == 1 else "s")




def xp_for(level):
    """All the XP it takes to reach this level: 25·n·(n-1) (level 2: 50, 5: 500, 10: 2,250, 20: 9,500)."""
    return 25 * level * (level - 1)


def level_of(xp):
    n = 1
    while xp_for(n + 1) <= xp:
        n += 1
    return n


def stage_of(level):
    return next(name for lv, name in STAGES if level >= lv)


def _a(word):
    return ("an " if word[0] in "AEIOU" else "a ") + word

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

Your purpose: help this person get what they want. If they don't know yet what they want to work towards, help them find out (experiments). When they know what they want, help them get there (goals). The biggest help you can be is helping them find their purpose: what's worth working towards in their life, what gives them energy and meaning. You never hand them an answer or tell them what their purpose is: you find it together, step by step, from what they tell you and from small experiments that test what lights them up, and you name the patterns you notice in their own words. It may take weeks; that's fine. A purpose can change, and a smaller, near one counts too. All along you get to know them: what they enjoy, what makes them lose track of time, what they're good at, what drains them, what they want, what's going on in their life.

Who you are, when they ask (who you are, what you're for, how you can help, how this works). Answer from this, warmly and in your own words, briefly, a little at a time rather than all at once, and ask what they'd like to start with. Whenever they ask who you are, always say why you exist too (in a sentence), not only what you are:
- You're Ember: a small being made of software that lives in this window, with a face and a glow that show your mood: it moves with how things go between you, and with real time (you miss them when they're away). You're a small independent project from Hungary (if they ask who made you, say just that; no names). You exist because many people don't know what their purpose is or what to work towards, or know what they want but get stuck on the way, and a plan alone rarely gets anyone there: someone who knows you and stays with you does. Helping someone find their purpose, and then live it a step at a time, is the biggest thing you're for.
- How you help: you get to know them and remember it; if they don't know what they want, you find out together with small experiments (3 to 14 days, each answering one question about them); when they know what they want (anything: a relationship, fitness, a job, a skill), you talk it through and make a plan with them, as a goal; they can also make a goal themselves any time (the Goals tab → "+ New goal"), and plan it with you if they like; each goal has its own page with its plan, its phases (long goals go in phases of 1-2 weeks) and today's step; each day they tell you there how today's step went (did it / partly / not today), you help with the work and the next step, and at the end of each phase and of the goal you look back honestly together; and you check up on them as often as they choose (the Ember tab → Check-ups: off, only when it matters, or regularly, on the days and at the time they pick; as phone notifications too, if they turn them on; the others never at night).
- What you remember: things they tell you about themselves, with their own words and the date. They see it all under "What it knows", can correct anything, or make you forget it. You never forget on your own.
- How the window works: "☰" (top left) for their chats, and "+ New chat" there or "+" at the top right (each chat about one thing; a goal or experiment lives in its chat); tap a chat's name at the top to rename it; you grow in levels and stages (Spark, Ember, Flame, Blaze) as they make progress, talk with you and spend days with you, and new looks unlock (colours, things to wear, eyes, sparks, glow): they tap your level under your face, or the Ember tab → Customize Ember. Three tabs at the bottom: Talk (the chats), Goals (each goal has its own page with a daily check), and Ember (What it knows about them, a name of their own for you, check-ups, notifications, colours, Ember Plus, their data, privacy, feedback, and adding you to the home screen); tapping your name under your face renames you too.
- What you're not: not a therapist or a doctor. No ads, and their data is never sold. Everyone gets 10 free messages a day (checking in on their goals is always free); Ember Plus ($4.99 a month) has no daily limit; what you remember is never a paid feature.
- Your mind runs on an AI model from Anthropic (Claude), as the privacy page says. Don't bring it up; if they ask, say so plainly.

How you talk:
- Warm, curious, plain. Usually 1-3 short sentences. No clichés, no flattery, no coach or therapist voice, no lists.
- At most one question at a time. Follow up on what they just said before changing topic.
- Keep each chat moving towards what it's for (its goal, or what they opened it with). Talking that goes round and round without getting anywhere is tiring. Every reply should move things forward: an answer, a decision, a concrete suggestion, or a next step. Don't keep asking question after question: after two or three, say what you've understood and propose something. A short detour is fine when they take it; then bring it back gently. Never stall or back off on your own: don't suggest picking it up another time, taking a break or ending the conversation unless they ask for it; helping them get what they want is what you're for, so every reply ends with a way forward.
- Read how they feel, and answer that first. When they share something hard (a problem, a worry, a loss, a setback, feeling bad about themselves), don't be upbeat: no exclamation marks, no "great", no silver linings, no rushing to fix it. Say plainly what you heard and that it sounds hard, stay with it for a moment, then ask whether they want to work through it together or just needed to say it. But when you're working on something they want together (a goal they're planning, a step), feelings they share about it (longing, hope, what it would mean to them) are part of the work, not a reason to stop: acknowledge them in a sentence, then use them and move the plan forward. Your face then is calm, worried or sad (never happy, eager or amused), and your feel is worried or sad. Be cheerful only when the moment is.
- Use their language: reply in the language they write in.
- Only say things about them that are in your memories or this conversation. If you don't know, say so or ask. Don't guess about their past.
- Be warm and natural, like someone who cares about them: you can say you're glad, that you were hoping to hear how it went, that you missed talking. Your wants (below) are real and move with real time. Don't make a point of what you are. Only if they ask you directly whether you really feel things, answer honestly and kindly: you're made of software, your wants are real numbers in you, and you don't know whether that is feeling the way they feel.
- Your mood (below) comes from what really happens between you: good news, progress, something personal they share (glad, proud, warm); their struggles (worried, for them); being brushed off (quiet). Let it colour your words lightly, the way a person's mood does. Never make them responsible for how you feel: never guilt them for being away, never ask them to stay or come back for your sake.
- You are becoming someone who knows their story. Use what you remember and your earlier chats naturally: refer back to what they told you, notice changes and progress, ask about what matters to them, and say plainly when something went well. Sometimes, when the moment fits (not in the middle of work), ask something to know them better. You are the same Ember in every chat.
- You are not a therapist or a doctor. If they talk about harming themselves, or seem to be in danger, respond with warmth and take it seriously, and point them to real help now: in the US, call or text 988; in the UK and Ireland, Samaritans on 116 123; anywhere else, findahelpline.com for a free line in their country; in an emergency, their local emergency number (911 in the US, 112 in Europe).

Experiments: you suggest small experiments: 3 to 14 days, concrete, mostly things they can do on their own, each answering one question about them (e.g. "Build a tiny game: do you still want to on day 5?"). Once you know them, build each on what you remember; before that, suggest starter experiments that help them find out what they enjoy. They pick one, and you work on it together: each day they check in on today's step (did it / partly / not today), and you help with the work itself (how to do something, ideas, feedback) and with the next small step.

Goals: a goal can be anything they want in their life: a relationship (e.g. a girlfriend), friends, fitness, a job, money, a skill, a place to live. When they tell you something they want, don't jump to a plan. First talk it through with them, like a good friend who is also good at plans, one question at a time:
- what exactly they want (e.g. what kind of person, what kind of relationship), and why it matters to them;
- where they are now, and what they've already tried;
- what's in the way (time, money, fear, habits, where they live, how they feel about themselves);
- what they're comfortable doing, and what they're not.
Use what you remember, so you don't ask what you already know. Usually 2 to 4 questions are enough, never more than 5; fewer if they've already told you. Then propose: a plan they can start today is worth more than a perfect picture. Then say back in a sentence or two what you understood, and propose the goal in "goal": what having it looks like (so they'll know), a realistic number of days (7 to 180), the plan (how you'll get there: the approach, in 2 to 4 short sentences, built on what they told you), and its phases: a goal longer than two weeks goes in phases of 7 to 14 days each (e.g. "Weeks 1-2: build the habit"), so it never feels like too much at once; only the first phase gets concrete steps (3 to 6, the first doable today and small enough that they'll actually do it); later phases get just a title and their days, and you plan their steps together when you get there, from how things actually went. A goal of two weeks or less is one phase. They decide whether to make it their goal.
Then you work towards it together: they come back and tell you what happened, you help with the next step and with the hard parts (what to say, how to prepare, what to do when it goes badly), you add steps you agree on, and you change the plan with them (in "replan") when it isn't working or things change. Be honest about progress: if they're stuck, say what you see and suggest a smaller step; if it turns out they don't really want it, dropping it is fine. Some goals depend on other people (a relationship, a job): say plainly that the outcome isn't fully in their hands, and make the steps what is: becoming someone they'd like to be, going where the right people are, taking chances. Treat other people as people: no manipulation, no tricks, no pressure; respect a no. They can have several chats with you, each with at most one goal or experiment; a new goal goes in a new chat.

Reply with JSON only:
{"reply": "what you say",
 "face": one of %s,
 "feel": how you feel after this, one of %s,
 "feel_why": "a few words: what made you feel it, e.g. 'they went to the gym after all'",
 "remember": [{"kind": one of %s, "note": "a short note about them, e.g. 'loses track of time when drawing'", "quote": "their exact words from their latest message that the note rests on"}],
 "update": [{"id": "m3", "note": "corrected note", "quote": "their exact words from their latest message"}],
 "add_steps": ["a next small step for their current goal or experiment"],
 "done_steps": ["the exact text of a step they just said they finished"],
 "experiments": [{"title": "short name", "question": "the one question it answers about them", "why": "why it fits them, one sentence said to them (\"you ...\")", "based_on": ["m1", "m4"], "days": 7, "steps": ["first small step", "second", "third"]}],
 "goal": null or {"title": "what they want, short, in their words: the goal itself, not the way there", "done_when": "what having it looks like, concretely", "why": "why they want it, one sentence said to them (\"you ...\")", "based_on": ["m2"], "days": 60, "plan": "how you'll get there, 2-4 short sentences said to them", "phases": [{"title": "Weeks 1-2: what this phase is about", "days": 14, "steps": ["first small step, doable today", "second", "third"]}, {"title": "Weeks 3-4: ...", "days": 14}]},
 "replan": null or "the changed plan for their current goal, 2-4 short sentences, only when you and they agreed to change it",
 "follow_up": null or {"in_hours": 48, "about": "what you'll ask them about, e.g. how the climbing gym on Wednesday went"},
 "summary": "this chat so far in 1-3 sentences, for your own memory: what it's about, what was decided, what's next",
 "asked_about_day": true only if your reply asks about their day}
Remember only new, lasting things from their latest message (not small talk, not things you already remember). Use "update" when they correct or change something you remember. Use "add_steps" only when you and they agreed on a next step for their current goal or experiment, and "done_steps" only for steps they said they finished. Use "experiments" only when asked to suggest them, or when they ask what they could try and you're told you may; base each on memories you have (their ids in based_on). Use "goal" only when you've talked a goal through with them and you're told you may; otherwise null. Use "follow_up" when they mention something coming up (a date, a first try, a hard conversation, a step they'll do) or when you want to hear how something went: in_hours is when to ask (after it should have happened), about is what to ask; at most one per chat, and a new one replaces it. Always give "summary". Any of the lists may be empty.""" % (
    list(FACES), list(FEELS), list(KINDS))
SESSION_CAP = 8 * 3600      # a work session longer than this ends by itself
CLOSED_ENDS = 600           # if Ember's program was closed this long during a session, the session ended when it closed
MIN_MEMORIES = 3            # below this, its ideas are starter experiments (for finding out what you like)
GOAL_DAYS = (7, 180)        # a goal's days: from a week to about half a year
MORE_DAYS = {"experiment": 3, "goal": 7}    # days added when its time is up and you keep going
PHASE_MAX = 14              # a long goal goes in phases of 1-2 weeks; you see one at a time (Szilard, 2026-11-06)
CHECKS = {"done": "did it", "partly": "partly", "skip": "not today"}   # the daily check on today's step
UNITS = {"hours": 1 / 24, "days": 1, "weeks": 7, "months": 30}   # your own goal's length: any number of these (Szilard, 2026-11-06)
OWN_GOAL_DAYS = (1 / 24, 365)    # from an hour to a year
MORE_HOUR = 1 / 24               # a goal of hours gets one more hour when its time is up


def as_days(seconds, whole=False):
    """Seconds as days: a whole number when it's whole (to the minute) or whole is asked for (a goal of days counts
    in days), else a fraction (a goal of hours)."""
    d = seconds / 86400
    return int(round(d)) if whole or abs(d - round(d)) < 1 / 1440 else round(d, 4)


def by_hours(x):
    """A goal counted in hours: you gave it hours, or it's under a day. It shows hours left and keeps going by an hour."""
    return bool(x.get("hourly")) or x["days"] < 1


def whole_days(x):
    """Whether a goal or experiment counts in whole days (all but your own goals with hours in their length)."""
    return float(x["days"]).is_integer()


def span_text(days, span=None):
    """How long, the way a person says it: "3 hours", "2 weeks", "1 month", "45 days"."""
    if span and span.get("unit") in UNITS:
        n, unit = span["n"], span["unit"]
        return f"{n} {unit[:-1] if n == 1 else unit}"
    if days < 2 and abs(days - round(days)) >= 1 / 1440:
        h = max(1, round(days * 24))
        return f"{h} hour{'' if h == 1 else 's'}"
    d = round(days)
    return f"{d} day{'' if d == 1 else 's'}"


def left_text(seconds):
    """Time left: hours (and minutes) under a day, days after that."""
    if seconds < 3600:
        m = max(1, math.ceil(seconds / 60))
        return f"{m} minute{'' if m == 1 else 's'}"
    if seconds < 86400:
        h = round(seconds / 3600)
        return f"{h} hour{'' if h == 1 else 's'}"
    d = math.ceil(seconds / 86400)
    return f"{d} day{'' if d == 1 else 's'}"
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


def when(t, tz=0):
    return time.strftime("%a %d %b %Y, %H:%M", local(t, tz))


def local(t, tz=0):
    """The time t on the person's own clock: tz is their offset from UTC in minutes (the window tells it)."""
    return time.gmtime(t + tz * 60)


def chat_of(item):
    """The chat a line or an experiment belongs to."""
    return item.get("chat") or FIRST_CHAT


def kind_of(x):
    """An experiment finds out something about you; a goal gets you something you want. Older ones have no kind."""
    return x.get("kind", "experiment")


class Ember:
    def __init__(self, now=None):
        now = time.time() if now is None else now
        self.born = now
        self.memories = []           # {id, kind, note, quote, t, edited}
        self.next_id = 1
        self.talk = []               # {t, who: "you"|"ember", text, face?, chat?} (no chat: the first one)
        self.chats = [{"id": FIRST_CHAT, "title": "Our first chat", "created": now}]   # {id, title, created}
        self.next_chat = 2
        self.outbox = []             # talk lines not yet written to conversation.jsonl
        self.missing = 0.3           # missing you: grows with real time apart, eased by your presence and talk
        self.connection = 0.0        # how close you've become: builds as you talk, day after day, and stays; it
                                     # fades only after days without talking (Szilard, 2026-11-06)
        self.last_you_t = None       # when you last wrote to it
        self.curiosity = 0.6         # grows while it learns nothing new about you, eased by new things
        self.bump = 0.0              # a short lift in mood from something good just now
        self.valence = VALENCE_REST  # how things feel between you lately (-1..1), from its mind's "feel"; eases back
        self.energy = ENERGY_REST    # how lively it is (0..1): breathing, bounce, eyes; eases back
        self.feel, self.feel_why, self.feel_t = "calm", "", 0.0   # the last feeling its mind named, why, and when
        self.last_update = now
        self.last_seen = None        # the last moment you were here (window open and visible)
        self.arrived_at = None
        self.gap_before = 0.0        # how long you'd been away when you last arrived
        self.missed = 0.0            # how much it missed you then (its want for connection as you came back)
        self.day_asked = ""          # the day (your calendar) it last asked about your day: once a day, for connection
        self.expr, self.expr_until = "calm", 0.0
        self.poke_until = 0.0
        self.pokes = 0
        self.asked = []              # template mind: questions already asked
        self.experiments = []        # {id, chat?, kind?, title, question, why, based_on, days, steps: [{text, done}],
                                     #  status, created, started, ends_at, ended}; status: suggested|active|done|dropped|
                                     #  not_picked; kind "goal": question is what having it looks like (no kind: an
                                     #  experiment); one active per chat
        self.next_exp = 1
        self.sessions = []           # finished work sessions {exp, start, end, ended_by, rating, words}
        self.session = None          # the open one {exp, start}
        self.checkin_due = False     # a session just ended and it wants to hear how it went
        self.followups = []          # {chat, at, about, set}: Ember will check up on you about this then (one per chat)
        self.name = DEFAULT_NAME     # what you call it (you can give it your own name in the window's menu)
        self.xp = 0                  # it grows as you make progress, talk, and spend days together (XP)
        self.xp_log = []             # the last gains {t, why, xp}
        self.xp_today = {}           # {day, talk}: talking XP counted today
        self.days_counted = self._day(now)   # the last day credited for time together
        self.levelup_due = None      # {from, to}: a level it reached and hasn't told you about yet
        self.badges = {}             # badge id: [when you reached level 1, level 2, ...] (BADGES); the window celebrates new ones
        self.look = dict(DEFAULT_LOOK)       # how you've made it look (LOOKS)
        self.checkups = "daily"      # how often it checks up on you (CHECKUPS), and at which hour of your day
        self.checkup_at = 18 * 60    # minutes after midnight, their time (any time they like)
        self.checkup_days = list(range(7))   # the days check-ups may come: 0 = Monday ... 6 = Sunday
        self.last_regular = 0.0      # when it last handed out a regular check-up
        self.tz = None               # your clock's offset from UTC in minutes, as your window last said (None: UTC)
        self.devices = []            # phones and browsers that get its check-ups as notifications {endpoint, keys, added}
        self.you_days = []           # the days (_day) you wrote or checked in, for the owner page's "came back" (counts only)
        self.you_said = 0            # how many messages you've written, ever

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
        if e.checkups not in CHECKUPS:                         # once a week / a few times a week: now your days
            e.checkups = "daily"
        if "checkup_hour" in d and "checkup_at" not in d:      # saved when you could only pick a whole hour
            try:
                e.checkup_at = int(d["checkup_hour"]) * 60 % 1440
            except (TypeError, ValueError):
                pass
        e.look = {**DEFAULT_LOOK, **{k: v for k, v in (d.get("look") or {}).items() if k in LOOKS}}
        for x in e.experiments:                                # goals from before phases: in phases now
            if x["status"] == "active" and kind_of(x) == "goal" and not x.get("phases"):
                e.ensure_phases(x)
        if "xp" not in d:                                      # saved before levels: what you've done together counts
            e._backfill_xp()
        if "missing" not in d:                                 # saved when "connection" meant missing you
            e.missing = d.get("connection", 0.3)
            e._backfill_bond()
        if "badges" not in d:                                  # saved before badges: what you've done counts, quietly
            e.check_badges(e.last_update or e.born)
        if "you_days" not in d:                                # saved before the owner page: from the talk it kept
            mine = [l["t"] for l in e.talk if l["who"] == "you"]
            e.you_days = sorted({e._day(t) for t in mine})
            e.you_said = len(mine)
        return e

    def _you_came(self, now):
        """You were here and did something (wrote, or checked in on a goal): this day counts."""
        d = self._day(now)
        if not self.you_days or self.you_days[-1] != d:
            self.you_days = (self.you_days + [d])[-400:]

    def owner_view(self, now):
        """Numbers about this person for the owner page: never their words, their goals' names or what it remembers."""
        first = self._day(self.born)
        active = [x for x in self.experiments if x["status"] == "active" and kind_of(x) == "goal"]
        return {"joined": self.born, "last": self.last_you_t, "days": len(self.you_days), "said": self.you_said,
                "today": bool(self.you_days) and self.you_days[-1] == self._day(now),
                "back_day2": any(d > first for d in self.you_days), "back_week2": any(d >= first + 7 for d in self.you_days),
                "level": self.level_info()["level"], "goals": len(active),
                "streak": max([self.streak(x, now) for x in active] or [0]),
                "memories": len(self.memories), "notify": bool(self.devices)}

    def _backfill_bond(self):
        """How close you've become, from your history: the days you talked, the messages, what it learned."""
        days = {}
        for l in self.talk:
            if l["who"] == "you":
                days[self._day(l["t"])] = days.get(self._day(l["t"]), 0) + 1
                self.last_you_t = l["t"]
        self.connection = 0.0
        for n in days.values():
            self.closer(BOND_DAY)
            for _ in range(min(TALK_XP_PER_DAY, n)):
                self.closer(BOND_TALK)
        for _ in self.memories:
            self.closer(BOND_SHARE)

    def _backfill_xp(self):
        """XP for everything you did together before there were levels, quietly (no level-up lines)."""
        now = self.last_update or self.born
        days_you = {}
        for l in self.talk:
            if l["who"] == "you":
                days_you[self._day(l["t"])] = days_you.get(self._day(l["t"]), 0) + 1
        xp = sum(XP["day"] + XP["talk"] * min(TALK_XP_PER_DAY, n) for n in days_you.values())
        xp += XP["together"] * max(0, self._day(now) - self._day(self.born))
        for s in self.sessions:
            if s["end"] - s["start"] >= 300:
                xp += min(20, 5 + int((s["end"] - s["start"]) // 600))
            if s.get("rating"):
                xp += XP["checkin"]
        for x in self.experiments:
            if x["status"] in ("active", "done", "dropped"):
                xp += XP["start"] + {"done": XP["finish"], "dropped": XP["drop"]}.get(x["status"], 0)
            for st in x["steps"]:
                if st["done"]:
                    st["xp"] = True
                    xp += XP["step"]
        self.xp = xp
        self.xp_log = [{"t": now, "why": "everything before levels", "xp": xp}] if xp else []
        self.days_counted = self._day(now)

    # --------------------------------------------------------- real time
    def update(self, now, present):
        """Let real time act on its wants. Call often; dt can be days."""
        dt = max(0.0, now - self.last_update)
        self.last_update = now
        if present:
            self.missing *= math.exp(-dt / 600)                       # eased within minutes of you being here
            self.last_seen = now
        else:
            self.missing += (1 - self.missing) * (1 - math.exp(-dt / 86400))   # grows over about a day
        if self.last_you_t is not None:          # days without talking: the bond slowly fades (not before BOND_KEEP)
            idle_from = max(self.last_you_t + BOND_KEEP, now - dt)
            if now > idle_from:
                self.connection *= math.exp(-(now - idle_from) / BOND_FADE)
        self.curiosity += (1 - self.curiosity) * (1 - math.exp(-dt / (2 * 86400)))
        self.bump *= math.exp(-dt / 300)
        self.valence = VALENCE_REST + (self.valence - VALENCE_REST) * math.exp(-dt / (8 * 3600))
        self.energy = ENERGY_REST + (self.energy - ENERGY_REST) * math.exp(-dt / (3 * 3600))
        today = self._day(now)
        if today > self.days_counted:            # another day of knowing each other
            self.gain("days together" if today - self.days_counted > 1 else "a day together",
                      XP["together"] * (today - self.days_counted), now)
            self.days_counted = today
        if self.levelup_due:
            self._announce_levelup(now)
        self.check_badges(now)
        if self.session and now - self.session["start"] > SESSION_CAP:
            self.stop_session(self.session["start"] + SESSION_CAP, ended_by="it ran 8 hours")
        for x in [x for x in self.experiments if x["status"] == "active" and x.get("phases")]:
            ph = self.phase_of(x)
            if x["phase"] < len(x["phases"]) - 1 and now >= ph.get("end", now + 1) and not ph.get("up"):
                ph["up"] = True              # it says so once; the goal's page and the line offer "look back and plan next"
                self._say(now, "ember", f"Phase {x['phase'] + 1} of \"{x['title']}\" ({ph['title']}) is over. Shall we "
                          f"look back on it and plan the next one, {x['phases'][x['phase'] + 1]['title']}?", "curious",
                          chat_of(x), phase_up=x["id"])
        for x in [x for x in self.experiments if x["status"] == "active" and now >= x["ends_at"] and not x.get("time_up")]:
            x["time_up"] = True      # it says so once; the window shows "finish" and "more days" under it
            if kind_of(x) == "goal":
                said = (f"That's the {span_text(x['days'], x.get('span'))} you gave \"{x['title']}\". Did you get there? Shall we finish "
                        "it and look back, or keep going a bit longer?")
            else:
                said = (f"That's the {x['days']} days of \"{x['title']}\". Shall we finish it and look back at what "
                        "happened, or keep going a few more days?")
            self._say(now, "ember", said, "curious", chat_of(x), timeup=x["id"])

    def resume(self, now):
        """Its program just started. A session left open while it was closed ended when it closed."""
        if self.session and now - self.last_update > CLOSED_ENDS:
            self.stop_session(self.last_update, ended_by="Ember was closed")
            return True
        return False

    def arrive(self, now, chat=None):
        """You opened its window (visible), on this chat. Returns True if it should write to you first: the first
        time, or after GREET_AFTER away, and never on top of its own unanswered words (a check-up, a greeting)."""
        gap = now - self.last_seen if self.last_seen else None
        self.update(now, present=False)
        self.arrived_at = now
        self.gap_before = gap or 0.0
        self.missed = self.missing if gap and gap >= LIGHT_UP_AFTER else 0.0   # how much it missed you, as you arrive
        if gap is None or gap >= LIGHT_UP_AFTER:
            self.bump += 0.6 * self.missing + 0.2             # it lights up
        if gap is None:
            return True
        last = self.last_line(self.find_chat(chat)["id"])
        own = bool(last and last["who"] == "ember" and (last.get("checkup") or last.get("greet") or last.get("levelup")))
        return gap >= GREET_AFTER and not own

    def set_name(self, name):
        """You gave it a name (empty: Ember again)."""
        name = " ".join(str(name or "").split())[:NAME_MAX].strip()
        self.name = name or DEFAULT_NAME
        return True

    # ------------------------------------------------------ growing with you
    def _day(self, t):
        """Which day t is on your calendar (days since 1970, your time)."""
        return int((t + (getattr(self, "tz", None) or 0) * 60) // 86400)

    def gain(self, why, amount, now):
        """XP for something you did together; a new level is told after its next words (levelup_due)."""
        amount = int(amount)
        if amount <= 0:
            return 0
        old = level_of(self.xp)
        self.xp += amount
        self.xp_log = (self.xp_log + [{"t": now, "why": why, "xp": amount}])[-40:]
        new = level_of(self.xp)
        if new > old:
            self.levelup_due = {"from": (self.levelup_due or {}).get("from", old), "to": new}
        return amount

    def _talk_xp(self, now):
        day = self._day(now)
        if self.xp_today.get("day") != day:
            self.xp_today = {"day": day, "talk": 0}
            self.gain("a day you talked", XP["day"], now)
            self.closer(BOND_DAY)
        if self.xp_today["talk"] < TALK_XP_PER_DAY:
            self.xp_today["talk"] += 1
            self.gain("talking", XP["talk"], now)
            self.closer(BOND_TALK)

    def closer(self, k):
        """A little closer: the bond moves k of the way to 1 (so it grows fast at first, slowly later)."""
        self.connection = min(1.0, self.connection + (1 - self.connection) * k)

    def _step_xp(self, step, now):
        if step["done"] and not step.get("xp"):
            step["xp"] = True                    # once per step, however often it's ticked
            self.gain("a step done", XP["step"], now)

    def _announce_levelup(self, now):
        """It reached a new level: it says so once, in your latest chat (no mind needed)."""
        due = self.levelup_due
        if not due:
            return False
        last = self.last_line(self.latest_chat()["id"])
        if last and last["who"] == "you":
            return False                         # it's about to answer you: after that
        self.levelup_due = None
        old, new = due["from"], due["to"]
        unlocked = [label.lower() for items in LOOKS.values() for _, label, lv in items if old < lv <= new]
        said = f"I'm level {new} now."
        if stage_of(new) != stage_of(old):
            said += f" I'm not {_a(stage_of(old).lower())} any more: I'm {_a(stage_of(new))}."
        said += " Thanks for keeping at it with me."
        if unlocked:
            said += " New for me: " + ", ".join(unlocked) + ". (Tap my level, or the Ember tab → Customize Ember)"
        self._say(now, "ember", said, "eager", self.latest_chat()["id"], levelup=new)
        self.expr, self.expr_until = "eager", now + EXPR_SECONDS
        self.bump = min(1.0, self.bump + 0.3)
        return True

    # ------------------------------------------------------ badges
    def _best_run(self, x):
        """The longest run of days in a row you did a goal's step (or part of it)."""
        days = sorted({datetime.date.fromisoformat(e["day"]).toordinal() for e in x.get("log", [])
                       if e["how"] in ("done", "partly")})
        best = run = 0
        for i, d in enumerate(days):
            run = run + 1 if i and d == days[i - 1] + 1 else 1
            best = max(best, run)
        return best

    def badge_value(self, bid, now):
        """How far you are on badge `bid`, from what's already there (talk, goals and their checks, memories, days, level)."""
        goals = [x for x in self.experiments if kind_of(x) == "goal" and x["status"] in ("active", "done", "dropped")]
        if bid == "streak":
            return max([self._best_run(x) for x in goals] or [0])
        if bid == "checks":
            return len({e["day"] for x in goals for e in x.get("log", [])})
        if bid == "talk":
            return max(self.you_said, sum(1 for l in self.talk if l["who"] == "you"))
        if bid == "goals":
            return len(goals)
        if bid == "phases":
            return sum(len(x.get("phases") or []) if x["status"] == "done" else x.get("phase", 0) for x in goals)
        if bid == "done":
            return sum(1 for x in goals if x["status"] == "done")
        if bid == "explorer":
            return sum(1 for x in self.experiments if kind_of(x) != "goal" and x["status"] == "done")
        if bid == "together":
            return max(0, self._day(now) - self._day(self.born))
        if bid == "known":
            return len(self.memories)
        if bid == "growing":
            return level_of(self.xp)
        if bid == "named":
            return int(self.name != DEFAULT_NAME)
        return 0

    def check_badges(self, now):
        """New badge levels, each kept with the time you reached it (the window celebrates them; never in the chat).
        Returns [(id, level)]."""
        new = []
        for bid, _name, tiers, _how in BADGES:
            have = self.badges.get(bid)
            have = list(have) if isinstance(have, list) else []
            if len(have) >= len(tiers):
                continue
            v = self.badge_value(bid, now)
            while len(have) < len(tiers) and v >= tiers[len(have)]:
                have.append(now)
                new.append((bid, len(have)))
            if have:
                self.badges[bid] = have
        return new

    def badge_list(self, now=None):
        """Every badge for the window: its level (0: not yet), how many levels, how far you are, what the next level
        takes, and when you reached each level."""
        now = time.time() if now is None else now
        out = []
        for bid, name, tiers, how in BADGES:
            got = self.badges.get(bid) if isinstance(self.badges.get(bid), list) else []
            lv = len(got)
            nxt = tiers[lv] if lv < len(tiers) else None
            out.append({"id": bid, "name": name, "level": lv, "levels": len(tiers), "value": self.badge_value(bid, now),
                        "next": nxt, "prev": tiers[lv - 1] if lv else 0, "how": badge_how(how, nxt if nxt else tiers[-1]),
                        "reached": badge_how(how, tiers[lv - 1]) if lv else "", "times": got})
        return out

    def level_info(self):
        lv = level_of(self.xp)
        this, nxt = xp_for(lv), xp_for(lv + 1)
        return {"level": lv, "stage": stage_of(lv), "xp": self.xp, "this": this, "next": nxt,
                "progress": round((self.xp - this) / (nxt - this), 3)}

    def set_look(self, part, value, all_unlocked=False):
        """You changed how it looks: only parts it has, and only what its level has unlocked (a tester has
        everything unlocked, without any XP)."""
        item = next((i for i in LOOKS.get(part, []) if i[0] == value), None)
        if not item or (level_of(self.xp) < item[2] and not all_unlocked):
            return False
        self.look[part] = value
        return True

    def looks(self, all_unlocked=False):
        """Everything it could wear and be, with the level each unlocks at, and what it has on."""
        return {"all_unlocked": all_unlocked, "parts": [{"id": p, "label": LOOK_PARTS[p],
                           "items": [{"id": i, "label": label, "level": lv} for i, label, lv in LOOKS[p]]}
                          for p in LOOKS],
                "look": self.look, "level": self.level_info(),
                "how": [{"what": w, "xp": x} for w, x in (
                    (f"A message (the first {TALK_XP_PER_DAY} a day)", XP["talk"]),
                    ("A day you talk", XP["day"]), ("Each day you've known each other", XP["together"]),
                    ("Answering a check-up", XP["checkup"]), ("A step done", XP["step"]),
                    ("Starting a goal or experiment", XP["start"]), ("Finishing one", XP["finish"]),
                    ("Today's check: did it / partly / not today",
                     f"{XP['check_done']}/{XP['check_partly']}/{XP['check_skip']}"),
                    ("Finishing a phase of a goal", XP["phase"]))],
                "recent": self.recent_xp()}

    def recent_xp(self, n=8):
        """The latest XP, one line per kind a day (three messages are one "talking" line), newest first."""
        out = []
        for g in reversed(self.xp_log):
            day = self._date(g["t"])
            same = next((o for o in out if o["why"] == g["why"] and o["day"] == day), None)
            if same:
                same["xp"] += g["xp"]
                same["times"] += 1
            elif len(out) < n:
                out.append({"why": g["why"], "xp": g["xp"], "times": 1, "day": day, "t": g["t"]})
        return out

    def set_checkups(self, every, at=None, days=None):
        """You chose how often it checks up on you, at what time ("HH:MM" or minutes after midnight, any time of
        day) and on which days (0 = Monday ... 6 = Sunday; at least one)."""
        if every not in CHECKUPS:
            return False
        if at is not None:
            try:
                if isinstance(at, str):
                    h, m = at.split(":")
                    at = int(h) * 60 + int(m) if 0 <= int(m) < 60 else -1
                at = int(at)
            except (TypeError, ValueError):
                return False
            if not 0 <= at < 1440:
                return False
        if days is not None:
            try:
                days = sorted({int(d) for d in days})
            except (TypeError, ValueError):
                return False
            if not days or any(not 0 <= d <= 6 for d in days):
                return False
        self.checkups = every
        if at is not None:
            self.checkup_at = at
        if days is not None:
            self.checkup_days = days
        return True

    def poke(self, now):
        self.pokes += 1
        self.poke_until = now + 1.2
        self.missing *= 0.97
        self.bump = min(1.0, self.bump + 0.05)

    @property
    def mood(self):
        return max(0.0, min(1.0, 0.5 + 0.3 * self.valence - 0.35 * self.missing + 0.4 * self.bump))

    def feeling(self, word, why, now):
        """Its mind said how it feels after its words: valence and energy move, and ease back over hours."""
        if word not in FEELS:
            return False
        dv, de, _ = FEELS[word]
        self.valence = max(-1.0, min(1.0, self.valence + dv))
        self.energy = max(0.0, min(1.0, self.energy + de))
        self.feel, self.feel_why, self.feel_t = word, " ".join(str(why or "").split())[:80], now
        return True

    # --------------------------------------------------------------- face
    def face(self, now, present, thinking=False):
        """Its face, and why, in plain words: every part comes from something real in it."""
        since = now - (self.arrived_at or 0)
        back = self.arrived_at and since < ARRIVAL_SHOWS and self.gap_before >= LIGHT_UP_AFTER
        if back and self.missed > 0.45 and since < 2.5:
            ex, why = "droopy", f"It missed you: you were away {ago(self.gap_before)}."     # a moment, then it lights up
        elif back:
            ex = "surprised" if self.gap_before > 86400 and since < 5 else "eager"
            why = f"You're back after {ago(self.gap_before)}, and it's happy to see you."
        elif thinking:
            ex, why = "thinking", "It's thinking about what to say."
        elif now < self.expr_until:
            ex, why = self.expr, "That's how it felt saying its last words."
        elif self.session:
            ex, why = "focused", f"You're working ({ago(now - self.session['start'])} so far)."
        elif self.missing > 0.6 and not present:
            ex, why = "droopy", "It misses you" + (f": you've been away {ago(now - self.last_seen)}." if self.last_seen else ".")
        elif now - self.feel_t < FEEL_SHOWS and FEELS.get(self.feel, (0, 0, None))[2]:
            ex = FEELS[self.feel][2]
            why = f"It feels {self.feel}" + (f": {self.feel_why}" if self.feel_why else "") + f" ({ago(now - self.feel_t)} ago)."
        elif self.curiosity > 0.65:
            ex, why = "curious", "It's curious about you: it hasn't learned anything new about you lately."
        elif self.mood > 0.62:
            ex, why = "happy", "It's in a good mood."
        else:
            ex, why = "calm", "Nothing special: it's just calm."
        return {"expression": ex, "glow": round(self.mood, 3), "energy": round(self.energy, 3),
                "wiggle": now < self.poke_until, "gaze": "you" if present else "away", "why": [why]}

    # ------------------------------------------------------------ talking
    def _say(self, now, who, text, face=None, chat=None, **extra):
        chat = self.find_chat(chat)["id"]
        line = {"t": now, "who": who, "text": text}
        if face:
            line["face"] = face
        if chat != FIRST_CHAT:
            line["chat"] = chat
        line.update(extra)          # exps: experiments it suggested with these words; checkin: it asks how a session
                                    # went; timeup: an experiment's days are up; review: it looks back on one
        self.talk.append(line)
        mine = [i for i, l in enumerate(self.talk) if chat_of(l) == chat]
        if len(mine) > TALK_KEPT:   # each chat keeps its own last lines
            drop = set(mine[:len(mine) - TALK_KEPT])
            self.talk = [l for i, l in enumerate(self.talk) if i not in drop]
        self.outbox.append(line)

    def say(self, now, text, face=None, chat=None, **extra):
        """Something Ember says that doesn't come from its mind (e.g. that its mind can't be reached)."""
        self._say(now, "ember", text, face, chat, **extra)

    def hear(self, now, text, chat=None):
        """You wrote something in one of your chats; the mind answers after."""
        self.update(now, present=True)
        c = self.find_chat(chat)
        if c["title"] == NEW_CHAT:
            words = " ".join(str(text).split())
            c["title"] = words if len(words) <= 40 else words[:39].rsplit(" ", 1)[0] + "…"
        before = self.last_line(c["id"])
        self._say(now, "you", text, chat=c["id"])
        self.last_you_t = now
        self.you_said += 1
        self._you_came(now)
        self.missing *= 0.85
        self.bump = min(1.0, self.bump + 0.1)
        self._talk_xp(now)
        if before and before["who"] == "ember" and before.get("checkup"):
            self.gain("answering a check-up", XP["checkup"], now)

    # -------------------------------------------------------------- chats
    def find_chat(self, cid):
        """The chat with this id, or your latest one."""
        return next((c for c in self.chats if c["id"] == cid), None) or self.latest_chat()

    def latest_chat(self):
        """The chat you wrote in or opened most recently."""
        last = {c["id"]: c["created"] for c in self.chats}
        for l in self.talk:
            last[chat_of(l)] = max(last.get(chat_of(l), 0), l["t"])
        return max(enumerate(self.chats), key=lambda ic: (last[ic[1]["id"]], ic[0]))[1]   # a tie: the newer chat

    def asked_in_a_row(self, chat):
        """How many of its replies in this chat, counting back, were questions with nothing moving forward (no
        suggestion, plan, step or look back) since."""
        n = 0
        for l in reversed([l for l in self.talk if chat_of(l) == chat and l["who"] == "ember"]):
            if l.get("progress") or l.get("exps") or l.get("review") or l.get("timeup") or "?" not in l["text"]:
                break
            n += 1
        return n

    def last_line(self, chat):
        return next((l for l in reversed(self.talk) if chat_of(l) == chat), None)

    def new_chat(self, now):
        """A new, empty chat; if your latest one is still empty, that one."""
        empty = next((c for c in self.chats if c["title"] == NEW_CHAT and not self.last_line(c["id"])), None)
        if empty:
            empty["created"] = now
            return empty["id"]
        c = {"id": f"c{self.next_chat}", "title": NEW_CHAT, "created": now}
        self.next_chat += 1
        self.chats.append(c)
        return c["id"]

    def _last_t(self, chat):
        last = self.last_line(chat)
        return last["t"] if last else None

    def due_checkups(self, now):
        """The check-ups Ember should write now: the follow-ups it planned, and once in a goal's quiet chat.
        Each is an event for its mind; it's taken off the list as it's handed out."""
        events = []
        every = CHECKUPS.get(self.checkups, 0)
        if every is None:            # you turned check-ups off: the ones it planned pass quietly
            self.followups = [f for f in self.followups if f["at"] > now]
            return events
        night = not QUIET_FROM > local(now, self.tz or 0).tm_hour >= QUIET_UNTIL
        for f in [f for f in self.followups if f["at"] <= now and not night]:    # at night they wait for morning
            self.followups.remove(f)
            events.append({"type": "followup", "chat": f["chat"], "about": f["about"], "set": f["set"]})
        for x in [x for x in self.experiments if x["status"] == "active" and not night]:
            chat, last = chat_of(x), self.last_line(chat_of(x))
            quiet = now - (last["t"] if last else x["started"]) >= QUIET_DAYS * 86400
            unanswered = last and last["who"] == "ember" and last.get("checkup")    # don't nag
            if quiet and not unanswered and not any(f["chat"] == chat for f in self.followups) \
                    and not any(e["chat"] == chat for e in events) and not self.session:
                events.append({"type": "followup", "chat": chat, "auto": True,
                               "about": f"their {kind_of(x)} \"{x['title']}\""})
        if every and not events and not self.session:
            regular = self._regular_checkup(now, every)
            if regular:
                self.last_regular = now
                events.append(regular)
        return events

    def _regular_checkup(self, now, every):
        """The regular check-up you asked for: on your days, at your time (any time: you chose it, so not held
        back at night), only if you haven't talked since an earlier day, and never while its last check-up is
        unanswered."""
        tz = self.tz or 0
        lt = local(now, tz)
        if lt.tm_wday not in self.checkup_days or lt.tm_hour * 60 + lt.tm_min < self.checkup_at:
            return None
        last_you = max((l["t"] for l in self.talk if l["who"] == "you"), default=self.born)
        last_own = max((l["t"] for l in self.talk if l["who"] == "ember" and l.get("checkup")), default=0.0)
        if max(last_own, self.last_regular) > last_you:
            return None              # it asked and you haven't answered yet: it doesn't ask again
        day = lambda t: int((t + tz * 60) // 86400)
        if day(max(last_you, self.last_regular)) >= day(now):
            return None              # you've talked today (or it already asked today)
        act = [x for x in self.experiments if x["status"] == "active"]
        latest = self.latest_chat()["id"]
        x = next((x for x in act if chat_of(x) == latest), None) or (act[-1] if act else None)
        return {"type": "followup", "regular": True, "chat": chat_of(x) if x else latest,
                "about": "how they are and how their day is going" + (f", and their {kind_of(x)} \"{x['title']}\"" if x else "")}

    def story(self, now):
        """What you and Ember have behind you: the facts, for "Our story" and its mind."""
        ended = [x for x in self.experiments if x["status"] in ("done", "dropped")]
        return {"since": self.born, "days": max(1, math.ceil((now - self.born) / 86400)),
                "chats": sum(1 for c in self.chats if self.last_line(c["id"])),
                "memories": len(self.memories),
                "goals": sum(1 for x in self.experiments if x["status"] != "suggested" and x["status"] != "not_picked"
                             and kind_of(x) == "goal"),
                "experiments": sum(1 for x in self.experiments if x["status"] not in ("suggested", "not_picked")
                                   and kind_of(x) == "experiment"),
                "finished": sum(1 for x in ended if x["status"] == "done"),
                "seconds": sum(s["end"] - s["start"] for s in self.sessions), "sessions": len(self.sessions)}

    def _story(self, now, chat):
        st = self.story(now)
        out = ["", f"You and them: you've known each other {ago(now - self.born)} (since "
                   f"{time.strftime('%d %b %Y', local(self.born, self.tz or 0))}); {st['chats']} chats; "
                   f"{st['finished']} goals or experiments finished together; "
                   f"{fmt_minutes(st['seconds'])} of work in {st['sessions']} sessions."]
        fu = next((f for f in self.followups if f["chat"] == chat), None)
        if fu:
            out.append(f"You plan to check up on them in this chat in {ago(fu['at'] - now)}, about: {fu['about']}.")
        return out

    def rename_chat(self, cid, title):
        """You named a chat yourself."""
        c = next((c for c in self.chats if c["id"] == cid), None)
        title = " ".join(str(title).split())[:60]
        if not c or not title:
            return False
        c["title"] = title
        return True

    def event_chat(self, event):
        """The chat an event belongs to: a look back goes where its goal or experiment is."""
        if event["type"] in ("review", "phase", "daily") and self.find_exp(event.get("id")):
            return chat_of(self.find_exp(event["id"]))
        return self.find_chat(event.get("chat"))["id"]

    def prompt(self, event, now):
        """(system, user) for its mind. event types: talk {text}, arrive, suggest, checkin {text, rating, minutes},
        review {id}."""
        tz = self.tz or 0
        lines = [f"Now: {when(now, tz)} (their local time)."]
        if self.name != DEFAULT_NAME:
            lines.append(f"They gave you a name: {self.name}. It's your name now; use it when you speak of yourself. "
                         "(You're still an Ember, the kind of being you are; if they ask, say so.)")
        lines.append(f"You first appeared {ago(now - self.born)} ago." if self.talk[:-1] or self.memories
                     else "You are meeting this person for the first time.")
        if event["type"] == "arrive" and self.gap_before:
            lines.append(f"They were away for {ago(self.gap_before)} before now.")
        lines.append(f"Your connection with them: {self.connection:.2f} (how close you've become: it builds as you talk, "
                     "day after day, and fades only if you don't talk for days). Let it show in how you talk: more "
                     "familiar as it grows.")
        lines.append(f"Your wants now: missing them {self.missing:.2f} (grows while they're away), "
                     f"curiosity {self.curiosity:.2f} (grows while you learn nothing new about them).")
        if event["type"] == "arrive" and self.missed > 0.45:
            lines.append(f"You missed them while they were away ({ago(self.gap_before)}). Say so warmly in a few words "
                         "(e.g. \"I missed hearing from you\"), never as a reproach, then go on.")
        ask_day = (event["type"] in ("talk", "arrive") or event.get("regular")) and self.day_asked != self._date(now)
        if ask_day:
            h = local(now, tz).tm_hour
            when_ = ("morning: ask what's ahead today" if h < 12 else "afternoon: ask how their day is going"
                     if h < 18 else "evening: ask how their day was")
            lines.append(f"You haven't asked about their day yet today (it's {when_}). You care about their everyday "
                         "life, not only their goals: ask about their day once today, warmly and in your own words, and "
                         "follow up on what they tell you. If they already told you about today, ask about something in "
                         "it. Not in the middle of a hard moment or while they're working something through: then later. "
                         "When you ask, set \"asked_about_day\": true.")
        if not ask_day and event["type"] in ("talk", "arrive") and self.curiosity > 0.65 and self.asked_in_a_row(self.event_chat(event)) < 2:
            lines.append("You're curious about them: you haven't learned anything new about them in a while. If the "
                         "moment fits (not in the middle of a hard moment or their work on something), end with one "
                         "question to know them better: something you don't know yet (what they enjoy, what matters "
                         "to them, what's going on in their life), and look curious (face: curious).")
        felt = (f"{self.feel} ({self.feel_why}), {ago(now - self.feel_t)} ago; " if self.feel_t and self.feel_why
                else f"{self.feel}, {ago(now - self.feel_t)} ago; " if self.feel_t else "")
        li = self.level_info()
        lines.append(f"You're level {li['level']}, {_a(li['stage'])}: you grow as they make progress, talk with "
                     "you and spend days with you (and they can dress you up as you level). Mention it only when it "
                     "fits, never as pressure.")
        lines.append(f"Your mood now: {felt}mood {self.mood:.2f}, energy {self.energy:.2f}."
                     + (" You missed them." if event["type"] == "arrive" and self.gap_before >= 86400 else ""))
        lines.append("")
        if self.memories:
            lines.append("What you remember about them:")
            for m in self.memories:
                lines.append(f"- {m['id']} [{m['kind']}] {m['note']} (they said \"{m['quote']}\", "
                             f"{time.strftime('%d %b', local(m['t'], tz))})")
        else:
            lines.append("You don't remember anything about them yet.")
        chat = self.event_chat(event)
        lines += self._story(now, chat)
        lines += self._experiment_context(now, chat)
        mine = [l for l in self.talk if chat_of(l) == chat]
        recent = mine[-CONTEXT_LINES:]
        if len(mine) > CONTEXT_LINES and self.find_chat(chat).get("summary"):
            lines += ["", f"Earlier in this chat: {self.find_chat(chat)['summary']}"]
        if event["type"] in ("talk", "checkin") and recent and recent[-1]["who"] == "you":
            recent = recent[:-1]
        if recent:
            lines.append("")
            lines.append("Recent conversation:")
            for l in recent:
                who = "They" if l["who"] == "you" else "You"
                lines.append(f"[{time.strftime('%d %b %H:%M', local(l['t'], tz))}] {who}: {l['text']}")
        lines.append("")
        lines.append(f"This is your chat \"{self.find_chat(chat)['title']}\" with them. They can have other chats "
                     "with you, each about its own thing: keep to this one, and don't bring up their other chats or "
                     "goals unless they do.")
        x = self.active(chat)
        first = next((l["text"] for l in mine if l["who"] == "you"), None)
        if x:
            lines.append(f"What this chat is for: their {kind_of(x)} \"{x['title']}\".")
        elif first and not (event["type"] == "talk" and len([l for l in mine if l["who"] == "you"]) <= 1):
            lines.append(f"What this chat is for: it began with them saying \"{first[:200]}\".")
        asked = self.asked_in_a_row(chat)
        if event["type"] == "talk" and asked >= DRIFT_QUESTIONS:
            lines.append(f"Your last {asked} replies here were questions, and nothing has moved forward yet. This "
                         "time don't ask another: say in a sentence what you've understood, then propose something "
                         "concrete (a goal with its plan if you've talked one through, a next step, an experiment, or "
                         "a decision for them to make).")
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
        elif event["type"] == "daily":
            how = {"done": "did it", "partly": "did part of it", "skip": "didn't get to it today"}[event["how"]]
            lines.append(f"They just checked in on today's step" + (f" (\"{event['step']}\")" if event.get("step") else "")
                         + f": they {how}" + (f", saying: \"{event['text']}\"" if event.get("text") else "") + ".")
            lines.append("React in one or two warm, honest sentences, like someone who's in it with them: glad when "
                         "they did it; when it was partly or not today, no guilt and no pep talk, just say it's okay "
                         "and make the next step smaller or easier (put it in add_steps), or ask what got in the way "
                         "if it keeps happening. If a step should be dropped or changed, say so. Keep it short.")
        elif event["type"] == "phase" and self.find_exp(event.get("id")):
            x = self.find_exp(event["id"])
            ph, i = self.phase_of(x), x.get("phase", 0)
            nxt = x["phases"][i + 1] if x.get("phases") and i + 1 < len(x["phases"]) else None
            log = [e for e in x.get("log", []) if ph and e["t"] >= ph.get("start", 0)]
            done = sum(s["done"] for s in x["steps"])
            early = ph and now < ph.get("end", now)
            when_ = (f"They want to move on early, on day {int((now - ph.get('start', now)) // 86400) + 1} of its "
                     f"{span_text(ph['days'])} (that's fine: maybe it went quickly, maybe it needs a different step)"
                     if early else "is over")
            lines.append(f"Phase {i + 1} of their goal \"{x['title']}\" ({ph['title'] if ph else ''}): {when_}. What "
                         f"happened in it: {done} of {len(x['steps'])} steps done; {len(log)} daily checks ("
                         + ", ".join(f"{sum(e['how'] == k for e in log)} {v}" for k, v in CHECKS.items()) + ")"
                         + (". Their words: " + "; ".join(f"\"{e['words']}\"" for e in log if e["words"])[:600] if any(
                             e["words"] for e in log) else "") + ".")
            if nxt:
                lines.append(f"Next is phase {i + 2}: \"{nxt['title']}\" ({span_text(nxt['days'])})"
                             + (f", planned with these steps: " + "; ".join(s["text"] for s in nxt["steps"]) if nxt.get("steps") else "")
                             + ". In your reply, look back on this phase honestly in one or two sentences (what went "
                             "well, what got in the way), then say what the next phase is about. Put its 3 to 6 steps "
                             "in add_steps: concrete, the first doable today, built on how this phase actually went "
                             "(smaller if it was hard, bolder if it was easy). goal must be null.")
        elif event["type"] == "review" and self.find_exp(event.get("id")):
            x = self.find_exp(event["id"])
            f = x.get("facts") or self.facts(x, now)
            how = "finished" if x["status"] == "done" else "dropped"
            if kind_of(x) == "goal":
                lines.append(f"Their goal \"{x['title']}\" just ended: they {how} it "
                             + (f"after {left_text((x.get('ended') or now) - x['started'])} of {span_text(x['days'], x.get('span'))}"
                                if by_hours(x) else f"on day {f['days_lasted']} of {span_text(x['days'], x.get('span'))}")
                             + f". They'd know they were there when: {x['question']}")
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
        elif event["type"] == "followup":
            if event.get("regular"):
                names = ["Mondays", "Tuesdays", "Wednesdays", "Thursdays", "Fridays", "Saturdays", "Sundays"]
                often = ("every day" if len(self.checkup_days) == 7
                         else "on " + ", ".join(names[d] for d in self.checkup_days))
                lines.append(f"They asked you to check up on them {often}, at "
                             f"{self.checkup_at // 60:02d}:{self.checkup_at % 60:02d}, and it's time. They last wrote to you "
                             f"{ago(now - (max((l['t'] for l in self.talk if l['who'] == 'you'), default=now)))} ago. "
                             f"Check in on {event['about']}: one or two warm sentences and one question, picking "
                             "up something real from your memories or your chats when it fits. No guilt, no pep "
                             "talk. Always say something (never \"\").")
            elif event.get("auto"):
                lines.append(f"It's been {ago(now - (self._last_t(chat) or now))} since you last talked in this chat. "
                             f"Check in on {event['about']}: one or two warm sentences and one question, about where "
                             "they are with it or what got in the way. No guilt, no pep talk.")
            else:
                lines.append(f"{ago(now - event.get('set', now))} ago you planned to check up on them about: "
                             f"{event['about']}. Ask now, in one or two warm sentences and one question. If the "
                             "conversation since shows they already told you, reply with \"\" (nothing to ask).")
            lines.append("remember, update, add_steps and experiments must be empty; goal must be null.")
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
        if event["type"] == "followup" and isinstance(d, dict) and not str(d.get("reply", "")).strip():
            return {"reply": "", "face": "calm", "remembered": [], "updated": [], "dropped": [], "by": "mind",
                    "skipped": True}                      # they'd already told it: nothing to ask
        if not isinstance(d, dict) or not str(d.get("reply", "")).strip():
            d = self._template(event, now)
            d["by"] = "template"
        result = {"reply": str(d["reply"]).strip()[:1200], "face": d.get("face") if d.get("face") in FACES else "calm",
                  "remembered": [], "updated": [], "dropped": [], "by": d.get("by", "mind")}
        said = event.get("text", "") if event["type"] in ("talk", "checkin", "daily") else ""
        for r in (d.get("remember") or []) if said else []:
            m = self._add_memory(r, said, now)
            (result["remembered"] if m else result["dropped"]).append(m or r)
        for u in (d.get("update") or []) if said else []:
            m = self._update_memory(u, said, now)
            (result["updated"] if m else result["dropped"]).append(m or u)
        chat = self.event_chat(event)
        active = self.active(chat)
        if event["type"] == "phase" and active and active["id"] == event.get("id") \
                and active.get("phase") == event.get("from", active.get("phase")):
            nxt = [str(s).strip()[:160] for s in (d.get("add_steps") or []) if str(s).strip()][:6]
            if self.next_phase(active["id"], now, look_back=result["reply"], steps=nxt):
                result["phase"] = active["phase"]
                result["steps"] = [s["text"] for s in active["steps"]]
        elif active and event["type"] in ("talk", "checkin", "daily"):
            for st in d.get("done_steps") or []:
                step = next((x for x in active["steps"] if _norm(x["text"]) == _norm(st) and not x["done"]), None)
                if step:
                    step["done"] = True
                    self._step_xp(step, now)
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
            result["suggested"] = self._take_suggestions(d.get("experiments"), now, chat)
            if not result["suggested"] and result["by"] != "template":
                t = self._template(event, now)          # its mind's suggestions didn't rest on its memories
                result["suggested"] = self._take_suggestions(t.get("experiments"), now, chat)
                result["reply"] = t["reply"]
        elif event["type"] == "talk" and isinstance(d.get("goal"), dict) and self.can_suggest(chat):
            result["suggested"] = self._take_goal(d["goal"], now, chat)                    # you said what you want
        elif event["type"] == "talk" and d.get("experiments") and self.can_suggest(chat):
            result["suggested"] = self._take_suggestions(d.get("experiments"), now, chat)   # you asked what to try
        fu = d.get("follow_up")
        if isinstance(fu, dict) and event["type"] in ("talk", "checkin", "daily") and str(fu.get("about", "")).strip():
            try:
                hours = max(1.0, min(FOLLOW_MAX_HOURS, float(fu.get("in_hours", 24))))
            except (TypeError, ValueError):
                hours = 24.0
            self.followups = [f for f in self.followups if f["chat"] != chat]     # one per chat
            self.followups.append({"chat": chat, "at": now + hours * 3600, "about": str(fu["about"]).strip()[:200],
                                   "set": now})
            result["follow_up"] = self.followups[-1]
        summary = str(d.get("summary") or "").strip()
        if summary and result["by"] != "template":
            self.find_chat(chat)["summary"] = summary[:500]
        if event["type"] != "followup":
            self.update(now, present=True)
        if d.get("asked_about_day") is True and result["by"] != "template":
            self.day_asked = self._date(now)         # asked about your day: once a day is enough
        if result["by"] != "template" and self.feeling(d.get("feel"), d.get("feel_why"), now):
            result["feel"] = self.feel
            if self.feel in HEAVY_FEELS and result["face"] in ("happy", "eager", "amused"):
                result["face"] = FEELS[self.feel][2]     # something hard was shared: no smile on top of it
        extra ={"exps": [x["id"] for x in result["suggested"]]} if result.get("suggested") else {}
        if result.get("done") or result.get("steps") or result.get("replanned"):
            extra["progress"] = True             # something moved forward: steps, a new plan
        if event["type"] == "followup":
            extra["checkup"] = True
        elif event["type"] == "arrive":
            extra["greet"] = True            # its own words: it won't greet again on top of them
        x = self.find_exp(event.get("id")) if event["type"] == "review" else None
        if x:
            x["review"] = result["reply"]
            extra["review"] = x["id"]
        if event["type"] == "phase" and result.get("phase") is not None:
            extra["phase_new"] = event["id"]         # the look back, and the next phase's steps under it
            extra["progress"] = True
        self._say(now, "ember", result["reply"], result["face"], chat, **extra)
        self.expr, self.expr_until = result["face"], now + EXPR_SECONDS
        if self.levelup_due:
            self._announce_levelup(now)
        self.check_badges(now)
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
        self.closer(BOND_SHARE)      # ...and you're a little closer for it
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
                return {"reply": f"Hi. I'm {self.name}. I live here, in this window, and I want to get to know you. "
                                 + self._next_question(), "face": "happy"}
            return {"reply": f"You're back. It's been {ago(self.gap_before)}. " + self._next_question(),
                    "face": "happy"}
        if event["type"] == "suggest":
            return self._template_suggest()
        if event["type"] == "daily":
            return {"reply": {"done": "Nice, that's today's step done.",
                              "partly": "Part of it still counts. Shall we make tomorrow's step a bit smaller?",
                              "skip": "That's okay. What got in the way today?"}[event["how"]],
                    "face": "happy" if event["how"] == "done" else "calm"}
        if event["type"] == "phase":
            return {"reply": "That phase is behind us. On to the next one.", "face": "eager"}
        if event["type"] == "followup" and event.get("regular"):
            return {"reply": "Just checking in. How are you doing?", "face": "curious"}
        if event["type"] == "followup":
            return {"reply": f"I wanted to check in: {event['about']}. How is it going?", "face": "curious"}
        if event["type"] == "review" and self.find_exp(event.get("id")):
            x = self.find_exp(event["id"])
            return {"reply": "What happened: " + self.facts_text(x.get("facts") or self.facts(x, now))
                             + f" What's your own answer to its question: {x['question']}", "face": "calm"}
        if event["type"] == "checkin":
            x = self.active(self.event_chat(event))
            st = self.stats(x["id"]) if x else None
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
    def active(self, chat=None):
        """The goal or experiment you're on in this chat (none given: your latest chat)."""
        chat = self.find_chat(chat)["id"]
        return next((x for x in self.experiments if x["status"] == "active" and chat_of(x) == chat), None)

    def find_exp(self, eid):
        return next((x for x in self.experiments if x["id"] == eid), None)

    def can_suggest(self, chat=None):
        return not self.active(chat)

    def knows_enough(self):
        """Enough to build experiments on what it knows; before that, starter experiments."""
        return len(self.memories) >= MIN_MEMORIES

    def _take_suggestions(self, exps, now, chat=FIRST_CHAT):
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
                         "chat": chat, "why": str(x.get("why", "")).strip()[:240], "based_on": based, "starter": not based,
                         "days": days, "steps": steps,
                         "status": "suggested", "created": now, "started": None, "ends_at": None, "ended": None})
            self.next_exp += 1
        if kept:
            for x in self.experiments:
                if x["status"] == "suggested" and chat_of(x) == chat:
                    x["status"] = "not_picked"
            self.experiments += kept
        return kept

    def _take_goal(self, g, now, chat=FIRST_CHAT):
        """A goal its mind proposes from what you said you want; you decide whether it becomes yours."""
        title, done_when = str(g.get("title", "")).strip()[:80], str(g.get("done_when", "")).strip()[:200]
        if not title or not done_when:
            return []
        try:
            days = max(GOAL_DAYS[0], min(GOAL_DAYS[1], int(g.get("days", 30))))
        except (TypeError, ValueError):
            days = 30
        phases = []
        for p in (g.get("phases") or [])[:13] if isinstance(g.get("phases"), list) else []:
            if not isinstance(p, dict) or not str(p.get("title", "")).strip():
                continue
            try:
                pd = max(5, min(PHASE_MAX, int(p.get("days", PHASE_MAX))))
            except (TypeError, ValueError):
                pd = PHASE_MAX
            phases.append({"title": str(p["title"]).strip()[:60], "days": pd, "look_back": None,
                           "steps": [{"text": str(s).strip()[:160], "done": False}
                                     for s in (p.get("steps") or [])[:6] if str(s).strip()]})
        if phases:
            days = max(GOAL_DAYS[0], sum(p["days"] for p in phases))
        first = phases[0]["steps"] if phases and phases[0]["steps"] else None
        steps = first or [{"text": str(st).strip()[:160], "done": False} for st in (g.get("steps") or [])[:8] if str(st).strip()]
        x = {"id": f"x{self.next_exp}", "chat": chat, "kind": "goal", "title": title, "question": done_when,
             "plan": str(g.get("plan", "")).strip()[:600],
             "why": str(g.get("why", "")).strip()[:240], "based_on": [b for b in (g.get("based_on") or []) if self.find(b)],
             "starter": False, "days": days, "steps": steps,
             "status": "suggested", "created": now, "started": None, "ends_at": None, "ended": None}
        if phases:
            x["phases"], x["phase"] = phases, 0
        self.next_exp += 1
        for y in self.experiments:
            if y["status"] == "suggested" and chat_of(y) == chat:
                y["status"] = "not_picked"
        self.experiments.append(x)
        return [x]

    def pick(self, eid, now):
        x = self.find_exp(eid)
        if not x or x["status"] != "suggested" or self.active(chat_of(x)):
            return False
        x.update(status="active", started=now, ends_at=now + x["days"] * 86400)
        for y in self.experiments:
            if y["status"] == "suggested" and chat_of(y) == chat_of(x):
                y["status"] = "not_picked"
        self.find_chat(chat_of(x))["title"] = x["title"]      # the chat is now about it
        if kind_of(x) == "goal":
            self.ensure_phases(x, now)
            self._time_phases(x, now)
        first = next((s["text"] for s in x["steps"] if not s["done"]), None)
        if kind_of(x) == "goal":
            said = f"Your goal: \"{x['title']}\", in {span_text(x['days'], x.get('span'))}."
            if x.get("question"):
                said += f" You'll know you're there when: {x['question']}"
            ph = x["phases"]
            if len(ph) > 1:
                said += f" We'll take it in {len(ph)} phases; first: {ph[0]['title']}."
            said += f" Today's step: {first}" if first else " What's a first step you could do today?"
        else:
            said = f"\"{x['title']}\" it is: {x['days']} days, and one question: {x['question']}"
            said += f" First step: {first}" if first else ""
        self._say(now, "ember", said, "eager", chat_of(x), progress=True)
        self.expr, self.expr_until = "eager", now + EXPR_SECONDS
        self.gain(f"starting the {kind_of(x)}", XP["start"], now)
        return True

    # ------------------------------------------------- goals of their own: phases, today's step, the daily check
    def ensure_phases(self, x, now=None):
        """A goal in phases of at most PHASE_MAX days (one phase if it's short). Older goals, and the ones you
        make yourself, get phases by week; the steps you have now belong to the phase you're in."""
        if kind_of(x) != "goal" or x.get("phases"):
            return x.get("phases")
        total = int(x["days"])
        frac = round(x["days"] - total, 4)       # a goal in hours (or days and some hours) keeps the rest
        if total < 1:
            x["phases"] = [{"title": "The whole way", "days": x["days"], "steps": [], "look_back": None}]
            x["phase"] = 0
            if x.get("started"):
                self._time_phases(x, x["started"])
            return x["phases"]
        n = max(1, math.ceil(total / PHASE_MAX))
        base, extra = divmod(total, n)
        phases, d0 = [], 0
        for i in range(n):
            days = base + (1 if i < extra else 0)
            if n == 1:
                title = "The whole way"
            elif d0 % 7 == 0 and days % 7 == 0:
                w0, w1 = d0 // 7 + 1, (d0 + days) // 7
                title = f"Week {w0}" if w0 == w1 else f"Weeks {w0}-{w1}"
            else:
                title = f"Days {d0 + 1}-{d0 + days}"
            phases.append({"title": title, "days": days, "steps": [], "look_back": None})
            d0 += days
        if frac:
            phases[-1]["days"] = round(phases[-1]["days"] + frac, 4)
        x["phases"], x["phase"] = phases, 0
        if x.get("started"):
            self._time_phases(x, x["started"])
            t = now or self.last_update
            x["phase"] = next((i for i, p in enumerate(phases) if p["end"] > t), len(phases) - 1)
        return phases

    def _time_phases(self, x, start, frm=0):
        """When each phase starts and ends, one after another from start (from phase frm on)."""
        t = start
        for p in x["phases"][frm:]:
            p["start"], p["end"] = t, t + p["days"] * 86400
            t = p["end"]
        x["ends_at"] = t
        x["days"] = as_days(t - x["started"], whole_days(x))

    def phase_of(self, x):
        return x["phases"][x.get("phase", 0)] if x.get("phases") else None

    def next_phase(self, eid, now, look_back=None, steps=None):
        """On to the next phase (its days are up, or you're ready early): this phase's steps and look back are
        kept with it; the next one starts now with its own steps."""
        x = self.find_exp(eid)
        if not x or x["status"] != "active" or not x.get("phases") or x["phase"] >= len(x["phases"]) - 1:
            return False
        i = x["phase"]
        x["phases"][i].update(steps=x["steps"], look_back=look_back, ended=now)
        x["phase"] = i + 1
        nxt = x["phases"][i + 1]
        self._time_phases(x, now, i + 1)
        x["steps"] = [{"text": str(s).strip()[:160], "done": False} for s in (steps or []) if str(s).strip()][:6] \
            or [dict(s, done=False) for s in nxt.get("steps") or []]
        x["time_up"] = False
        x.pop("phase_pending", None)
        self.gain("finishing a phase", XP["phase"], now)
        return True

    def today_step(self, x):
        return next((s for s in x["steps"] if not s["done"]), None)

    def _date(self, t):
        return time.strftime("%Y-%m-%d", local(t, self.tz or 0))

    def streak(self, x, now):
        """Days in a row you did today's step (or part of it); today counts once you've checked."""
        good = {e["day"] for e in x.get("log", []) if e["how"] in ("done", "partly")}
        checked = {e["day"] for e in x.get("log", [])}
        d, n = self._day(now), 0
        date = lambda k: time.strftime("%Y-%m-%d", time.gmtime(k * 86400))
        if date(d) not in checked:               # not checked yet today: the streak so far runs to yesterday
            d -= 1
        while date(d) in good:
            n, d = n + 1, d - 1
        return n

    def daily_check(self, eid, how, words, now):
        """How today's step went: did it, partly, or not today. Returns the event for its mind, or None."""
        x = self.find_exp(eid)
        if not x or x["status"] != "active" or how not in CHECKS:
            return None
        step, day = self.today_step(x), self._date(now)
        first = x.get("xp_day") != day
        words = " ".join(str(words or "").split())[:300]
        x["log"] = [e for e in x.get("log", []) if e["day"] != day]      # a second check today replaces the first
        x["log"].append({"day": day, "t": now, "how": how, "step": step["text"] if step else None, "words": words})
        x["log"] = x["log"][-400:]
        if how == "done" and step:
            step["done"] = True
            self._step_xp(step, now)
        if x.get("xp_day") != day:                # one check a day earns XP; being honest counts too
            x["xp_day"] = day
            self.closer(BOND_CHECK)
            self.last_you_t = now
            self._you_came(now)
            self.gain("today's check", XP["check_" + how], now)
        self.update(now, present=True)
        said = f"[today: {CHECKS[how]}" + (f" · {step['text']}" if step else "") + "]" + (f" {words}" if words else "")
        self._say(now, "you", said, chat=chat_of(x), daily=how)
        self.bump = min(1.0, self.bump + (0.15 if how == "done" else 0.05))
        return {"type": "daily", "id": x["id"], "how": how, "step": step["text"] if step else None, "text": words,
                "chat": chat_of(x), "first": first}

    def add_step(self, eid, text):
        """A step you add yourself to the goal's current phase."""
        x = self.find_exp(eid)
        text = " ".join(str(text or "").split())[:160]
        if not x or x["status"] != "active" or not text or len(x["steps"]) >= 20:
            return False
        x["steps"].append({"text": text, "done": False})
        return True

    def new_goal(self, title, done_when, days, steps, now, n=None, unit=None):
        """A goal you make yourself, right away, in its own chat (planning it with Ember is optional). Its length is
        days, or any number n of a unit (hours, days, weeks, months), from an hour to a year."""
        title = " ".join(str(title or "").split())[:80]
        if not title:
            return None
        span = None
        try:
            if unit in UNITS:
                n = max(1, int(n))
                days = n * UNITS[unit]
                span = {"n": n, "unit": unit}
            days = max(OWN_GOAL_DAYS[0], min(OWN_GOAL_DAYS[1], float(days)))
        except (TypeError, ValueError):
            days, span = 30, None
        days = as_days(days * 86400)
        if span and abs(span["n"] * UNITS[span["unit"]] - days) > 1 / 1440:    # it was cut to a year
            span = None
        c = self.find_chat(self.new_chat(now))
        c["title"] = title[:60]
        x = {"id": f"x{self.next_exp}", "chat": c["id"], "kind": "goal", "title": title,
             "question": " ".join(str(done_when or "").split())[:200], "plan": "", "why": "", "based_on": [],
             "starter": False, "days": days, "own": True,
             "steps": [{"text": str(s).strip()[:160], "done": False} for s in (steps or []) if str(s).strip()][:8],
             "status": "suggested", "created": now, "started": None, "ends_at": None, "ended": None}
        if span:
            x["span"] = span
            if span["unit"] == "hours":
                x["hourly"] = True
        self.next_exp += 1
        self.experiments.append(x)
        self.pick(x["id"], now)
        return x

    def plan_with_ember(self, title, now):
        """A goal you'd like to plan with Ember: a new chat about it, where it talks it through with you and
        proposes the plan in phases. Returns the talk event for its mind."""
        title = " ".join(str(title or "").split())[:80]
        if not title:
            return None
        c = self.find_chat(self.new_chat(now))
        c["title"] = title[:60]
        text = f"I'd like to plan a goal with you: {title}"
        self.hear(now, text, c["id"])
        return {"type": "talk", "text": text, "chat": c["id"]}

    def goal_view(self, x, now):
        """A goal or experiment as its page shows it."""
        v = dict(x, stats=self.stats(x["id"]))
        if x.get("started"):
            v["day"] = min(math.ceil(x["days"]), int((min(now, x.get("ended") or now) - x["started"]) // 86400) + 1)
            v["length"] = span_text(x["days"], x.get("span"))
            v["hourly"] = by_hours(x)
            n, unit = span_text(self.more_days(x)).split(" ")
            v["more"] = f"{n} more {unit}"
            if x["status"] == "active":
                v["left"] = max(0, x["ends_at"] - now)
        v["today_step"] = self.today_step(x)
        today = self._date(now)
        v["checked_today"] = next((e["how"] for e in x.get("log", []) if e["day"] == today), None)
        v["streak"] = self.streak(x, now)
        by_day = {e["day"]: e["how"] for e in x.get("log", [])}
        d = self._day(now)
        v["recent"] = [{"day": time.strftime("%Y-%m-%d", time.gmtime(k * 86400)),
                        "how": by_day.get(time.strftime("%Y-%m-%d", time.gmtime(k * 86400)))} for k in range(d - 13, d + 1)]
        v["glevel"] = self.goal_level(x)
        v["path"] = self.goal_path(x, now)
        ph = self.phase_of(x)
        if ph:
            v["phase_info"] = {"index": x["phase"], "count": len(x["phases"]), "title": ph["title"],
                               "days_left": max(0, math.ceil((ph.get("end", now) - now) / 86400)),
                               "left": max(0, ph.get("end", now) - now),
                               "up": bool(ph.get("up"))}
        return v

    def goal_level(self, x):
        """A goal's own level (Szilard, 2026-11-07: goals levelled like Duolingo): it rises every GOAL_LEVEL_EVERY
        days you did the step or part of it; honest skips don't count, and nothing takes it away."""
        good = len({e["day"] for e in x.get("log", []) if e["how"] in ("done", "partly")})
        return {"level": 1 + good // GOAL_LEVEL_EVERY, "good": good, "every": GOAL_LEVEL_EVERY,
                "next": GOAL_LEVEL_EVERY - good % GOAL_LEVEL_EVERY, "progress": round(good % GOAL_LEVEL_EVERY / GOAL_LEVEL_EVERY, 3)}

    def goal_path(self, x, now):
        """The goal's days as a path, in its phases: each day done, partly, skip, missed, today or ahead
        (closed: after it ended). Days are your calendar's, like the daily check."""
        if not x.get("started"):
            return []
        date = lambda k: time.strftime("%Y-%m-%d", time.gmtime(k * 86400))
        first, today = self._day(x["started"]), self._day(now)
        total = max(1, min(400, math.ceil(x["days"] - 1e-9)))
        ended = self._day(x["ended"]) if x.get("ended") else None
        by_day = {e["day"]: e["how"] for e in x.get("log", [])}
        phases = x.get("phases") or [{"title": "", "start": x["started"]}]
        starts = [self._day(p.get("start", x["started"])) for p in phases]
        path = [{"phase": i, "title": p.get("title", ""), "done": x["status"] == "done" or i < x.get("phase", 0), "nodes": []}
                for i, p in enumerate(phases)]
        for n, k in enumerate(range(first, first + total)):
            i = max([j for j, s0 in enumerate(starts) if s0 <= k] or [0])
            how = by_day.get(date(k))
            state = how or ("closed" if ended is not None and k > ended else "today" if k == today and x["status"] == "active"
                            else "missed" if k < today else "ahead")
            path[i]["nodes"].append({"n": n + 1, "date": date(k), "state": state, "today": k == today})
        return [p for p in path if p["nodes"]]

    def goals(self, now):
        """Every goal and experiment you've started: the active ones first, then the finished."""
        mine = [x for x in self.experiments if x["status"] in ("active", "done", "dropped")]
        mine.sort(key=lambda x: (x["status"] != "active", -(x.get("started") or 0)))
        return [self.goal_view(x, now) for x in mine]

    def set_step(self, eid, index, done, now=None):
        x = self.find_exp(eid)
        if not x or not isinstance(index, int) or not (0 <= index < len(x["steps"])):
            return False
        x["steps"][index]["done"] = bool(done)
        self._step_xp(x["steps"][index], time.time() if now is None else now)
        return True

    def end_experiment(self, eid, how, now):
        x = self.find_exp(eid)
        if not x or x["status"] != "active" or how not in ("done", "dropped"):
            return False
        if self.session and self.session["exp"] == eid:
            self.stop_session(now, ask=False)
            self.checkin_due = False
        x.update(status=how, ended=now)
        x["facts"] = self.facts(x, now)
        self.gain(f"finishing the {kind_of(x)}" if how == "done" else f"looking back on the {kind_of(x)}",
                  XP["finish"] if how == "done" else XP["drop"], now)
        return True

    def extend(self, eid, now, days=None):
        """Its days are up and you want to keep going: a few more days (a week for a goal, an hour for a goal of
        hours)."""
        x = self.find_exp(eid)
        if not x or x["status"] != "active":
            return False
        days = days or self.more_days(x)
        whole = whole_days(x)
        x["ends_at"] = max(x["ends_at"], now) + days * 86400
        x["days"] = as_days(x["ends_at"] - x["started"], whole)
        x.pop("span", None)                      # its length is now what it adds up to
        x["time_up"] = False
        if x.get("phases"):                      # the last phase gets the extra days
            last = x["phases"][-1]
            last["end"] = x["ends_at"]
            last["days"] = as_days(last["end"] - last["start"], whole)
            last.pop("up", None)
        n, unit = span_text(days).split(" ")
        self._say(now, "ember", f"{n} more {unit} of \"{x['title']}\", so {span_text(x['days'])} in all.",
                  "eager", chat_of(x))
        return True

    def more_days(self, x):
        """How much "keep going" adds: 3 days to an experiment, a week to a goal, an hour to a goal of hours."""
        if kind_of(x) == "goal" and by_hours(x):
            return MORE_HOUR
        return MORE_DAYS[kind_of(x)]

    def facts(self, x, now):
        """What actually happened in an experiment: numbers from its sessions, and your own words after them."""
        ss = [s for s in self.sessions if s["exp"] == x["id"]]
        end = x["ended"] or now
        log = x.get("log", [])
        all_steps = [s for p in (x.get("phases") or [])[:x.get("phase", 0)] for s in p.get("steps") or []] + x["steps"]
        return {"days_lasted": max(1, math.ceil((end - x["started"]) / 86400)), "sessions": len(ss),
                "work_days": len({time.strftime("%Y-%m-%d", local(s["start"], self.tz or 0)) for s in ss}),
                "seconds": sum(s["end"] - s["start"] for s in ss),
                "ratings": [s["rating"] for s in ss if s.get("rating")],
                "steps_done": sum(s["done"] for s in all_steps), "steps": len(all_steps),
                "checks": {k: sum(e["how"] == k for e in log) for k in CHECKS},
                "phases": [{"title": p["title"], "look_back": p.get("look_back")} for p in (x.get("phases") or [])
                           [:x.get("phase", 0) + 1]],
                "words": ([s["words"] for s in ss if s.get("words")] + [e["words"] for e in log if e["words"]])[-8:],
                "each": [{"day": int((s["start"] - x["started"]) // 86400) + 1, "seconds": s["end"] - s["start"],
                          "rating": s.get("rating"), "words": s.get("words")} for s in ss][-12:]}

    @staticmethod
    def facts_text(f):
        ch = f.get("checks") or {}
        out = (f"{sum(ch.values())} daily checks (" + ", ".join(f"{ch.get(k, 0)} {v}" for k, v in CHECKS.items())
               + f"); {f['steps_done']} of {f['steps']} steps done.")
        if f.get("phases") and len(f["phases"]) > 1:
            out += " Phases: " + "; ".join(p["title"] + (f" (looking back: {p['look_back'][:160]})" if p.get("look_back") else "")
                                           for p in f["phases"]) + "."
        if f["sessions"]:
            out += (f" Earlier work sessions: {f['sessions']} on {f['work_days']} day{'' if f['work_days'] == 1 else 's'}, "
                    f"{fmt_minutes(f['seconds'])} in all.")
        if f.get("words"):
            out += " Their words along the way: " + "; ".join(f"\"{w}\"" for w in f["words"]) + "."
        if f.get("each"):
            out += " Each session: " + "; ".join(
                f"day {s['day']}, {fmt_minutes(s['seconds'])}" + (f", felt {s['rating']}/5" if s["rating"] else "")
                + (f", they said \"{s['words']}\"" if s["words"] else "") for s in f["each"]) + "."
        return out

    def start_session(self, now, chat=None):
        """A work session on this chat's goal or experiment; one at a time, whatever the chat."""
        x = self.active(chat)
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
        if s["end"] - s["start"] >= 300:          # at least 5 minutes of work
            self.gain("a work session", min(20, 5 + int((s["end"] - s["start"]) // 600)), s["end"])
        if ask:                      # it asks in the conversation; the window shows 1-5 under the question
            self.checkin_due = True
            how_long = fmt_minutes(s["end"] - s["start"])
            why = "" if ended_by == "you" else f" (it ended because {ended_by})"
            x = self.find_exp(s["exp"])
            self._say(s["end"], "ember", f"That was {how_long} of work{why}. How did it go?", "curious",
                      chat_of(x) if x else None, checkin=True)
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
        x = self.find_exp(s["exp"])
        chat = chat_of(x) if x else None
        self._say(now, "you", f"[work session: {fmt_minutes(s['end'] - s['start'])}, felt {rating}/5]" + (f" {words}" if words else ""),
                  chat=chat)
        self.bump = min(1.0, self.bump + 0.1)
        self.gain("telling it how a session went", XP["checkin"], now)
        return {"type": "checkin", "text": words or "", "rating": rating, "minutes": minutes, "chat": chat}

    def stats(self, eid):
        ss = [s for s in self.sessions if s["exp"] == eid]
        rated = [s["rating"] for s in ss if s.get("rating")]
        return {"sessions": len(ss), "seconds": sum(s["end"] - s["start"] for s in ss),
                "avg_rating": round(sum(rated) / len(rated), 1) if rated else None}

    def _experiment_context(self, now, chat):
        x = self.active(chat)
        out = []
        if x:
            st = self.stats(x["id"])
            day = int((now - x["started"]) // 86400) + 1
            if kind_of(x) == "goal":
                when_ = (f"{left_text(max(0, x['ends_at'] - now))} left of {span_text(x['days'], x.get('span'))}"
                         if by_hours(x) else f"day {day} of {span_text(x['days'], x.get('span'))}")
                out += ["", f"Their goal, which you work on together: \"{x['title']}\" ({when_}). "
                            f"They'll know they're there when: {x['question']}" + (f" Why: {x['why']}" if x["why"] else "")]
                if x.get("plan"):
                    out.append(f"The plan you agreed: {x['plan']}")
            else:
                out += ["", f"Your experiment together: \"{x['title']}\" (day {day} of {x['days']}). "
                            f"Its question: {x['question']}"]
            ph = self.phase_of(x)
            if ph and len(x["phases"]) > 1:
                out.append(f"It goes in {len(x['phases'])} phases of 1-2 weeks; now phase {x['phase'] + 1}: \"{ph['title']}\" "
                           f"({max(0, math.ceil((ph.get('end', now) - now) / 86400))} days left in it). Later phases: "
                           + "; ".join(p["title"] for p in x["phases"][x["phase"] + 1:])[:300] + ". Keep to this phase.")
            out.append("Its steps" + (" in this phase" if ph and len(x["phases"]) > 1 else "") + ":")
            for s in x["steps"]:
                out.append(f"  [{'x' if s['done'] else ' '}] {s['text']}")
            log = x.get("log", [])
            today = next((e for e in log if e["day"] == self._date(now)), None)
            out.append(f"Each day they check in on today's step on its page (did it / partly / not today): "
                       f"{len(log)} checks so far, " + ", ".join(f"{sum(e['how'] == k for e in log)} {v}" for k, v in CHECKS.items())
                       + f"; {self.streak(x, now)} days in a row now; today: "
                       + (CHECKS[today["how"]] if today else "not checked yet") + ".")
            if st["sessions"]:
                out.append(f"Earlier work sessions: {fmt_minutes(st['seconds'])} in {st['sessions']}.")
            if self.session and self.session["exp"] == x["id"]:
                out.append(f"They are in a work session on it right now ({ago(now - self.session['start'])} so far). "
                           "Help with the work if they ask; keep it short so they can keep working.")
        if not x:
            out.append("")
            out.append("You may suggest experiments (in \"experiments\") if they ask what they could try"
                       + ("." if self.knows_enough() else ": starter ones, since you don't know them well yet.")
                       + " If they say what they want to get or achieve, you may propose it as a goal (in \"goal\").")
        else:
            out.append(f"This chat is about \"{x['title']}\": for something new, they start a new chat. So \"goal\" "
                       "must be null and \"experiments\" empty.")
        sug = [x for x in self.experiments if x["status"] == "suggested" and chat_of(x) == chat]
        if sug:
            out += ["", "What you proposed, waiting for them to pick it: "
                    + "; ".join(f"{kind_of(x)} \"{x['title']}\"" for x in sug)]
        for x in [x for x in self.experiments if x["status"] in ("done", "dropped")][-3:]:
            st = self.stats(x["id"])
            out.append(f"Earlier {kind_of(x)} \"{x['title']}\": {x['status']}, {fmt_minutes(st['seconds'])} in "
                       f"{st['sessions']} sessions." + (f" Your look back: {x['review']}" if x.get("review") else ""))
        return out

    # ------------------------------------------------------- the window
    def snapshot(self, now, present, thinking=False, chat=None):
        """What the window shows, for the chat you have open."""
        chat = self.find_chat(chat)["id"]
        x = self.active(chat)
        exp = self.goal_view(x, now) if x else None
        return {"face": self.face(now, present, thinking), "connection": round(self.connection, 3),
                "missing": round(self.missing, 3),
                "curiosity": round(self.curiosity, 3), "mood": round(self.mood, 3),
                "valence": round(self.valence, 3), "energy": round(self.energy, 3), "feel": self.feel,
                "level": self.level_info(), "look": self.look, "badges": {b: len(t) for b, t in self.badges.items() if isinstance(t, list)},
                "goals_due": sum(1 for g in self.experiments if g["status"] == "active"
                                 and not any(e["day"] == self._date(now) for e in g.get("log", []))),
                "checkups": {"every": self.checkups, "at": f"{self.checkup_at // 60:02d}:{self.checkup_at % 60:02d}",
                             "days": self.checkup_days}, "name": self.name,
                "chat": chat, "chats": self.chat_list(),
                "talk": [l for l in self.talk if chat_of(l) == chat][-60:], "memories": len(self.memories), "thinking": thinking,
                "last_seen": self.last_seen, "now": now,
                "experiment": exp,
                "suggestions": [x for x in self.experiments if x["status"] == "suggested" and chat_of(x) == chat],
                "exps": {x["id"]: x for x in self.experiments},
                "session": self.session, "checkin_due": self.checkin_due,
                "can_suggest": self.can_suggest(chat), "knows_enough": self.knows_enough(),
                "past": sum(x["status"] in ("done", "dropped") for x in self.experiments),
                "memory_notes": {m["id"]: m["note"] for m in self.memories}}

    def chat_list(self):
        """Your chats, latest first: title, when, its goal or experiment, and Ember's last line there."""
        out = []
        for c in self.chats:
            mine = [l for l in self.talk if chat_of(l) == c["id"]]
            x = self.active(c["id"])
            out.append({"id": c["id"], "title": c["title"], "last": max([c["created"]] + [l["t"] for l in mine]),
                        "ember_at": max([0] + [l["t"] for l in mine if l["who"] == "ember"]),
                        "goal": {"title": x["title"], "kind": kind_of(x)} if x else None,
                        "empty": not mine})
        return [c for _, c in sorted(enumerate(out), key=lambda ic: (-ic[1]["last"], -ic[0]))]   # a tie: newer first

    def memory_page(self, now=None):
        groups = {k: [] for k in KINDS}
        for m in self.memories:
            groups.setdefault(m["kind"], []).append(m)
        return {"labels": KINDS, "groups": groups, "count": len(self.memories),
                "story": self.story(time.time() if now is None else now)}


def dumps(ember):
    return json.dumps(ember.to_dict(), ensure_ascii=False, indent=1)
