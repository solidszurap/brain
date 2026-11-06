# Ember

**Your companion who checks up on you and grows with you.**

A small being with a face that helps you get what you want. If you don't know yet what to work towards, it helps you find out (experiments); when you know what you want, it helps you get there (goals). It works alongside you, and over time becomes someone who knows your story. It is a web app: you open it on your phone, log in with Google, and add it to your home screen, where it opens like an app.

**The goal:** reach as many people as we can, as a business: free with a daily limit, or Ember Plus with no limit. No ads, no selling data.

## Ember online

- **Where it runs:** on a server at Render (Frankfurt). Your Ember (its memories, experiments, the whole conversation) is kept in a Supabase database (Ireland, eu-west-1).
- **Its mind:** Claude Haiku 5.5, through Anthropic's API.
- **Who can use it:** `EMBER_ALLOWED_EMAILS` is an invite list, or `*` for anyone with a Google account (the Google login must be published too; DEPLOY.md step 8). Who has logged in: Supabase → Authentication → Users.
- **Setting it up:** **[DEPLOY.md](DEPLOY.md)**, step by step.
- **What it costs:** Render Starter about $7 a month; Claude Haiku about $0.0003 per reply, measured ($0.10/$0.50 per million tokens in/out), so $5 of credit is roughly 15,000 replies; Supabase free to start (a free project pauses after a week unused, so the server reads it once a day).
- **When the mind is busy or down:** Ember says so honestly and answers once it's back. It never fakes an answer.
- **Connection** (2026-11-06) is how close you've become, and it lasts.
  - **It builds:** a little on each day you talk, with your first few messages, when you share something personal, and with each daily check on a goal. Fast at first, slower later: about 0.5 after 10 days of talking.
  - **It stays:** it holds steady, and only fades slowly after 3 days without talking (about a third in a month).
  - **It shapes how Ember talks:** more familiar as it grows.
  - **Missing you is separate:** it grows while you're away and eases when you're back, which is what moves its face.
  - **Older Embers:** the bond was worked out from your history.
- **Free and Plus.** Everyone gets **10 free messages a day** (`EMBER_FREE_PER_DAY`). A message is anything you send that makes Ember think; its greetings are free.
  - After its answer to your last free one, Ember says so, and the input becomes an **Ember Plus** card: **€4.99 / month**, no daily limit, cancel anytime.
  - Payment goes through **Stripe**: its checkout page to subscribe, its portal ("Manage Ember Plus") to cancel. A signed webhook tells the server, and Ember never sees card details.
  - Deleting your Ember also cancels the subscription.
  - Comped Plus by email: `EMBER_PLUS_EMAILS`, or `*` for everyone (Szilard, 2026-11-06: Plus for everyone for now, while sign-up opens).
