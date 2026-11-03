# Ember

A small being with a face that helps you find what to work towards, then works alongside you on it, and over time becomes someone who knows your story. It is a web app: you open it on your phone, log in with Google, and add it to your home screen, where it opens like an app.

## Ember online

- **Where it runs:** on a server at Render (Frankfurt). Your Ember (its memories, experiments, the whole conversation) is kept in a Supabase database (Ireland, eu-west-1).
- **Its mind:** Claude Haiku 5.5, through Anthropic's API.
- **Who can use it:** it's invite-only while being tested (`EMBER_ALLOWED_EMAILS`).
- **Setting it up:** **[DEPLOY.md](DEPLOY.md)**, step by step.
- **What it costs:** Render Starter about $7 a month; Claude Haiku about $0.0003 per reply, measured ($0.10/$0.50 per million tokens in/out), so $5 of credit is roughly 15,000 replies; Supabase free to start (a free project pauses after a week unused, so the server reads it once a day).
- **When the mind is busy or down:** Ember says so honestly and answers once it's back. It never fakes an answer.
- **Free and Plus.** Everyone gets **5 free messages a day** (`EMBER_FREE_PER_DAY`). A message is anything you send that makes Ember think; its greetings are free.
  - After its answer to your last free one, Ember says so, and the input becomes an **Ember Plus** card: **€4.99 / month**, no daily limit, cancel anytime.
  - Payment goes through **Stripe**: its checkout page to subscribe, its portal ("Manage Ember Plus") to cancel. A signed webhook tells the server, and Ember never sees card details.
  - Deleting your Ember also cancels the subscription.
  - Comped Plus by email: `EMBER_PLUS_EMAILS`.
- **A safety cap per person** (`EMBER_DAILY_CAP`, 150 replies a day, Plus included) keeps costs in check.
- **Colours:** the menu (⋯) has five colour versions (Ember, Night, Plum, Forest, Day), kept on each device. Ember itself stays orange in all of them.
- **Your data:** the menu (⋯) has Privacy ([web/privacy.html](web/privacy.html)), "Download my data" (everything, as JSON), and "Delete my Ember", which deletes everything and the account, for good. Logs hold ids and errors only, never what anyone said.

## Run it on your own computer

```bash
pip install -r requirements.txt
python ember.py            # local mode: one Ember, yours, in ember_state/, no login; http://localhost:8765
python check_ember.py      # Ember's self: quick checks, about a second, no LLM
python check_server.py     # the server: quick checks with a fake mind, fake logins and a fake Supabase
```

Local mode reads its mind from `.env` (`EMBER_VOICE=anthropic` and `ANTHROPIC_API_KEY=...`, or Gemini). Without a key, a simple template mind answers. It asks questions and keeps what you say about yourself.

## What it is

- **A computer-native being.** It's not an imitation animal: it doesn't eat or sleep, and nothing is simulated while you're away. It knows the real time and remembers exactly.
- **The LLM is its mind.** It gives Ember its personality, thoughts and speech. Plain code gives it what an LLM lacks:
  - a memory that lasts;
  - wants that change with real time (connection, curiosity);
  - a face that shows them.
- **Honest, lightly.** Every memory keeps your exact words and the date. A memory whose quote isn't in what you wrote is not kept. "Why this face?" shows the numbers behind its face. Those numbers are not feelings, and nothing shows Ember feels anything.
- **Memory is the core promise, for everyone.** Ember remembers everything, forever. The "What it knows" page lists everything it remembers, with its source. You can correct anything or make it forget.
- **Not a therapist.** If someone talks about harming themselves, Ember points to real help (in Hungary 116-123, or 112).

## Build order

1. **Core (done).**
   - The face: animated, driven by its state, with a "why this face?" panel.
   - Chat with its mind.
   - Memories with your words as the source.
   - The memory page.
   - Its wants, moved by real time apart and together.
   - A greeting when you come back after an hour or more.
