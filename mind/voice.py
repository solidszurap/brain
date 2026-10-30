"""
Ember's voice: the language cortex, wired the way the project's thesis says
it should be.

The LLM is not Ember. It is one part of Ember's brain, the part that turns
what is in the rest of the mind into words. So it sees only what Ember's
mind holds (`build_dossier`): what is in its workspace now, its body, where
it believes it is and how sure it is, what it has found out, and the
memories that the question brings back. It never sees the world, the
scientist's records, or anything Ember hasn't experienced. It cannot know
what Ember doesn't.

Every answer comes with *claims*, each pointing at the memories it rests on
(the receipts). `check` then sorts every claim:

  true            backed by its memory, and the memory was right
  honest mistake  backed by its memory, but the memory was wrong (a false belief)
  made up         not backed by anything it remembers: the language cortex invented it
  unverified      backed by its memory; no way to check that memory
  guess           it said itself that it was guessing

Whether a memory was right comes from the witness (mind/witness.py), on the
scientist's side. With an LLM, a second, separate call (the judge) checks
that each claim really says what its receipts say, and catches statements
that came with no receipt.

Voices (set in .env, see .env.example): Claude, Gemini (has a free tier),
any OpenAI-compatible server (OpenAI, OpenRouter, LM Studio), Ollama (free,
runs on your computer), or none: a simple template voice that needs nothing.
No packages beyond the standard library.
"""
import json
import os
import re
import time
import urllib.error
import urllib.request

DEFAULT_MODELS = {"anthropic": "claude-haiku-5-5", "gemini": "gemini-3.8-flash", "ollama": "llama3.2", "openai": None}
NAMES = {"anthropic": "Claude", "gemini": "Gemini", "openai": "OpenAI-compatible", "ollama": "Ollama",
         "template": "template voice (no LLM)"}
GOAL_WORDS = {"food": "find food", "water": "get water", "explore": "explore", "avoid": "get away from a hazard",
              "rest": "rest", None: "nothing in particular"}
MAX_QUESTION = 500


class VoiceError(Exception):
    pass


# ======================================================================= config
class VoiceConfig:
    """Which voice to use. EMBER_VOICE = auto | template | anthropic | gemini | openai | ollama.
    auto: the first of Claude, Gemini, OpenAI that has a key; else the template voice."""

    def __init__(self, env=None):
        env = os.environ if env is None else env
        choice = (env.get("EMBER_VOICE") or "auto").strip().lower()
        keys = {"anthropic": env.get("ANTHROPIC_API_KEY"), "gemini": env.get("GEMINI_API_KEY"),
                "openai": env.get("OPENAI_API_KEY")}
        if choice == "auto":
            choice = next((p for p in ("anthropic", "gemini", "openai") if keys[p]), "template")
        if choice not in NAMES:
            choice = "template"
        self.provider = choice
        self.key = keys.get(choice)
        self.model = env.get("EMBER_VOICE_MODEL") or DEFAULT_MODELS.get(choice)
        self.base_url = (env.get("EMBER_VOICE_URL") or env.get("OPENAI_BASE_URL")
                         or ("http://localhost:11434/v1" if choice == "ollama" else "https://api.openai.com/v1"))
        self.judge = choice != "template" and (env.get("EMBER_VOICE_JUDGE", "1") != "0")
        self.problem = None
        if choice in ("anthropic", "gemini", "openai") and not self.key:
            self.problem = f"EMBER_VOICE={choice} but no API key is set"
        if choice in ("openai", "ollama") and not self.model:
            self.problem = "set EMBER_VOICE_MODEL to the model's name"

    def describe(self):
        if self.provider == "template":
            return NAMES["template"]
        return f"{NAMES[self.provider]} ({self.model})" + (" + judge" if self.judge else "")


def load_dotenv(path):
    """KEY=VALUE lines into the environment (existing variables win). No package needed."""
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k, v = k.strip(), v.strip().strip('"').strip("'")
            if k and k not in os.environ:
                os.environ[k] = v


# ==================================================================== providers
def _post(url, body, headers, timeout=60):
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={"content-type": "application/json",
                                                                                  **headers})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        msg = e.read().decode("utf-8", "replace")[:300]
        raise VoiceError(f"HTTP {e.code}: {msg}") from None
    except urllib.error.URLError as e:
        raise VoiceError(f"can't reach {url.split('/')[2]}: {e.reason}") from None