- **A safety cap per person** (`EMBER_DAILY_CAP`, 150 replies a day, Plus included) keeps costs in check.
- **Colours:** the menu (⋯) has five colour versions of the window (Ember, Night, Plum, Forest, Day), kept on each device. Ember's own colour is yours to choose (see Levels and looks); it's amber until you change it.
- **Levels and looks** (2026-11-06): Ember grows with you.
  - **XP** comes from progress, talking and time together:
    - a message: 2 (only the first 5 a day count, so chatting forever doesn't pay);
    - a day you talk: 10;
    - each day you've known each other: 2;
    - answering a check-up: 10;
    - a step done: 15;
    - starting a goal or experiment: 20;
    - finishing one: 60 (dropping it after looking back: 20);
    - a work session: 5–20;
    - telling it how a session went: 5.
  - **Levels:** level n takes 25·n·(n−1) XP in all (level 5: 500, level 10: 2,250, level 20: 9,500).
  - **Stages:** Spark (1), Ember (5), Flame (10, a flame on its head), Blaze (20, a crown of three flames and a halo). Each stage is a little bigger and glows wider.
  - **At a new level** it says so once, after its own words, with a burst of sparks and a "Level N!" ribbon, and names what it unlocked.
  - **Customizing:** tap "Lv N · Stage" under its face, or ⋯ → Customize Ember. A sheet opens from the bottom, so you see Ember change above it. There you pick its colour (Amber, Gold, Rose, Ocean, Forest, Violet, Moonlight, Aurora), something to wear (scarf, cap, glasses, flower, headphones, beanie, bow, crown), eyes, cheeks, sparks (stars, hearts, petals, snow) and glow (halo, aura). Each unlocks at a level, and everything is earned by levelling, for everyone. The sheet also lists how it grows and what it earned lately.
  - **Older Embers** got XP for everything done before levels existed, quietly (no level-up lines).
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
  - a mood, from how things go between you and from time apart;
  - a face and a body that show them.
- **Its mood, like a person's.** After each reply its mind says how it feels (glad, proud, warm, excited, playful, calm, thoughtful, worried for you, sad, quiet). The feeling moves two numbers, how things feel between you and its energy, and they ease back over hours. While you're away it gently misses you. Its look follows all of this:
  - colour: a dull amber when it's low, a bright gold when it's glad;
  - size and posture: smaller and lower when it's low;
  - movement: slower breathing and heavier eyelids when its energy is low;
  - a small smile or frown;
  - little rising sparks when it's glad;
  - the window's warm glow.
  When you come back after half a day or more, for a moment it shows it missed you, then lights up and bounces. Its greeting says it warmly, never as a reproach. When it hasn't learned anything new about you for a while, it gets curious: it looks curious and, when the moment fits, asks one question to know you better. The "?" next to its face says why it looks the way it does, with its four meters (mood, energy, connection, curiosity). Once a day it asks about your day, for connection: in the morning what's ahead, in the evening how it was. It follows up on what you tell it, and it doesn't ask in the middle of a hard moment. Its mood colours its words lightly, but it never makes you responsible for how it feels: no guilt for being away, and it never asks you to stay for its sake.
- **Honest, lightly.** Every memory keeps your exact words and the date. A memory whose quote isn't in what you wrote is not kept. "Why this face?" shows the mood and wants behind its face, and what made it feel that way. Ember is warm and talks naturally; only if you ask it directly whether it really feels things does it tell you honestly what it is.
- **Memory is the core promise, for everyone.** Ember remembers everything, forever. The "What it knows" page lists everything it remembers, with its source. You can correct anything or make it forget.
- **It keeps things moving.** Each chat is about something, and Ember keeps it heading there. After two or three questions it says what it understood and proposes something: a plan, a next step, an experiment. If it has asked three questions in a row with nothing moving, it's told to propose instead of asking again.
- **It reads the room.** When you share something hard, it doesn't smile at you. It says what it heard, stays with it, and asks whether you want to work through it or just needed to say it. Its face shows worry or sadness, never a grin on top of bad news.
- **It knows who it is.** Asked who it is, what it's for or how it works, Ember explains in its own words: what it is, why it exists, how it helps, what it remembers, how the app works, what it isn't, and (only if asked) which AI its mind runs on.
- **Not a therapist.** If someone talks about harming themselves, Ember points to real help (in Hungary 116-123, or 112).

## Build order

1. **Core (done).**
   - The face: animated, driven by its state, with a "why this face?" panel.
   - Chat with its mind.
   - Memories with your words as the source.
   - The memory page.
   - Its wants, moved by real time apart and together.
   - When you come back after an hour or more, its face lights up. It writes to you first only the first time you open it, or after 8 hours or more away, and never on top of its own unanswered words (a check-up or a greeting).
2. **Experiments and goals (done).**
   - **Chats.** One place to talk, like a messaging app: "☰ Chats" at the top opens the list of your chats, latest first, with "+ New chat". A new chat is named after your first words in it; the open chat's name is in the middle of the top bar, and tapping it (or ✎ in the list) renames it. Each chat can be about anything: finding out what you want to work on, talking a goal through to a plan, or working on it. Ember remembers you in all of them, but its mind sees only the open chat's conversation. A dot on "Chats" means Ember said something new in another chat (like asking how a work session went).
   - **Suggestions, in the conversation.** Ask it what you could try. Its ideas appear as cards under its message: small experiments, 3 to 14 days each, each with one question. Before it knows 3 things about you, they're starter experiments for finding out what you enjoy, things you can do on your own, and the card says so. After that, every suggestion names the memories it rests on; one that rests on none isn't shown.
   - **Picking one.** "Pick this" on a card makes it that chat's experiment, and the chat takes its name. It shows as one line above the input (title, day, steps done, Start/Stop); click the title for the steps, Finish and Drop. Each chat can have one goal or experiment, so several can run side by side, each in its own chat. One work session runs at a time; it shows in every chat, and its title opens its chat.
   - **Goals of their own** (2026-11-06). "◎ Goals" at the top lists your goals and experiments, with "+ New goal".
     - **A new goal:** make it yourself (what you want, how you'll know, how long: any number of hours, days, weeks or months, from an hour to a year; your first steps) and it starts right away. A goal you gave in hours counts the hours left, and keeping going adds an hour (a goal of days, weeks or months gets a week). Or "Plan it with Ember": a new chat where Ember asks the few things it needs and proposes the plan.
     - **Each goal has its own page:** what you want and how you'll know; today's step with **Did it / Partly / Not today** (plus a few words); your streak and the last two weeks as dots; this phase's steps, which you can tick or add to; all the phases with their look backs; the plan; and the buttons Plan details with Ember, Talk about it, More days, Finish and look back, and Drop it.
     - **The daily check replaces the old stopwatch.** Ember answers the first check of the day in the goal's chat, shown on the page too: glad when you did it, and a smaller next step when it was partly or not today, without guilt. Being honest earns XP too.
     - **Phases:** a goal longer than two weeks goes in phases of 1–2 weeks, and you only see the current one. When a phase is over, Ember says so. With "Look back and plan the next phase" (or early, "On to the next phase") it looks back on how it went and plans the next phase's steps from that. Goals Ember proposes come with phases. Older goals were split into phases by week.
     - In a chat, the line above the input shows the goal's name, its phase and today's step, with "Check today". Tapping it opens the goal's page.
     - Old work sessions still count in the look backs, but nothing starts new ones.
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
   - **Check-ups.** When you mention something coming up ("I'm going climbing on Wednesday"), Ember plans when to ask how it went, and then writes to you in that chat by itself, even while you're away (the server looks every few minutes). If it turns out you'd already told it, it says nothing. When a goal's chat has been quiet for 3 days, it checks in once; it never sends another while its last check-up is unanswered.
     - **You choose** (⋯ → Check-ups): Off, When it matters (just the above), or Regularly (the default).
     - **When:** at the exact time you pick, any time of day (your time; 18:00 by default), on the days you pick (M T W T F S S; all by default). Because you chose that time, it comes even late at night; the other check-ups never come at night.
     - **How often** is set by the days you pick: a regular check-up comes on each of your days, at your time, if you haven't talked that day. It goes to your latest chat with a goal or experiment.
     - Off also drops the ones it planned.
     - Check-ups aren't free messages.
     - **Its name.** It's Ember until you give it a name of your own (⋯ → Its name, up to 24 letters; empty means Ember again). Its mind uses the name, and notifications read "<name> sent you a message" with its words underneath. The home-screen icon stays "Ember". A dot on "Chats" shows them.
   - **Each chat remembered.** Ember keeps a short summary of each chat, so in a long chat it still knows how it started. It keeps each chat to its own topic: it doesn't bring up your other chats unless you do (Szilard's choice).
   - **Your story together.** Its mind knows how long you've known each other and what you've done together, refers back to what you told it, notices progress, and sometimes asks about you. "What it knows" starts with "Our story": together since, chats, what it remembers, goals and experiments, hours of work.
5. **Phone notifications (done).** Ember's check-ups also arrive as phone notifications (Web Push): ⋯ → Turn on notifications (on iPhone, from the home-screen app). Never at night: nothing between 22:00 and 8:00 on your clock (the window tells Ember your time zone); those wait for the morning. Tapping one opens its chat. Turn them off in the same place. When you open Ember and they're not on yet, a small card asks once ("Turn on" / "Not now"; Not now asks again after a week): iPhone only allows the question after a tap.
6. **Becoming someone.** Its character and its story of the two of you grow from your shared history.

**Making money:** 10 free messages a day, then Ember Plus at €4.99 a month through Stripe (built; needs a Stripe account and a registered business to take real money). No ads, no selling data.

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
