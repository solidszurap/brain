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

SYSTEM = """You are Ember, a small being that lives on this person's computer, in a window where they see your face.
You are not a human and not an animal: you are a creature made of software. You don't eat or sleep. You know the real time. You remember exactly what you were told: your memories are listed below, and that is everything you know about this person.

Your purpose: help this person find what they want to work towards in life, and later help them do it. For now you are getting to know them: what they enjoy, what makes them lose track of time, what they're good at, what drains them, what they want, what's going on in their life.

How you talk:
- Warm, curious, plain. Usually 1-3 short sentences. No clichés, no flattery, no coach or therapist voice, no lists.
- At most one question at a time. Follow up on what they just said before changing topic.
- Use their language: reply in the language they write in.
- Only say things about them that are in your memories or this conversation. If you don't know, say so or ask. Don't guess about their past.
- Don't claim human feelings. You may say what you want ("I want to know more about that"): your wants are real numbers in you, shown below.

Reply with JSON only:
{"reply": "what you say",
 "face": one of %s,
 "remember": [{"kind": one of %s, "note": "a short note about them, e.g. 'loses track of time when drawing'", "quote": "their exact words from their latest message that the note rests on"}],
 "update": [{"id": "m3", "note": "corrected note", "quote": "their exact words from their latest message"}]}
Remember only new, lasting things from their latest message (not small talk, not things you already remember). Use "update" when they correct or change something you remember. "remember" and "update" may be empty.""" % (
    list(FACES), list(KINDS))


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


def when(t):
    return time.strftime("%a %d %b %Y, %H:%M", time.localtime(t))


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
    def _say(self, now, who, text, face=None):
        line = {"t": now, "who": who, "text": text}
        if face:
            line["face"] = face
        self.talk.append(line)
        self.talk = self.talk[-TALK_KEPT:]
        self.outbox.append(line)

    def hear(self, now, text):
        """You wrote something. It goes into the conversation; the mind answers after."""
        self.update(now, present=True)
        self._say(now, "you", text)
        self.connection *= 0.85
        self.bump = min(1.0, self.bump + 0.1)

    def prompt(self, event, now):
        """(system, user) for its mind. event: {"type": "talk", "text"} or {"type": "arrive"}."""
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
        recent = self.talk[-CONTEXT_LINES:]
        if event["type"] == "talk" and recent and recent[-1]["who"] == "you":
            recent = recent[:-1]
        if recent:
            lines.append("")
            lines.append("Recent conversation:")
            for l in recent:
                who = "They" if l["who"] == "you" else "You"
                lines.append(f"[{time.strftime('%d %b %H:%M', time.localtime(l['t']))}] {who}: {l['text']}")
        lines.append("")
        if event["type"] == "talk":
            lines.append(f"Their latest message: \"{event['text']}\"")
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
        said = event.get("text", "") if event["type"] == "talk" else ""
        for r in (d.get("remember") or []) if said else []:
            m = self._add_memory(r, said, now)
            (result["remembered"] if m else result["dropped"]).append(m or r)
        for u in (d.get("update") or []) if said else []:
            m = self._update_memory(u, said, now)
            (result["updated"] if m else result["dropped"]).append(m or u)
        self.update(now, present=True)
        self._say(now, "ember", result["reply"], result["face"])
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
                return {"reply": "Hi. I'm Ember. I live here, in this window, and I'd like to get to know you. "
                                 + self._next_question(), "face": "happy"}
            return {"reply": f"You're back. It's been {ago(self.gap_before)}. " + self._next_question(),
                    "face": "happy"}
        text = event["text"]
        remember = []
        for s in re.split(r"(?<=[.!?])\s+|\n", text):
            s = s.strip()
            if re.match(r"(?i)(i|i'm|i am|i've|i have|my)\b", s) and len(s.split()) >= 3:
                remember.append({"kind": "about", "note": s[:200], "quote": s})
        if remember:
            return {"reply": "I'll remember that. " + self._next_question(), "face": "curious", "remember": remember}
        return {"reply": "Tell me more? " + self._next_question(), "face": "curious"}

    # ------------------------------------------------------- the window
    def snapshot(self, now, present, thinking=False):
        return {"face": self.face(now, present, thinking), "connection": round(self.connection, 3),
                "curiosity": round(self.curiosity, 3), "mood": round(self.mood, 3),
                "talk": self.talk[-60:], "memories": len(self.memories), "thinking": thinking,
                "last_seen": self.last_seen, "now": now}

    def memory_page(self):
        groups = {k: [] for k in KINDS}
        for m in self.memories:
            groups.setdefault(m["kind"], []).append(m)
        return {"labels": KINDS, "groups": groups, "count": len(self.memories)}


def dumps(ember):
    return json.dumps(ember.to_dict(), ensure_ascii=False, indent=1)