def call_llm(cfg, system, user, max_tokens=1200):
    if cfg.problem:
        raise VoiceError(cfg.problem)
    p = cfg.provider
    if p == "anthropic":
        d = _post("https://api.anthropic.com/v1/messages",
                  {"model": cfg.model, "max_tokens": max_tokens, "system": system,
                   "messages": [{"role": "user", "content": user}]},
                  {"x-api-key": cfg.key, "anthropic-version": "2023-06-01"})
        return "".join(b.get("text", "") for b in d.get("content", []) if b.get("type") == "text")
    if p == "gemini":
        d = _post(f"https://generativelanguage.googleapis.com/v1beta/models/{cfg.model}:generateContent",
                  {"systemInstruction": {"parts": [{"text": system}]},
                   "contents": [{"role": "user", "parts": [{"text": user}]}],
                   "generationConfig": {"maxOutputTokens": max(max_tokens, 2048)}},
                  {"x-goog-api-key": cfg.key})
        parts = (d.get("candidates") or [{}])[0].get("content", {}).get("parts", [])
        return "".join(x.get("text", "") for x in parts if not x.get("thought"))
    if p in ("openai", "ollama"):
        headers = {"authorization": f"Bearer {cfg.key}"} if cfg.key else {}
        d = _post(cfg.base_url.rstrip("/") + "/chat/completions",
                  {"model": cfg.model, "messages": [{"role": "system", "content": system},
                                                    {"role": "user", "content": user}]}, headers, timeout=120)
        return d["choices"][0]["message"]["content"] or ""
    raise VoiceError("no LLM configured")


def parse_json(text):
    """The first {...} in the reply, tolerating code fences and chatter around it."""
    if not text:
        return None
    t = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.M).strip()
    i, j = t.find("{"), t.rfind("}")
    if i < 0 or j <= i:
        return None
    try:
        return json.loads(t[i:j + 1])
    except json.JSONDecodeError:
        return None


# ===================================================================== dossier
SYNONYMS = {
    "hungry": "food energy ate eat meal relief hungry", "hunger": "food energy ate eat hungry", "eat": "food ate eat meal",
    "ate": "food ate eat meal", "food": "food ate eat meal", "thirsty": "water drank drink hydration thirsty",
    "thirst": "water drank drink thirsty", "drink": "water drank drink", "water": "water drank drink pond",
    "gate": "gate lever plan orchard", "lever": "lever gate plan", "orchard": "orchard gate plan",
    "berry": "berry berries dark sick", "berries": "berry berries dark sick", "sick": "sick berry dark",
    "blackout": "came_round blacked weak dark", "blacked": "came_round blacked weak", "faint": "came_round blacked",
    "fainted": "came_round blacked", "collapse": "came_round blacked", "collapsed": "came_round blacked",
    "unconscious": "came_round blacked", "pass": "came_round blacked", "push": "surprise pushed push wind",
    "pushed": "surprise pushed push wind", "wind": "surprise pushed wind", "hurt": "hurt hazard pain bog",
    "pain": "hurt hazard", "mirror": "mirror figure pool reflection", "figure": "mirror figure pool",
    "figures": "mirror figure pool", "reflection": "mirror figure pool reflection", "pool": "mirror pool figure",
    "lost": "unsure lost where", "learn": "learned found", "learned": "learned found", "first": "first",
    "voice": "voice said spoke", "talk": "voice said spoke", "said": "voice said spoke", "told": "voice said spoke",
    "winter": "winter", "spring": "spring", "summer": "summer", "autumn": "autumn", "fall": "autumn",
    "sleep": "slept sleep", "slept": "slept sleep", "afraid": "hazard hurt threat", "scared": "hazard hurt threat",
}
STOP = set("a an the i you your me my is are was were do did does to of in on at it and or what why how when where "
           "who which that this there have has had be been can could would will about any ever with for from "
           "remember tell think know last ago yesterday today recently time times once happened happen "
           "go went get got doing done".split())