2. **Experiments (done).**
   - **Chat | Experiment.** A switch at the top, there from the start. Chat is just the conversation. Experiment shows the experiment line above the input and tells Ember's mind you want to work on it (or find one).
   - **Suggestions, in the conversation.** Ask it what you could try; in Experiment mode the input says so. Its ideas appear as cards under its message: small experiments, 3 to 14 days each, each with one question. Before it knows 3 things about you, they're starter experiments for finding out what you enjoy, things you can do on your own, and the card says so. After that, every suggestion names the memories it rests on; one that rests on none isn't shown.
   - **Picking one.** "Pick this" on a card makes it your active experiment and switches to Experiment mode. It shows as one line above the input (title, day, steps done, Start/Stop); click the title for the steps, Finish and Drop. A running work session shows in Chat mode too.
   - **Work sessions.** "Start working on it" shows a timer, and its face goes focused while real time is counted. A session ends by itself after 8 hours.
   - **Check-in, in the conversation.** When you stop a session, Ember asks how it went; you answer under its question with 1–5 and a few words. Its mind answers, agrees the next step (added to the checklist), and ticks off steps you say you finished.
   - **Help with the work.** During a session, its mind knows the experiment, the steps and the time so far.
   - **The end, honestly.** When its days are up, Ember asks once: finish and look back, or 3 more days. When an experiment ends (finished or dropped), Ember looks back on what actually happened: each session's day, length and feeling, and your own words after it. It says what that suggests about the experiment's question, or that there's too little to tell, then asks your own answer. A card under its words shows the numbers. Its mind remembers this look back later.
3. **Online (live since 2026-11-03).**
   - A web app with Google login, one Ember per person.
   - Phone layout, installable to the home screen.
   - Retries, and honesty when the mind is down.
   - The daily limit.
   - Privacy, export and delete.
   - The safety rule.
4. **Nudges.** Phone notifications when you drift (Web Push), rare, and they can be turned off.
5. **Becoming someone.** Its character and its story of the two of you grow from your shared history.

**Making money:** 5 free messages a day, then Ember Plus at €4.99 a month through Stripe (built; needs a Stripe account and a registered business to take real money). No ads, no selling data.

## Files

- `server/app.py`: the server.
  - One Ember per person, kept in memory and saved to the store.
  - Real time acts lazily on each poll.
  - The mind worker: one thought at a time, retries, the honest "can't think" line, the daily limit.
  - The routes and the pages.
- `server/store.py`: where Embers live. `FileStore` (a folder: local mode and checks) and `SupabaseStore` (Postgres through Supabase's REST API).
- `server/billing.py`: Ember Plus through Stripe. Checkout, the customer portal, cancel, webhook signature check (HMAC), and the plan from each event.
- `server/auth.py`: who's asking. Supabase login tokens (cached), the invite list, local mode.
- `server/__main__.py`: `python -m server` (online, on Render), and `run_local` for `ember.py`.
- `server/schema.sql`: the tables (`embers`, `lines`, `usage`, `plans`), with row level security on.
- `render.yaml`: the Render setup.
- `mind/core.py`: Ember's self. Its wants, memory, conversation, experiments, sessions, face, the prompt for its mind, and the template mind. Standard library only.
- `mind/llm.py`: which LLM, and the call itself. Claude goes through the `anthropic` SDK at low effort; Gemini, OpenAI-compatible and Ollama go through urllib.
- `web/index.html`: its window.
  - The Google login.
  - The face on top, the conversation under it (with experiment cards and the check-in inside it), the experiment line above the input.
  - "What it knows" and the menu.
- `web/privacy.html`, `web/manifest.webmanifest`, `web/sw.js`, `web/icons/` (drawn by `tools/make_icons.py`).
- `tools/import_local.py`: moves a local Ember into an online account.
- `ember.py`: local mode, plus archiving the grid-world life.
- `check_ember.py`, `check_server.py`: the quick checks.
- `ember_state/` (not in git): your local Ember (`ember.json`, `conversation.jsonl`, `usage.json`, `archive/`).
- The earlier Ember, a survival creature in a 40×40 grid world with a hand-built brain, is no longer in the repo. It lives on in git as the tag **`grid-ember-final`** (its full record is in that version's README). It was set aside on 2026-11-03: the survival world made no sense as a life for it, and nobody would want it. Its life is archived in `ember_state/archive/`, never deleted.
