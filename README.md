# Ember

A small being with a face that helps you get what you want. If you don't know yet what to work towards, it helps you find out (experiments); when you know what you want, it helps you get there (goals). It works alongside you, and over time becomes someone who knows your story. It is a web app: you open it on your phone, log in with Google, and add it to your home screen, where it opens like an app.

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
- **Honest, lightly.** Every memory keeps your exact words and the date. A memory whose quote isn't in what you wrote is not kept. "Why this face?" shows the wants behind its face. Ember is warm and talks naturally; only if you ask it directly whether it really feels things does it tell you honestly what it is.
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
2. **Experiments and goals (done).**
   - **Chats.** One place to talk, like a messaging app: "☰ Chats" at the top opens the list of your chats, latest first, with "+ New chat". A new chat is named after your first words in it. Each chat can be about anything: finding out what you want to work on, talking a goal through to a plan, or working on it. Ember remembers you in all of them, but its mind sees only the open chat's conversation. A dot on "Chats" means Ember said something new in another chat (like asking how a work session went).
   - **Suggestions, in the conversation.** Ask it what you could try. Its ideas appear as cards under its message: small experiments, 3 to 14 days each, each with one question. Before it knows 3 things about you, they're starter experiments for finding out what you enjoy, things you can do on your own, and the card says so. After that, every suggestion names the memories it rests on; one that rests on none isn't shown.
   - **Picking one.** "Pick this" on a card makes it that chat's experiment, and the chat takes its name. It shows as one line above the input (title, day, steps done, Start/Stop); click the title for the steps, Finish and Drop. Each chat can have one goal or experiment, so several can run side by side, each in its own chat. One work session runs at a time; it shows in every chat, and its title opens its chat.
   - **Work sessions.** "Start working on it" shows a timer, and its face goes focused while real time is counted. A session ends by itself after 8 hours.
   - **Check-in, in the conversation.** When you stop a session, Ember asks how it went; you answer under its question with 1–5 and a few words. Its mind answers, agrees the next step (added to the checklist), and ticks off steps you say you finished.
   - **Help with the work.** During a session, its mind knows the experiment, the steps and the time so far.
   - **The end, honestly.** When its days are up, Ember asks once: finish and look back, or 3 more days. When an experiment ends (finished or dropped), Ember looks back on what actually happened: each session's day, length and feeling, and your own words after it. It says what that suggests about the experiment's question, or that there's too little to tell, then asks your own answer. A card under its words shows the numbers. Its mind remembers this look back later.
   - **Goals.** Anything you want in your life: a girlfriend, friends, fitness, a job, a skill. When you tell Ember what you want, it doesn't jump to a plan. It talks it through with you first, one question at a time: what exactly you want and why, where you are now, what you've tried, what's in the way, what you're comfortable doing. Then it says back what it understood and proposes the goal as a card: what having it looks like (so you'll know), how many days (7 to 180), the plan (the way there, built on what you told it), and the first steps, the first one doable today. "Make this my goal" makes it yours. Then you come back and tell it what happened; it helps with the next step and the hard parts, ticks off what you did, adds steps you agree on, and changes the plan with you when it isn't working. When a goal depends on other people, it says plainly that the outcome isn't fully in your hands and makes the steps what is. No manipulation or tricks towards others. Work sessions and check-ins work for goals too. When its days are up it asks whether you got there (finish and look back, or a week more), and its look back asks whether you got what you wanted. A new goal goes in a new chat.
3. **Online (live since 2026-11-03).**
   - A web app with Google login, one Ember per person.
   - Phone layout, installable to the home screen.
   - Retries, and honesty when the mind is down.
   - The daily limit.
   - Privacy, export and delete.
   - The safety rule.
4. **Checking up on you, and a connection (done).**
   - **Check-ups.** When you mention something coming up ("I'm going climbing on Wednesday"), Ember plans when to ask how it went, and then writes to you in that chat by itself, even while you're away (the server looks every few minutes). If it turns out you'd already told it, it says nothing. When a goal's chat has been quiet for 3 days, it checks in once; it never sends another while its last check-up is unanswered. Check-ups aren't free messages. A dot on "Chats" shows them.
   - **Each chat remembered.** Ember keeps a short summary of each chat, so in a long chat it still knows how it started. It keeps each chat to its own topic: it doesn't bring up your other chats unless you do (Szilard's choice).
   - **Your story together.** Its mind knows how long you've known each other and what you've done together, refers back to what you told it, notices progress, and sometimes asks about you. "What it knows" starts with "Our story": together since, chats, what it remembers, goals and experiments, hours of work.
5. **Phone notifications (done).** Ember's check-ups also arrive as phone notifications (Web Push): ⋯ → Turn on notifications (on iPhone, from the home-screen app). Never at night: nothing between 22:00 and 8:00 on your clock (the window tells Ember your time zone); those wait for the morning. Tapping one opens its chat. Turn them off in the same place.
6. **Becoming someone.** Its character and its story of the two of you grow from your shared history.

**Making money:** 5 free messages a day, then Ember Plus at €4.99 a month through Stripe (built; needs a Stripe account and a registered business to take real money). No ads, no selling data.

## Files

- `server/app.py`: the server.
  - One Ember per person, kept in memory and saved to the store.
  - Real time acts lazily on each poll.
  - The mind worker: one thought at a time, retries, the honest "can't think" line, the daily limit.
  - The routes and the pages.
- `server/store.py`: where Embers live. `FileStore` (a folder: local mode and checks) and `SupabaseStore` (Postgres through Supabase's REST API).
- `server/push.py`: phone notifications (Web Push): encrypted for your device (RFC 8291) and signed with Ember's key (VAPID). `tools/make_vapid.py` makes the key once.
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