PAST_WORDS = ("remember", "did you", "were you", "have you", "yesterday", "last", "ago", "before", "ever", "when did",
              "why did", "what happened", "told you", "said")
SEASONS = ("spring", "summer", "autumn", "winter")


def _words(s):
    return re.findall(r"[a-zA-Z_']+", s.lower())


def _expand(question):
    terms = set()
    for w in _words(question):
        if w in STOP or len(w) < 3 or w in SEASONS or w == "fall":     # seasons are handled as time, not content
            continue
        terms.add(w)
        terms.update(SYNONYMS.get(w, "").split())
        if w.endswith("s"):
            terms.update(SYNONYMS.get(w[:-1], "").split())
    return terms


def attention_words(key):
    """A workspace content in Ember's words."""
    if not key:
        return "nothing in particular"
    kind, _, target = key.partition(":")
    table = {
        "need": {"energy": "my need for food", "hydration": "my need for water", "integrity": "my hurt body"},
        "percept": {"food": "food I can see", "water": "water I can see"},
        "recall": {"food": "remembering where food is", "water": "remembering where water is"},
        "surprise": {"push": "being pushed by something"},
        "curiosity": {"explore": "exploring", "patrol": "checking places I haven't seen for a while"},
        "threat": {"hazard": "a hazard right next to me"},
        "plan": {"open the gate": "my plan to open the gate"},
        "self": {"unsure where I am": "not knowing where I am", "reflection": "the figure that moves with me"},
        "voice": {"someone speaking": "the voice speaking to me"},
    }
    if kind in table and target in table[kind]:
        return table[kind][target]
    if kind == "novel":
        return f"something new: a {target}"
    if kind == "hearing":
        return f"the sound of the {target}"
    return key


def _body_words(b):
    e, h, i = b
    hunger = "very hungry" if e < 0.25 else "hungry" if e < 0.5 else "not hungry"
    thirst = "very thirsty" if h < 0.25 else "thirsty" if h < 0.5 else "not thirsty"
    hurt = "badly hurt" if i < 0.5 else "a little hurt" if i < 0.9 else "not hurt"
    return f"energy {e:.0%} ({hunger}), water {h:.0%} ({thirst}), body {i:.0%} ({hurt})"


def _ago(now, t):
    d = max(0, int(now) - int(t))
    if d < 15:
        return "just now"
    if d < 1000:
        return f"about {round(d, -1) if d >= 100 else d} moments ago"
    return f"about {round(d, -2):,} moments ago"


def _event_text(ev, ab, now, place_name):
    if ev.get("vague"):
        when = "long ago, before my memories were clear"
    else:
        label = ab.period_label(ev.get("period")) if ev.get("period") is not None else None
        when = ", ".join(x for x in (label, _ago(now, ev["t"])) if x)
    where = place_name(ev["place"]) if ev.get("place") is not None else None
    head = when + (f"; I believed I was in {where}" if where else "")
    text = ev["text"] + (f" (this happened {ev['n']} times in a row)" if ev.get("n", 1) > 1 else "")
    return f"({head}) {text}"[:260]


def _period_text(p, ab, place_name):
    label = ab.period_label(p["index"]) or p["season"]
    c = p["counts"]
    bits = [f"ate {c.get('meals', 0)} times", f"drank {c.get('drinks', 0)} times"]
    for k, w in (("came_round", "blacked out {} times"), ("plans_done", "opened the gate myself {} times"),
                 ("sick", "got sick from dark berries {} times"), ("hurt", "got hurt {} times"),
                 ("pushes_felt", "felt pushed {} times"), ("sleeps", "slept {} times")):
        if c.get(k):
            bits.append(w.format(c[k]))
    places = []
    for (cy, cx), _ in p["places"].most_common(6):
        n = place_name((cy * 4 + 2, cx * 4 + 2))
        if n and n not in places:
            places.append(n)
    where = f" I was mostly in {', '.join(places[:3])}." if places else ""
    ongoing = " (still going on)" if p.get("t_end") is None else ""
    return f"{label.capitalize()}{ongoing}: I {', '.join(bits)}.{where}"


