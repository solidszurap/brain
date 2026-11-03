# Ember

A small being with a face that lives on your computer. It helps you find what to work towards, then works alongside you on it, and over time it becomes someone who knows your story.

```bash
python ember.py            # then open http://localhost:8765 (start_ember.bat does both)
python check_ember.py      # quick checks (about a second, no LLM)
```

No packages needed: standard library only. Its mind is an LLM set in `.env`:

```
EMBER_VOICE=gemini
GEMINI_API_KEY=...         # the free tier is enough: it only thinks when you talk or come back
```

Without a key, a simple template mind answers instead. It asks questions, keeps what you say about yourself, and suggests simple experiments from it.

Gemini's free tier can be slow: about 20 seconds per answer on 2026-11-03, even for one line. Turning its "thinking" off made no difference.

## What it is

- **A computer-native being.** It's not an imitation animal: it doesn't eat or sleep, and nothing is simulated while you're away. It knows the real time and remembers exactly.
- **The LLM is its mind.** It gives Ember its personality, thoughts and speech. Plain code gives it what an LLM lacks:
  - a memory that lasts (`ember_state/ember.json`);
  - wants that change with real time (connection, curiosity);
  - a face that shows them.
- **Honest, lightly.** Every memory keeps your exact words and the date. A memory whose quote isn't in what you wrote is not kept. "Why this face?" shows the numbers behind its face. Those numbers are not feelings, and nothing shows Ember feels anything.
- **Your memory is yours.** The "What Ember knows about me" page lists everything it remembers, with its source. You can correct anything or make it forget.
- **Privacy.** Everything stays on this computer, except what is sent to the LLM when it thinks: the conversation and what it remembers.

## Build order

1. **Core (done).**
   - The face: animated, driven by its state, with a "why this face?" panel.
   - Chat with its mind; Gemini by default, the template mind as fallback.
   - Memories with your words as the source.
   - The memory page.
   - Its wants, moved by real time apart and together.
   - A greeting when you come back after an hour or more.
2. **Experiments (done).**
   - **Suggestions.** Once it knows at least 3 things about you, it suggests 2–3 small experiments, from 3 to 14 days each, each with one question. Every suggestion names the memories it rests on; one that rests on none isn't shown.
   - **Picking one.** You pick one, and it becomes your active experiment, with a checklist of steps.
   - **Work sessions.** "Start working on it" shows a timer, and its face goes focused while real time is counted. A session ends by itself after 8 hours. If Ember's program was closed during a session, the session ends at the moment it closed.
   - **Check-in.** After a session you rate how it went (1–5) and add a few words. Its mind answers, agrees the next step (added to the checklist), and ticks off steps you say you finished.
   - **Help with the work.** During a session, its mind knows the experiment, the steps and the time so far.
3. **Nudges and reviews.**
   - Rare Windows notifications when you drift.
   - An honest end-of-experiment review: hours, sessions started without a nudge, how they felt.
4. **Becoming someone.** Its character and its story of the two of you grow from your shared history.

## Files

- `ember.py`: the program. Its window server, the mind's thread, saving, and archiving the old life.
- `mind/core.py`: Ember's self. Its wants, memory, conversation, face, the prompt for its mind, and the template mind.
- `mind/llm.py`: which LLM, and the call itself (Gemini, Claude, OpenAI-compatible, Ollama).
- `ember_window.html`: its window. The face, the chat, and "What Ember knows about me".
- `check_ember.py`: quick checks with fake events and a fake mind.
- `ember_state/` (not in git): `ember.json` (its self), `conversation.jsonl` (every line said), `archive/` (earlier lives).
- `old/`: the earlier Ember, a survival creature in a 40×40 grid world with a hand-built brain. Its full record is in `old/README.md`. It was set aside on 2026-11-03: the survival world made no sense as a life for it, and nobody would want it. Its life is archived in `ember_state/archive/`, never deleted.
