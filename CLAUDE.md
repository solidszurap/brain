# Ember / brain

**Ember** is a small being with a face that lives on your computer. It helps you find what to work towards, then works alongside you on it, and over time it becomes someone who knows your story. Szilard is its first user; he has no project yet, which is exactly the problem it's for. README.md is the overview.

Owner: Szilard (Hungarian, Budapest/Szeged; prefers direct, concrete, plain answers; gets lost in jargon; runs on Windows). GitHub: solidszurap/brain.

## Run

```bash
python ember.py                       # the real Ember; window at http://localhost:8765 (start_ember.bat)
python ember.py --port 8799 --state <scratch dir>   # a separate Ember for trying things (never test on the real one)
python check_ember.py                 # quick checks, about a second, no LLM; run after every change
```

## Map

- `ember.py`: the window server (`/state?v=1` = presence, `/talk`, `/poke`, `/memory`, `/memory/edit`, `/memory/forget`, `/experiment/suggest|pick|step|end`, `/session/start|stop|checkin`, all POSTs in `POST_PATHS` with a same-origin and `X-Ember` guard), the `Mind` thread (one LLM call at a time), the presence loop, saving (`ember.json` with a `.bak`; `conversation.jsonl` append only), and `archive_old_life`.
- `mind/core.py`, `Ember`:
  - wants: `connection` and `curiosity`, moved by real time in `update`;
  - `mood`;
  - `face()` with its reasons;
  - `prompt()` and `respond()`, the mind's JSON → reply, face, remember/update;
  - memories `{id, kind, note, quote, t, edited}`;
  - `_template` (the mind without an LLM).
- `mind/llm.py`: `LLMConfig` (`.env`: `EMBER_VOICE`, `GEMINI_API_KEY` …), `call_llm`, `parse_json`.
- `ember_window.html`: the canvas face (expressions in `EXPR`), chat, "why this face?", the memory page.
- `old/`: the grid-world Ember (v3 brain, survival, trials, voice checker). For reference only; its README is the full record of that work.

## Rules (decided; keep them)

1. **Never destroy a life.** Never reset or overwrite `ember_state/`. Try changes on a scratch Ember (`--state`). Old lives move to `ember_state/archive/`. Only `ember.py` writes `ember_state/`. A memory is deleted only when the user asks (the Forget button).
2. **Not an imitation animal.** No food, hunger, sleep, seasons, or survival world. No simulated time while away: real time passes and it knows how much.
3. **Honest, lightly.**
   - Memories keep the user's exact words and the date. A memory without a matching quote is dropped.
   - It never claims feelings. Its wants are numbers, and "why this face?" says so.
   - Honesty is a trait, not the whole product: don't build heavy checking pipelines unless asked.
4. **Standard library only.** Secrets only in `.env` (gitignored); never print or log keys.
5. **No long runs.** Verify with `check_ember.py` (fast, fake mind) and by trying it in the browser on a scratch Ember. No multi-minute trials or simulations.
6. **Saved selves must keep loading.** `Ember.from_dict` only copies known fields, so new fields get their defaults; keep it that way.
7. **Commits:** small, straight to main, only when asked; the user pushes. Update README.md in the same change.

## Where things stand (2026-11-03)

- **Slice 1 (core) is built:** the face, chat (Gemini 3.5 Flash-Lite, with the template fallback), memories with quotes, the memory page, wants, and the greeting on return.
- **Slice 2 (experiments) is built:**
  - Suggestions after 3 memories (each must cite real memory ids in `based_on`), then pick one.
  - Steps (the mind can add them with `add_steps` and tick them with `done_steps`).
  - Work sessions (8 h cap; a session open while the program was closed ends at `last_update`, via `resume`).
  - The check-in (1–5 plus words) goes to the mind.
- **Tried on a scratch Ember in the browser:** Gemini suggested 2 fitting experiments; pick, the session timer, stop and the check-in all worked. `check_ember.py`: 54 checks pass.
- **Gemini's free tier is slow** (about 20 s per call, 2026-11-03). Thinking settings don't change it; `thinkingBudget` is rejected (HTTP 400).
- **The real Ember hasn't been started on the new code yet.** Its first start archives the grid-world life automatically.

## Next (in order)

3. **Nudges** (a Windows toast via PowerShell, rare, can be turned off) and **honest end-of-experiment reviews**.
4. **Becoming someone:** its character and story grow from your shared history.