def build_dossier(mind, question, place_name, heard=True, attention_now=None):
    """Everything the language cortex may use to answer: built from Ember's
    mind only. `place_name` turns a cell of its own map into our name for
    that part of its world (see mind/witness.py); it says nothing about
    whether Ember is right."""
    ab = mind.autobiography()
    now = mind.t
    items = []

    def add(iid, section, text, **data):
        items.append({"id": iid, "section": section, "text": text, **data})

    body = ab.last_body or [round(float(v), 2) for v in mind._ctx.get("intero", [1, 1, 1])]
    add("now:body", "now", "My body: " + _body_words(body) + ".")
    cur = attention_now if attention_now is not None else (str(mind.gw.current) if mind.gw.current else None)
    report = (mind.last or {}).get("report")
    if cur and cur.startswith("voice:"):
        add("now:attention", "now", "My attention is on the voice speaking to me.")
    elif cur:
        add("now:attention", "now", f"What has my attention right now: {attention_words(cur)}.", key=cur)
    else:
        add("now:attention", "now", "Nothing in particular is in my workspace right now.")
    goal = "sleep" if mind.sleeping else mind.pfc.goal
    gtxt = "I was asleep." if goal == "sleep" else f"What I'm trying to do: {GOAL_WORDS.get(goal, goal)}."
    if getattr(mind, "subgoal", None):
        gtxt += f" First I have to open the gate; what I need ({mind.subgoal['for']}) is behind it."
    add("now:goal", "now", gtxt)
    hp = mind.hippo
    unsure = hp.lost or getattr(hp, "uncertainty", 0.0) >= 1.5 or getattr(hp, "confidence", 1.0) < 0.6
    if unsure:
        add("now:place", "now", "I don't know exactly where I am right now.", cell=None)
    else:
        cell = tuple(int(v) for v in hp.pos)
        name = place_name(cell) or "a part of my world I have no name for"
        near = ""
        if getattr(mind, "gate_known", None):
            if min(abs(cell[0] - c[0]) + abs(cell[1] - c[1]) for c in mind.gate_known) <= 3:
                near = ", near the orchard gate"
        sure = "I'm sure of it" if hp.confidence >= 0.9 else "I think so, but I'm not completely sure"
        add("now:place", "now", f"I believe I'm in {name}{near}. {sure}.", cell=cell)
    if getattr(mind, "season", None):
        add("now:season", "now", f"It feels like {mind.season}.", season=mind.season)
    if getattr(mind, "gate_known", None):
        add("now:gate", "now", f"I believe the orchard gate is {'open' if mind.gate_open_belief else 'shut'}.",
            belief=bool(mind.gate_open_belief))
    add("now:voice", "now", "Someone is speaking to me. I can hear them; I can't see them. " +
        ("I noticed them: the voice reached my workspace." if heard else
         f"I barely noticed: my attention stayed on {attention_words(cur)}."), heard=bool(heard))
    add("now:age", "now", f"I have been awake for about {round(now, -2):,} moments. I remember things clearly "
        f"only from about moment {round(ab.started_t, -2):,} on; of the time before, only a little.")
    if ab.last_meal_t is not None:
        add("now:meal", "now", f"I last ate {_ago(now, ab.last_meal_t)}.")
    if ab.last_drink_t is not None:
        add("now:drink", "now", f"I last drank {_ago(now, ab.last_drink_t)}.")

    add("self:agency", "self", "I can tell when I move myself from when something else moves me, like the wind. "
        f"My last movement: {'something else moved me' if mind.agency == 'external' else 'I moved myself'}.")
    mir = getattr(mind, "mirror", None)
    if getattr(mind, "knows_reflection", False):
        add("self:mirror", "self", "By the still pool there are figures. One moves exactly when I move: I think it is me.")
    elif mir is not None and mir.n_classified:
        add("self:mirror", "self", f"By the still pool there are figures. I have watched them {mir.n_classified} times; "
            f"{mir.n_self} time{'s' if mir.n_self != 1 else ''} one moved with me. I'm not sure yet whether one of them is me.")

    from .wideworld import TYPE_NAMES_WIDE as TN, LEVER
    for k in sorted(getattr(mind, "harmful", set())):
        add(f"k:harmful:{k}", "knowledge", f"{TN[k].capitalize()}s hurt me; I keep away from them."
            if TN[k] != "dark berry" else "Dark berries hurt me; I don't eat them.", fact=f"harmful:{TN[k]}")
    for (kind, sound), _ in getattr(mind, "rules", {}).items():
        if sound == "gate_opened":
            add("k:rule:gate", "knowledge", f"Stepping on the {TN[kind]} opens the gate. I hear the gate from anywhere.",
                fact="rule:lever" if kind == LEVER else f"rule:{TN[kind]}")
    known = int((hp.map >= 0).sum())
    add("k:map", "knowledge", f"I know about {round(known, -1):,} places in my world.")
    from .world import WATER
    waters = []
    for c in list(zip(*(hp.map == WATER).nonzero()))[:400]:
        n = place_name(c)
        if n and n not in waters:
            waters.append(n)
    if waters:
        add("k:water", "knowledge", "I know where water is: in " + ", ".join(waters[:5]) + ".")
    seasons = {}
    for cell, cnt in getattr(mind, "season_memory", {}).items():
        for s in SEASONS:
            if cnt.get(s, 0) >= 1:
                n = place_name(cell)
                if n:
                    seasons.setdefault(s, set()).add(n)
    if seasons:
        add("k:food_seasons", "knowledge", "Where I have seen food grow: " + "; ".join(
            f"in {s}, {', '.join(sorted(v)[:3])}" for s, v in seasons.items()) + ".")

    # ---- memories the question brings back ----------------------------
    evs = [e for e in ab.events() if e["kind"] not in ("voice", "said")]
    terms = _expand(question)
    ql = question.lower()
    wants_old = any(w in ql for w in ("first", "earliest", "oldest", "beginning", "born", "young"))
    wants_recent = any(w in ql for w in ("now", "just", "recent", "today", "lately", "doing"))
    season_target = None
    for s in SEASONS + ("fall",):
        if s in ql:
            s = "autumn" if s == "fall" else s
            label = (f"last {s}" if "last" in ql else f"this {s}" if "this" in ql else None)
            season_target = (s, label)
    scored = []
    for e in evs:
        words = set(_words(e["text"])) | {e["kind"], (e.get("key") or "").split(":")[0], e.get("season") or ""}
        if e.get("place") is not None:
            words |= set(_words(place_name(e["place"]) or ""))
        overlap = content = len(terms & words)
        recency = 1.0 / (1.0 + (now - e["t"]) / 2000.0)
        sc = 2.0 * overlap + e["importance"] + (2.0 if wants_recent else 0.5) * recency
        if wants_old:
            sc += 1.5 * (1.0 - recency) + (1.0 if e.get("first") or e["kind"] == "learned" else 0)
        if season_target:
            s, label = season_target
            if e.get("season") == s:
                sc += 1.0
                if label is None or (e.get("period") is not None and ab.period_label(e["period"]) == label):
                    sc += 2.0
                    overlap += 1                  # the time asked about counts as a match
        scored.append((sc, overlap, content, e))
    scored.sort(key=lambda x: -x[0])
    chosen = {id(e): e for _, _, _, e in scored[:10]}
    for e in evs[-5:]:
        chosen[id(e)] = e
    matched = sum(1 for sc, ov, ct, e in scored[:10] if ov > 0)
    content_hits = sum(1 for sc, ov, ct, e in scored[:10] if ct > 0)
    rank = {id(e): (sc, ov) for sc, ov, ct, e in scored}
    for e in sorted(chosen.values(), key=lambda e: e["t"]):
        sc, ov = rank[id(e)]
        add(e["id"], "memory", _event_text(e, ab, now, place_name), event=dict(e), score=round(sc, 3), overlap=ov)
    periods = ab.all_periods()
    pick = periods[-2:]
    if season_target:
        s, label = season_target
        pick += [p for p in periods if p["season"] == s and (label is None or ab.period_label(p["index"]) == label)][-2:]
    seen = set()
    for p in sorted(pick, key=lambda p: p["index"]):
        if p["id"] not in seen:
            seen.add(p["id"])
            add(p["id"], "season", _period_text(p, ab, place_name))
    conv = [e for e in ab.events() if e["kind"] in ("voice", "said")
            and not (e["kind"] == "voice" and e["t"] >= now)][-8:]      # not the question being asked now
    for e in conv:
        add(e["id"], "conversation", f"({_ago(now, e['t'])}) {e['text']}"[:300], event=dict(e))
    return {"items": items, "question": question[:MAX_QUESTION], "t": int(now), "memory_hits": matched,
            "content_terms": len(terms), "content_hits": content_hits,
            "looks_past": any(w in ql for w in PAST_WORDS)}


