# Ember / brain

**Ember** ("Your companion who grows with you.", Szilard's tagline, 2026-11-06: on the login screen, the manifest and the meta description) is a small being with a face, now a web app (phone-first, Google login, one Ember per person). It helps you get what you want: if you don't know yet what to work towards, it helps you find out (experiments); when you know what you want, it helps you get there (goals). It works alongside you, and over time it becomes someone who knows your story. Szilard is its first user; he has no project yet, which is exactly the problem it's for. A possible business later: a free plan with a daily limit plus Ember Plus via Stripe; no ads, no selling data. README.md is the overview; DEPLOY.md is how it goes online.

Owner: Szilard (Hungarian, Budapest/Szeged; prefers direct, concrete, plain answers; gets lost in jargon; runs on Windows; not technical about hosting, so he relies on us for that). GitHub: solidszurap/brain.

## Run

```bash
pip install -r requirements.txt       # fastapi, uvicorn, anthropic, cryptography
python ember.py                       # local mode: your Ember in ember_state/, no login; http://localhost:8765
python ember.py --port 8799 --state <scratch dir>   # a separate Ember for trying things (never test on the real one)
python check_ember.py                 # Ember's self: about a second, no LLM
python check_server.py                # the server: a few seconds; fake mind, fake logins, fake Supabase
python -m server                      # online mode (Render); needs the env vars in render.yaml
```

## Map

- `server/app.py`, `create_app(store, auth, cfg, call, clock, ...)`:
  - `Users` caches one `Ember` per person and saves lines first, then the self.
  - `/state?v=1` is presence: it calls `arrive`/`update` lazily, since there is no global loop.
  - `MindWorker` is one queue and one thread.
    - Retries: the SDK's own, plus one more after `retry_delay`.
    - If the mind still fails: the `UNREACHABLE` line once, then a retry every `retry_every`.
    - A non-retryable error gives the `FAILED` line.
    - The daily cap gives the `CAPPED` line.
    - After a restart, unanswered last lines are re-queued.
  - The POST guard: `X-Ember` header and same host. `/stripe/webhook` is exempt: it checks Stripe's signature instead. Plus `/me/export` and `/me/delete`; delete cancels an active subscription first.
  - Ember Plus:
    - `is_plus`: local mode, `EMBER_PLUS_EMAILS`, or the plan status in `PLUS_STATUSES`.
    - `spend_free`: `free_per_day` counted messages (talk, suggest, checkin), then 402.
    - `after_reply`: the `LAST_FREE` line, marked `paywall`.
    - `/plus/checkout`, `/plus/portal`, `/stripe/webhook`.
    - `/state` returns `plan`.
- `server/store.py`: `FileStore` (a folder; `fixed=` for local mode; delete = archive) and `SupabaseStore` (PostgREST via urllib with the service key; delete = rows plus the auth user).
- `server/push.py`: `Push(VAPID_PRIVATE_KEY)`: `encrypt` (RFC 8291 aes128gcm), `_vapid` (ES256 JWT), `send` (urllib; `PushGone` on 404/410). The app: `/config` gives `vapid_public`; `/push/subscribe`, `/push/unsubscribe` keep `Ember.devices`; `after_reply` sends a `followup` reply to every device in a thread (`notify`), forgetting gone ones. `/state?tz=` sets `Ember.tz` (minutes from UTC): the prompt's "Now" is their local time, and `due_checkups` waits outside 8:00-22:00 (`QUIET_UNTIL`/`QUIET_FROM`). The window: ⋯ → Turn on notifications (`toggleNotify`; iPhone needs the home-screen app), and the `#notifyAsk` card when you open Ember (`askNotify`: only while permission is still "default"; "Not now" = localStorage `ember.notifyAskAfter`, a week); if permission was granted before, it subscribes again quietly unless you turned them off (`ember.notifyOff`); `sw.js` shows them and a tap opens `/?chat=`. Key: `tools/make_vapid.py` → `.env`, then Render.
- `server/billing.py`: `Billing`.
  - `live` (an `sk_live_` key) and `terms_url` (`EMBER_TERMS_URL`) combine into `selling`: a live key sells nothing until the terms URL is set (Szilard, 2026-11-06, before taking real money). `/plus/checkout` then returns 503, and `plan.payments` is false.
  - With `terms_url`, checkout sends `consent_collection[terms_of_service]=required`. `/config` gives `terms_url` for the ⋯ menu's "Terms (ÁSZF)" and the paywall line.
  - Going live is DEPLOY.md 6.8.
  - Plus is just "no daily limit", at €4.99 a month. Progress (daily checks, phase look backs, reviews, check-ups, greetings) never counts as a message.
- `server/billing.py`: `Billing` (Stripe via urllib: `checkout`, `portal`, `cancel`, `verify` with a 5-minute tolerance, `plan_from_event`). The stores have `get_plan`/`set_plan` and `add_message`/`messages_today`.
- `server/auth.py`: `SupabaseAuth` (`/auth/v1/user`, 5-minute cache, `EMBER_ALLOWED_EMAILS` or `*`) and `LocalAuth`.
- `server/__main__.py`: `run_online` (env, refuses to start without a usable mind; starts `keep_awake`, one Supabase read a day) and `run_local` (used by `ember.py`).
- `mind/core.py`, `Ember`:
  - each chat's `summary` (from the mind's `summary`; "Earlier in this chat" once it's longer than `CONTEXT_LINES`); other chats are never brought into a chat (Szilard, 2026-11-04);
  - `story()`: since, chats, memories, goals, experiments, work; in the prompt (`_story`) and on the memory page ("Our story");
  - wants: `missing` (missing you: grows while you're away, eases in minutes when you're here; this was `connection` until 2026-11-06) and `curiosity`, moved by real time in `update`;
  - `connection` is the bond (Szilard, 2026-11-06: "permanent, only dropping if not talked in a long time").
    - `closer(k)` raises it: `BOND_DAY` on the first message of a day, `BOND_TALK` for the first `TALK_XP_PER_DAY` messages, `BOND_SHARE` when it learns something, and `BOND_CHECK` on a daily check.
    - `update` fades it only after `BOND_KEEP` (3 days) since `last_you_t`, at `BOND_FADE` (30 days).
    - Old saves: `from_dict` moves the old `connection` into `missing` and runs `_backfill_bond()` from the talk and memories.
    - The prompt says how close you are; the "?" meter "connection" is the bond.
  - its feeling (2026-11-05):
    - The mind's `feel` (one of `FEELS`) and `feel_why` go through `feeling()`, which nudges `valence` (-1..1) and `energy` (0..1).
    - Both ease back to `VALENCE_REST`/`ENERGY_REST` in `update`: valence over about 8 hours, energy over about 3.
    - The template mind leaves them alone.
  - `mood = 0.5 + 0.3*valence - 0.35*connection + 0.4*bump`;
  - `face()` with its reasons. Precedence: missing you (`droopy`), then a feeling from the last `FEEL_SHOWS` (its face from `FEELS`), then curious, then happy. It also returns `energy`.
  - The window (`draw()`) turns mood and energy into the look: body colour and size, posture, breathing, eyelids and blinking, a baseline smile, sparks when glad, and `--moodglow` on `body::before`.
  - Mood colours its words lightly and is never used to guilt-trip (`SYSTEM`).
  - Missing you and curiosity, made visible (2026-11-06; Szilard couldn't see them work).
    - `arrive` keeps `missed` (the connection as you come back).
    - `face()` shows a moment of having missed you (`droopy`, under 2.5 s, when `missed` > .45), then `surprised`/`eager` for `ARRIVAL_SHOWS`. This comes before `thinking`, so the greeting doesn't hide it.
    - It is never `droopy` for missing you while you're here.
    - The prompt says "You missed them" warmly at an arrive with `missed` > .45, and asks one get-to-know-you question when `curiosity` > .65 (not after 2 questions in a row).
    - `face().why` is one plain sentence. The "?" panel (`renderWhy`) shows it above the four meters with their numbers (mood, energy, connection, curiosity); Szilard wanted the numbers back (2026-11-06).
    - It asks about your day once a day, for connection (Szilard, 2026-11-06):
      - The prompt tells the mind (talk, arrive, a regular check-up) while `day_asked` isn't today: morning, what's ahead; afternoon, how it's going; evening, how it was.
      - The mind sets `asked_about_day` when it does, which sets `day_asked`. The template mind doesn't count.
      - On those days it comes before the curiosity question (one question at a time).
  - Focus and empathy (2026-11-06, Szilard: "talking and talking but no progress"; "always smiling when I share hard things").
    - `SYSTEM` says:
      - keep each chat moving towards what it's for;
      - after 2-3 questions, propose something;
      - a goal talk-through uses 2-4 questions, never more than 5;
      - read how they feel first: hard things get no upbeat tone, no silver linings, and a calm/worried/sad face;
      - never stall or back off on its own: no "pick this up another time" unless they ask, and every reply ends with a way forward. Feelings shared about a goal being planned (longing, hope) are part of the work: acknowledge them and move the plan on. (Szilard's 2026-11-05 chat: Ember backed off after he described the warmth he's looking for.)
    - The prompt says what the chat is for: its goal, or its first words.
    - When `asked_in_a_row(chat)` reaches `DRIFT_QUESTIONS` (3; replies with "?" since the last `progress`/`exps`/`review`/`timeup` line), the prompt tells it to propose instead of asking.
    - `respond` marks `progress` when steps or a plan changed.
    - It replaces a cheerful face with the feeling's face after `HEAVY_FEELS`.
  - An answer from the mind that isn't readable JSON is asked once more (`_think`); if it fails again, the `FAILED` line is said. The template never answers online in its place (2026-11-06).
  - `prompt()` and `respond()`, the mind's JSON → reply, face, remember/update/add_steps/done_steps/experiments;
  - memories `{id, kind, note, quote, t, edited}`;
  - experiments and goals (one list, `experiments`; a goal has `kind: "goal"` and its `question` is what having it looks like; `kind_of`), sessions and the check-in. `SYSTEM` tells the mind to talk a goal through first (what, why, where you are, what you tried, what's in the way, what you're comfortable with; usually 3-6 questions), then propose it in `goal` with a `plan` (`_take_goal`: 7-180 days, up to 8 steps; the title is what you want, not the way there). While a goal is active, `replan` changes its plan when you agree. Goals that depend on other people: honest that the outcome isn't fully in your hands; no manipulation. One goal or experiment is active at a time; a goal gets 7 more days (`MORE_DAYS`), and its time-up line and look back ask whether you got there;
  - `say()`;
  - `_template` (the mind without an LLM);
  - the safety rule in `SYSTEM`.
- `mind/llm.py`: `LLMConfig` (`EMBER_VOICE`; Claude first in auto), `call_llm`, `LLMError(retryable)`, and `_call_claude` (`anthropic` SDK, `claude-haiku-5-5`, effort low, records `cfg.last_usage`).
- `web/index.html`:
  - Boot reads `/config`. Online, it loads supabase-js (pinned 2.118.0 from jsdelivr; supports Supabase's new publishable keys) for Google login. `api()` adds the bearer token; a 401 shows the login cover and a 403 shows "not invited".
  - Chats (2026-11-04; Szilard dropped the Chat | Work switch for this): `Ember.chats` `{id, title, created}`, starting with `c1` "Our first chat"; a line or an experiment has `chat` (none: `c1`, so older selves load as one chat; `chat_of`). `new_chat` reuses an empty "New chat"; `hear` names a new chat after your first words; `pick` renames the chat after its goal. Each chat has at most one active goal or experiment (`active(chat)`; no chat given = `latest_chat()`), so several run side by side; one work session at a time overall. `event_chat(event)` decides where Ember answers and which lines its mind sees (a look back goes to its goal's chat; the check-in to the session's goal's chat); the prompt names the chat and lists goals in the other chats. Each chat keeps its own `TALK_KEPT` lines. Server: `/state?chat=` (snapshot of that chat: `chat`, `chats` from `chat_list()`, its `talk` and `experiment`; plus `thinking_in`), `/talk {text, chat}`, `/chat/new`, `/session/start {chat}`, `/experiment/extend {id}`. The window: "☰ Chats" opens `#chatsDrawer` (list + "+ New chat", ✎ per chat), the open chat in localStorage `ember.chat`, its name in the middle of the top bar (tap to rename in place: `startRename`, `/chat/rename`, `rename_chat`; on phones "What it knows" moves into the ⋯ menu to give it room), a dot when another chat has something new (`seenAt`, localStorage `ember.seen`). `#sessionbar` shows the open chat's goal, or the running session from any chat. Ideas are there from the start: before `knows_enough()` (3 memories) they are `starter` experiments (`STARTERS` for the template mind) that need no memory; after it, each must cite memories.
  - The canvas face (`EXPR`) sits above the conversation. `#chat` fades at its edges instead of cutting messages (2026-11-06): a CSS mask with `--ft`/`--fb`, switched on by `chatEdges()` when scrolled down or with more below. Experiment cards render under an Ember line's `exps`; the check-in renders under the last `checkin` line while `checkin_due`. The experiment line is `#sessionbar`, with its pop-up `#expcard`.
  - The look: solid surfaces with a thin edge (`--surface`, `--raised`, `--overlay`, `--edge`), soft shadows (`--lift`), a warm glow behind (`--glow1-3`) and flat orange buttons (`--btn`). No glass: no backdrop blur, gloss or lit edges (Szilard, 2026-11-03). The body is `position: fixed; inset: 0`, so the page is exactly the screen. iOS 26 paints the strip behind the clock from a pinned element at the very top if it has one plain colour, and blurs the page there if not: so `.top` is `position: fixed` from `top: 0`, plain `--bg`, `env(safe-area-inset-top)` + `--topbar` tall, and the body is padded by the same. The body's background is plain too and the glow is `body::before`. Never give these a gradient or blur. (Sources: hawkshift.com/research/ios-26-safari-status-bar; WebKit bug 301994.) Colour versions (Ember, Night, Plum, Forest, Day) are `[data-theme]` token overrides, picked in the menu and kept in localStorage `ember.theme`; the buttons stay orange in all of them, and Ember is amber unless you choose another colour (Levels and looks). The model's name is never shown.
  - **Goals of their own** (2026-11-06, Szilard: a goal option that's always there, each goal its own window, no stopwatch for multi-day goals, long goals too much).
    - `core.py`, goal data:
      - A goal has `phases` `[{title, days, start, end, steps, look_back, up}]` and `phase`; `x["steps"]` is the current phase's steps.
      - `PHASE_MAX` is 14. `ensure_phases` splits by week (old goals in `from_dict`, your own goals, and proposals without phases); `_time_phases` times them; `next_phase` keeps the steps and look back, starts the next one now, and gives `XP["phase"]`.
    - `core.py`, the daily check:
      - `log` `[{day, t, how, step, words}]` holds `CHECKS` (done/partly/skip), one per day.
      - `daily_check` ticks today's step on done, gives XP once a day, says your `daily` line, and returns the `daily` event; `first` means Ember answers only the first check of the day.
      - `today_step`, `streak` (a skip today ends it), `add_step`.
    - `core.py`, starting goals: `new_goal` (its own chat, active at once), `plan_with_ember` (a new chat with a `talk`), `goal_view`/`goals`; `snapshot.goals_due`.
    - `core.py`, phase ends and the mind:
      - `update` says a `phase_up` line once at a phase's end.
      - The `phase` event (`from` guards against doubles) gets the phase's facts; `respond` makes its reply the look back and `add_steps` the next phase's steps (`phase_new` line).
      - The mind's `goal` carries `phases` (`_take_goal`: 5-14 days each).
      - `facts` counts checks and phases.
    - Server: `GET /goals`, `/goal/new {title, done_when, days, steps, with_ember}`, `/goal/check`, `/goal/phase` (`phase_pending`, 2 minutes), `/goal/step`.
    - Window: "◎ Goals" (`#goalsDrawer`, `#goalsDot`), and `#goalPage` (`openGoal`, `renderGoalPage`, `renderNewGoal`, `waitGoalReply` shows Ember's answer to a check). `#sessionbar` is the goal bar; picked cards and `phase_up`/`phase_new` lines have Open goal / Look back and plan.
    - Work sessions stay in the code for old data, but nothing starts them.
  - **Levels and looks** (2026-11-06, Szilard: "your companion who grows with you"; XP from progress, talking and days together; all earned by levelling, nothing tied to Plus).
    - `core.py`:
      - `XP` (the table, one place), `TALK_XP_PER_DAY` (5), `xp_for`/`level_of` (25·n·(n−1)), `STAGES` (Spark 1, Ember 5, Flame 10, Blaze 20), and `LOOKS` (part → `[(id, label, level)]`, the first is the free default; `DEFAULT_LOOK`).
      - `Ember.xp`, `xp_log` (the last 40), `xp_today`, `days_counted`, `levelup_due`, `look`.
      - `gain()` is called from `hear` (`_talk_xp`, answering a `checkup`), `respond`/`set_step` (`_step_xp`, once per step via `step["xp"]`), `pick`, `end_experiment`, `stop_session` (5 min or more), `checkin` and `update` (days together).
      - A new level sets `levelup_due`; `_announce_levelup` says one `levelup` line in the latest chat. It is called from `update`, and at the end of `respond`, never between your line and its answer.
      - `from_dict` without `xp` runs `_backfill_xp`, which counts the history quietly.
      - `set_look` accepts only unlocked items; `looks()` is the catalog for `/looks`; `/look {part, value}`.
      - `snapshot` has `level` and `look`; the prompt has one level line.
    - Window:
      - `draw()` uses `BODY`/`bodyHues` (colours; aurora shifts), `STAGE` (size, glow, room above), `flame()`, `wear()`, the `look.eyes`/`look.cheeks` variants, `particle()` (sparks, stars, hearts, petals, snow) and the glow styles (halo, aura).
      - A level rise in `S.level` gives `burst()` and a "Level N!" ribbon.
      - `#lvBadge` under the face, and the `#lookSheet` bottom sheet (`openLooks`, `renderLooks`, `SWATCH`; Ember above it is the live preview).
  - The menu (⋯): install guide, privacy, export, colour, log out, delete. Confirmations are a second click (`sure`), because `confirm()` is blocked in the app's browser.
- `web/privacy.html`, `manifest.webmanifest`, `sw.js` (no caching; an offline note), `icons/` (`tools/make_icons.py`).
- The grid-world Ember (v3 brain, survival, trials, voice checker) was removed from the repo on 2026-11-03; it's the git tag `grid-ember-final` (`git show grid-ember-final:README.md` is its full record). Local leftovers: `trials/` (an 85 MB cache, safe to delete) and `ember_state/archive/` (its life; keep).

## Rules (decided; keep them)

1. **Never destroy a life.**
   - Never reset or overwrite `ember_state/`, and never touch live data to try things.
   - Use a scratch Ember (`--state`) or the checks.
   - Old lives move to `ember_state/archive/`.
   - Online deletion happens only through the user's own "Delete my Ember". Memories are deleted only by Forget.
2. **Memory is perfect for everyone, forever.** It's the core promise and never a paid feature. Keep costs flat by what goes into the prompt, never by forgetting.
3. **Not an imitation animal.** No food, hunger, sleep, seasons, or survival world. No simulated time while away: real time passes and it knows how much.
4. **Honest, lightly.**
   - Memories keep the user's exact words and the date. A memory without a matching quote is dropped.
   - Feelings (Szilard, 2026-11-04): Ember is warm and talks naturally ("I'm glad you went", "I missed hearing from you"), and the app doesn't point out what it lacks. Only if you ask it directly whether it really feels things does it answer honestly: software, wants that are real numbers, and it doesn't know whether that is feeling. It never lies about what it is. Its mood shows on its face and in its words (2026-11-05), but it never makes you responsible for it: no guilt for being away, and it never asks you to stay for its sake.
   - When its mind can't answer, it says so; no fake answers online.
   - Honesty is a trait, not the whole product: no heavy checking pipelines unless asked.
5. **Dependencies:**
   - `mind/core.py` uses the standard library only.
   - The server uses FastAPI, uvicorn, `anthropic` and `cryptography` only (`cryptography` for phone notifications: Szilard's choice, 2026-11-04, over hand-written crypto).
   - Secrets only in `.env` (local) or Render's environment (online). Never print or log keys, or anything users say: logs hold ids and errors only.
6. **Invite-only** (`EMBER_ALLOWED_EMAILS`) until Szilard decides otherwise.
7. **Free and Plus:** 10 free messages a day (Szilard, 2026-11-06; was 5; progress like daily checks, check-ups and look backs never counts), then Ember Plus at €4.99 a month (Stripe). Never sell data and never show ads. Taking real money needs his registered business and terms of service (ÁSZF); we don't write legal text.
8. **No long runs.** Verify with `check_ember.py`, `check_server.py`, and by trying it in the browser (phone size 375 px and desktop) on a scratch Ember.
9. **Saved selves must keep loading.** `Ember.from_dict` only copies known fields, so new fields get their defaults; keep it that way.
10. **Commits:** small, straight to main, only when Szilard asks (don't ask him whether to commit). He pushes. Update README.md in the same change.

## Where things stand (2026-11-03)

- **LIVE: https://ember-dztb.onrender.com** (Render service `ember`, Frankfurt, Starter; auto-deploys on push to main).
  - Supabase project `afkhnskxmfplablmfvtl` (Ireland). Its Site URL and redirect point to the Render address.
  - Google OAuth client "Ember" in Google Cloud project `ember-513617`, in testing; test users are added under Audience.
  - Szilard logged in on his iPhone on 2026-11-03 and Ember greeted him.
  - Stripe is set up in **test mode** (2026-11-03) on his account "Solid Results Marketing": product Ember Plus €4.99/month (`price_1UXn8gG7FBneCrtjMlHk8vWe`), webhook "ember" to `/stripe/webhook` (4 events, API version 2023-10-16), and the customer portal (cancel at the end of the period). The three `STRIPE_*` values are in Render, and its log says "payments: on". A test payment and a cancel both reached the `plans` table. Live mode needs his business and ÁSZF first (DEPLOY.md step 6.8).

- **Built and live:** the face, chat, memories with quotes, the memory page, wants, the greeting on return, chats (2026-11-04), experiments, goals (2026-11-04), work sessions, check-ins, end-of-experiment reviews, Ember Plus, privacy/export/delete, five colour versions; a name of your own, check-ups at your time and days, focus and empathy, soft chat edges, levels and looks (2026-11-06).
- **Checked on 2026-11-03:** both checks pass; the live pages load; `/state` without a login is refused (401) and an unsigned webhook is refused (400); Render's logs show no errors (mind: Claude Haiku, invite list 1 person, payments on); with the public key, all four Supabase tables show 0 rows (RLS on, no policies, as intended); Stripe's webhook has 4 deliveries and 0 failures.
- **Supabase hardened (2026-11-03, with Szilard's OK):** the Email sign-in provider is off (only Google is on); `public.rls_auto_enable()` (Supabase's own event-trigger function) can no longer be executed by `public`, `anon` or `authenticated`.
- **Supabase free projects pause after a week with no activity,** so the online server reads it once a day (`keep_awake` in `server/__main__.py`).
- **The mind is Claude Haiku 5.5** ($0.10/$0.50 per million tokens; measured about $0.0003 a reply). The real cost per reply is logged in the `usage` table.
- **iPhone:** the home-screen app blurred under the clock. Tried, in order: no glass; a plain body; no `black-translucent` (2026-11-04, kept); extra padding (too low, removed); now the top bar is pinned at `top: 0` with a plain colour (2026-11-04), the way other web apps fixed it. Confirmed on his iPhone: the blur is gone. A real App Store app (a wrapper around this page) would avoid it entirely, but needs an Apple developer account ($99/year) and a Mac to build. Also WebKit bug 301994 (26.1+ status bar area).

## Next (in order)

1. Go live together, following DEPLOY.md (done 2026-11-03). Left: add to the home screen on his iPhone and check the service worker there. His local Ember is **not** imported: on 2026-11-03 he chose to keep the online one only (it already had his words); `ember_state/` stays on his PC as an archive. Measured cost: 2 replies = 2,589 tokens in / 555 out, about $0.00027 a reply.
2. **Nudges:** check-ups are built (2026-11-04: `follow_up` from the mind → `followups`, one per chat; `due_checkups` also checks in once on a goal's chat after `QUIET_DAYS`, never while its last check-up is unanswered; the server's `checkups` thread hands them to the mind every `checkup_every` seconds as `followup` events, which are free (`OWN`) and say nothing on failure; an empty reply means they'd already told it).
   - **How often is your choice** (2026-11-05, Szilard; `Ember.checkups` in `CHECKUPS`: off, when, daily ("Regularly"); default daily).
     - Once a week and a few times a week were dropped on 2026-11-06, since the days are customizable; `from_dict` turns them into daily.
     - Time and days (2026-11-06, Szilard: "fully customizable"): `checkup_at` is minutes after midnight, any time, default 18:00; `checkup_days` is 0 = Monday … 6 = Sunday, default all.
     - Old saves' `checkup_hour` is migrated in `from_dict`, and `/checkups` still accepts `hour`.
     - `_regular_checkup` hands out a `{"regular": True}` followup at that time on a chosen day, if they haven't written (and it hasn't asked) yet that day.
     - The regular one ignores the quiet night (they chose the time); planned and quiet-goal check-ups still wait for 8:00.
     - Never while a check-up is unanswered.
     - "off" drops due planned ones.
     - The window: ⋯ → Check-ups (`#ckEvery`, `#ckTime` time picker, `#ckDays` day chips, `renderCheckups`, `saveCheckups`), sent to `/checkups` `{every, at, days}` (`set_checkups`).
   - **Greeting on open** (2026-11-05): `arrive(now, chat)` lights up after `LIGHT_UP_AFTER` (1 h), but writes first only the first time, or after `GREET_AFTER` (8 h). It never writes on top of its own unanswered `checkup`/`greet` line.
   - The `checkups` thread's `@asynccontextmanager` had slipped onto it from `lifespan` (it ran by accident); fixed 2026-11-05.
   - **Its name** (2026-11-06, Szilard): `Ember.name` (`DEFAULT_NAME` "Ember", `NAME_MAX` 24, `set_name`; `/name`; ⋯ → Its name, `#emberName`).
     - The prompt says the name when it isn't the default.
     - Notifications have the title "<name> sent you a message" and the body is its words.
     - iPhone may add its own "from Ember" line, which we can't change.
   - Phone notifications are built too (2026-11-04, `server/push.py`), and the key is in Render. iPhone push only works once Ember is added to the home screen.
   - **End-of-experiment reviews are built (2026-11-03).** `update` says once when an experiment's days are up (`timeup` line; the window shows "Finish and look back" / "3 more days" → `/experiment/extend`). `end_experiment` stores `facts` (each session's day, length, rating, words). `/experiment/end` queues a `review` event, which isn't a free message. The reply is kept as `x["review"]` on a `review` line, shown with a facts card, and goes into later prompts.
3. **Becoming someone:** its character and story grow from your shared history.
4. **Later:** open sign-up, App Store wrappers.
- **The mind's model:** Haiku 5.5 was kept on purpose (2026-11-03; Szilard chose it over a mixed setup or Sonnet).
  - Switching is one Render setting: `EMBER_VOICE_MODEL`.
  - If it ever moves to Sonnet or Opus, add prompt caching first. Move the volatile "Now: …" line to the end of the prompt so the instructions and memories form a stable, cacheable start.
  - With Haiku, caching isn't worth it (about $0.0005 a reply, and the prefix may be under the minimum).