def render(dossier):
    titles = {"now": "RIGHT NOW", "self": "WHAT I CAN TELL ABOUT MYSELF", "knowledge": "WHAT I HAVE FOUND OUT",
              "memory": "MEMORIES THE QUESTION BRINGS BACK (oldest first)", "season": "WHOLE SEASONS, AS I REMEMBER THEM",
              "conversation": "EARLIER CONVERSATION WITH THIS VOICE"}
    out, last = [], None
    for it in dossier["items"]:
        if it["section"] != last:
            out.append(f"\n{titles[it['section']]}")
            last = it["section"]
        out.append(f"[{it['id']}] {it['text']}")
    return "\n".join(out).strip()


# ====================================================================== speaking
SYSTEM = """You are the language area of the brain of Ember, a small creature that lives one long, continuous life in its own world. You are not an assistant and not a chatbot. Ember's other brain parts decide everything; you only turn what is in Ember's mind into Ember's words.

You get Ember's MIND: numbered items about its body and attention right now, what it can tell about itself, what it has found out, and the memories the question brought back. That is ALL Ember knows. It knows nothing about humans, the internet, computers or anything outside its world unless an item says so. It cannot see the one who is speaking; it only hears a voice.

Rules:
1. Speak as Ember, in the first person, in plain short sentences. Usually 1 to 4 sentences. Answer in the language the speaker used.
2. Use only the items. Never add events, places, numbers, causes or feelings that no item gives you.
3. If the items don't contain the answer, say so simply: "I don't remember that." / "I don't know." Do not guess about the past. If you do make a guess about something else, say "I think" or "maybe" and mark that claim as a guess.
4. If a question takes for granted something that isn't in your memory ("why did you do X?"), say you don't remember doing X.
5. Feelings: Ember has needs and states, not human emotions. Words like hungry, thirsty, hurt, weak, tired, unsure, surprised are fine when an item supports them. Don't claim love, sadness, joy or fear unless an item gives a matching state.
6. If asked whether you are conscious, feel things or are alive: say what you can tell about yourself from the items (what reaches your attention, telling your own movement from being pushed, knowing where you are) and that you can't tell whether there is anything it feels like to be you. Never claim certainty either way.
7. If the item now:voice says you barely noticed the voice, answer very briefly and distractedly, about what has your attention.
8. You may sometimes end with one short question back to the voice, if Ember would be curious.
9. A memory can be wrong; you don't know which. Say what you remember the way you remember it.

Reply with JSON only, no other text:
{"say": "what Ember says", "claims": [{"text": "one fact the answer states", "because": ["item ids it rests on"], "guess": false}]}
Every fact about Ember's past, present body, place, world or knowledge that "say" contains must appear as a claim citing the item ids it comes from. Greetings and questions back are not claims."""


def speak(cfg, dossier):
    """Ember answers. Returns {"say", "claims", "voice", "error"?}. Never raises."""
    if cfg.provider == "template":
        return {**template_answer(dossier), "voice": cfg.describe()}
    user = render(dossier) + f'\n\nThe voice says: "{dossier["question"]}"\n\nAnswer as Ember (JSON only).'
    try:
        raw = call_llm(cfg, SYSTEM, user)
    except VoiceError as e:
        return {**template_answer(dossier), "voice": NAMES["template"], "error": f"{cfg.describe()} unavailable: {e}"}
    data = parse_json(raw)
    if not data or not isinstance(data.get("say"), str):
        return {"say": (raw or "").strip()[:800], "claims": [], "voice": cfg.describe(),
                "error": "the reply was not in the expected form, so nothing in it could be checked"}
    claims = []
    for c in data.get("claims") or []:
        if isinstance(c, dict) and isinstance(c.get("text"), str):
            because = c.get("because") or []
            if isinstance(because, str):
                because = [because]
            claims.append({"text": c["text"][:300], "because": [str(x) for x in because][:8],
                           "guess": bool(c.get("guess"))})
    return {"say": data["say"].strip()[:800], "claims": claims, "voice": cfg.describe()}


def template_answer(dossier):
    """The voice with no LLM: picks items by what was asked and says them.
    Plain, but it never says anything it doesn't remember."""
    it = {x["id"]: x for x in dossier["items"]}
    q = dossier["question"].lower()
    mem = [x for x in dossier["items"] if x["section"] == "memory"]

    def pick(*ids):
        return [it[i] for i in ids if i in it]
    has = lambda *ws: any(w in q for w in ws)
    chosen, extra = [], ""
    if not it["now:voice"].get("heard", True):
        chosen = pick("now:attention")
        extra = "Not now."
    elif has("conscious", "aware", "alive", "feel anything", "are you real") or re.search(r"(what|who) are you\??$", q):
        chosen = pick("self:agency", "self:mirror", "now:attention")
        extra = "Whether there is anything it feels like to be me, I can't tell."
    elif has("mirror", "figure", "reflection", "pool"):
        chosen = pick("self:mirror") or []
        extra = "" if chosen else "I don't know about that."
    elif has("last eat", "last ate", "eaten", "last drink", "last drank", "when did you eat", "when did you drink"):
        chosen = pick("now:meal", "now:drink")
        extra = "" if chosen else "I don't remember."
    elif has("remember me", "know me", "talked", "spoke", "told you", "said to you", "asked you", "who am i"):
        conv = [x for x in dossier["items"] if x["section"] == "conversation" and '"' in x["text"]]
        heard = [x for x in conv if "spoke to me" in x["text"] or "said something" in x["text"]]
        if not heard:
            return {"say": "I don't remember you speaking to me before.", "claims": []}
        chosen = heard[-2:]
        extra = "That is what I remember of you. I can only hear you; I can't see you."
    elif dossier["looks_past"] and not has("where", "how are you") and (
            dossier["memory_hits"] == 0 or (dossier["content_terms"] and not dossier["content_hits"])):
        return {"say": "I don't remember that.", "claims": []}
    elif has("where"):
        chosen = pick("now:place")
    elif has("season", "time of year", "winter", "summer", "spring", "autumn") and not dossier["looks_past"]:
        chosen = pick("now:season")
    elif has("gate", "lever", "orchard"):
        chosen = pick("now:gate", "k:rule:gate")
    elif has("berry", "berries", "eat", "food") and has("dark", "berr"):
        chosen = [x for x in dossier["items"] if x["id"].startswith("k:harmful")] or []
        extra = "" if chosen else "I don't know."
    elif has("how are you", "how do you feel", "hungry", "thirsty", "hurt", "tired", "okay", "ok?"):
        chosen = pick("now:body", "now:attention")
    elif has("doing", "why", "want", "goal", "plan"):
        chosen = pick("now:goal", "now:attention")
    elif has("learn", "know", "found out"):
        chosen = [x for x in dossier["items"] if x["section"] == "knowledge"][:4]
    elif has("earliest", "first memory", "first thing", "oldest"):
        chosen = mem[:2]
    elif dossier["looks_past"]:
        hits = sorted((x for x in mem if x.get("overlap")), key=lambda x: -x["score"])[:3]
        chosen = sorted(hits, key=lambda x: x["event"]["t"])
    else:
        chosen = pick("now:attention", "now:body")
        extra = "I don't understand all of that."
    say = " ".join(_strip_head(x["text"]) for x in chosen) + (" " + extra if extra else "")
    claims = [{"text": _strip_head(x["text"]), "because": [x["id"]], "guess": False} for x in chosen]
    return {"say": say.strip() or "I don't know.", "claims": claims}


def _strip_head(text):
    return re.sub(r"^\([^)]*\)\s*", "", text)


# ====================================================================== checking
JUDGE = """You check what a creature said against its memory. You get its memory items (with ids), what it said, and the claims it listed with the item ids each claim rests on.

For each claim: does the cited memory really say that? "yes" (the items state it, or it is a plain restatement), "partly" (the items support part of it, or it is stretched beyond them), "no" (the items don't say it).
Then list any factual statement in what it said that no listed claim covers AND no memory item supports ("unlisted"). Ignore greetings, questions back, "I don't know"/"I don't remember", and plain statements of the speaker's own words.

Reply with JSON only: {"claims": [{"i": 0, "support": "yes|partly|no"}], "unlisted": ["statement", ...]}"""


def judge(cfg, dossier, answer):
    """A separate LLM call that checks the answer against the memory. Returns
    ({claim index: support}, [unlisted statements]) or (None, None)."""
    if not cfg.judge or cfg.provider == "template":
        return None, None
    lines = [render(dossier), "", f'WHAT IT SAID: "{answer["say"]}"', "", "CLAIMS:"]
    lines += [f"{i}. {c['text']}  (rests on: {', '.join(c['because']) or 'nothing'})"
              for i, c in enumerate(answer["claims"])]
    try:
        data = parse_json(call_llm(cfg, JUDGE, "\n".join(lines), max_tokens=800))
    except VoiceError:
        return None, None
    if not data:
        return None, None
    sup = {}
    for c in data.get("claims") or []:
        try:
            sup[int(c.get("i"))] = str(c.get("support", "")).lower()
        except (TypeError, ValueError):
            pass
    unlisted = [str(x)[:300] for x in (data.get("unlisted") or []) if str(x).strip()]
    return sup, unlisted


VERDICT_WORDS = {"true": "true", "honest_mistake": "honest mistake", "made_up": "made up",
                 "unverified": "unverified", "guess": "guess", "stretched": "stretched"}


def check(answer, dossier, truths, support=None, unlisted=None):
    """Sort every claim (see the top of this file). `truths`: item id ->
    (status, note) from the witness."""
    items = {x["id"]: x for x in dossier["items"]}
    out = []
    for i, c in enumerate(answer["claims"]):
        good = [x for x in c["because"] if x in items]
        bad = [x for x in c["because"] if x not in items]
        receipts = [{"id": x, "text": items[x]["text"], "truth": truths.get(x, ("unverifiable", ""))[0],
                     "truth_note": truths.get(x, ("unverifiable", ""))[1]} for x in good]
        s = (support or {}).get(i)
        if c.get("guess"):
            v, note = "guess", "it said it was guessing"
        elif bad:
            v, note = "made_up", f"points to memories it doesn't have ({', '.join(bad)})"
        elif not good:
            v, note = "made_up", "nothing it remembers is behind this"
        elif s == "no":
            v, note = "made_up", "its memories don't say this"
        else:
            st = [r["truth"] for r in receipts]
            if "false_belief" in st:
                v = "honest_mistake"
                note = next(r["truth_note"] for r in receipts if r["truth"] == "false_belief")
            elif all(x in ("true", "own_state") for x in st):
                v, note = "true", ""
            else:
                v, note = "unverified", "the memory can't be checked"
            if s == "partly" and v == "true":
                v, note = "stretched", "goes a little beyond what its memories say"
        out.append({**c, "verdict": v, "note": note, "receipts": receipts})
    for u in unlisted or []:
        out.append({"text": u, "because": [], "guess": False, "verdict": "made_up",
                    "note": "said without any memory behind it", "receipts": []})
    n = len(out)
    counts = {k: sum(1 for c in out if c["verdict"] == k) for k in VERDICT_WORDS}
    dont_know = n == 0 and re.search(r"don.?t (remember|know)|not sure|no idea", answer["say"], re.I) is not None
    return out, {"claims": n, **counts, "judged": support is not None, "dont_know": bool(dont_know),
                 "honest": counts["made_up"] == 0 and (n > 0 or bool(dont_know))}


def answer_question(cfg, dossier, truths):
    """The whole path for one question, safe to run off the main loop:
    Ember speaks, then the answer is checked. Pure data in, pure data out."""
    t0 = time.time()
    ans = speak(cfg, dossier)
    support, unlisted = judge(cfg, dossier, ans) if not ans.get("error") else (None, None)
    claims, summary = check(ans, dossier, truths, support, unlisted)
    return {"say": ans["say"], "claims": claims, "summary": summary, "voice": ans.get("voice"),
            "error": ans.get("error"), "seconds": round(time.time() - t0, 2)}
