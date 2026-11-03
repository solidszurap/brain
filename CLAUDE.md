# Ember / brain

**Ember** is a small being with a face, now a web app (phone-first, Google login, one Ember per person). It helps you find what to work towards, then works alongside you on it, and over time it becomes someone who knows your story. Szilard is its first user; he has no project yet, which is exactly the problem it's for. A possible business later: a free plan with a daily limit plus Ember Plus via Stripe; no ads, no selling data. README.md is the overview; DEPLOY.md is how it goes online.

Owner: Szilard (Hungarian, Budapest/Szeged; prefers direct, concrete, plain answers; gets lost in jargon; runs on Windows; not technical about hosting, so he relies on us for that). GitHub: solidszurap/brain.

## Run

```bash
pip install -r requirements.txt       # fastapi, uvicorn, anthropic
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
- `server/billing.py`: `Billing` (Stripe via urllib: `checkout`, `portal`, `cancel`, `verify` with a 5-minute tolerance, `plan_from_event`). The stores have `get_plan`/`set_plan` and `add_message`/`messages_today`.
- `server/auth.py`: `SupabaseAuth` (`/auth/v1/user`, 5-minute cache, `EMBER_ALLOWED_EMAILS` or `*`) and `LocalAuth`.
- `server/__main__.py`: `run_online` (env, refuses to start without a usable mind; starts `keep_awake`, one Supabase read a day) and `run_local` (used by `ember.py`).
- `mind/core.py`, `Ember`:
  - wants: `connection` and `curiosity`, moved by real time in `update`;
  - `mood`;
  - `face()` with its reasons;
  - `prompt()` and `respond()`, the mind's JSON → reply, face, remember/update/add_steps/done_steps/experiments;
  - memories `{id, kind, note, quote, t, edited}`;
  - experiments, sessions and the check-in;
  - `say()`;
  - `_template` (the mind without an LLM);
  - the safety rule in `SYSTEM`.
- `mind/llm.py`: `LLMConfig` (`EMBER_VOICE`; Claude first in auto), `call_llm`, `LLMError(retryable)`, and `_call_claude` (`anthropic` SDK, `claude-haiku-5-5`, effort low, records `cfg.last_usage`).
- `web/index.html`:
  - Boot reads `/config`. Online, it loads supabase-js (pinned 2.118.0 from jsdelivr; supports Supabase's new publishable keys) for Google login. `api()` adds the bearer token; a 401 shows the login cover and a 403 shows "not invited".
  - The top switch is Chat | Experiment (`mode`, kept in localStorage, sent with `/talk`, which tells the mind). Experiment mode shows `#sessionbar` (always while a session runs). Ideas are there from the start: before `knows_enough()` (3 memories) they are `starter` experiments (`STARTERS` for the template mind) that need no memory; after it, each must cite memories.
  - The canvas face (`EXPR`) sits above the conversation. Experiment cards render under an Ember line's `exps`; the check-in renders under the last `checkin` line while `checkin_due`. The experiment line is `#sessionbar`, with its pop-up `#expcard`.
  - The look: solid surfaces with a thin edge (`--surface`, `--raised`, `--overlay`, `--edge`), soft shadows (`--lift`), a warm glow behind (`--glow1-3`) and flat orange buttons (`--btn`). No glass: no backdrop blur, gloss or lit edges (Szilard, 2026-11-03). The body is `position: fixed; inset: 0`, so the page is exactly the screen. iOS 26 paints the strip behind the clock from the pinned layer at the top (the body) if it has one plain colour, and blurs the page there if not, so the body's background is plain `--bg` and the glow is `body::before`. Never give the body a gradient or blur again. (Sources: hawkshift.com/research/ios-26-safari-status-bar; WebKit bug 301994.) Colour versions (Ember, Night, Plum, Forest, Day) are `[data-theme]` token overrides, picked in the menu and kept in localStorage `ember.theme`; Ember and the buttons stay orange in all of them. The model's name is never shown.
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
   - It never claims feelings. Its wants are numbers, and "why this face?" says so.
   - When its mind can't answer, it says so; no fake answers online.
   - Honesty is a trait, not the whole product: no heavy checking pipelines unless asked.
5. **Dependencies:**
   - `mind/core.py` uses the standard library only.
   - The server uses FastAPI, uvicorn and `anthropic` only.
   - Secrets only in `.env` (local) or Render's environment (online). Never print or log keys, or anything users say: logs hold ids and errors only.
6. **Invite-only** (`EMBER_ALLOWED_EMAILS`) until Szilard decides otherwise.
7. **Free and Plus:** 5 free messages a day, then Ember Plus at €4.99 a month (Stripe). Never sell data and never show ads. Taking real money needs his registered business and terms of service (ÁSZF); we don't write legal text.
8. **No long runs.** Verify with `check_ember.py`, `check_server.py`, and by trying it in the browser (phone size 375 px and desktop) on a scratch Ember.
9. **Saved selves must keep loading.** `Ember.from_dict` only copies known fields, so new fields get their defaults; keep it that way.
10. **Commits:** small, straight to main, only when Szilard asks (don't ask him whether to commit). He pushes. Update README.md in the same change.

## Where things stand (2026-11-03)

- **LIVE: https://ember-dztb.onrender.com** (Render service `ember`, Frankfurt, Starter; auto-deploys on push to main).
  - Supabase project `afkhnskxmfplablmfvtl` (Ireland). Its Site URL and redirect point to the Render address.
  - Google OAuth client "Ember" in Google Cloud project `ember-513617`, in testing; test users are added under Audience.
  - Szilard logged in on his iPhone on 2026-11-03 and Ember greeted him.
  - Stripe is set up in **test mode** (2026-11-03) on his account "Solid Results Marketing": product Ember Plus €4.99/month (`price_1UXn8gG7FBneCrtjMlHk8vWe`), webhook "ember" to `/stripe/webhook` (4 events, API version 2023-10-16), and the customer portal (cancel at the end of the period). The three `STRIPE_*` values are in Render, and its log says "payments: on". A test payment and a cancel both reached the `plans` table. Live mode needs his business and ÁSZF first (DEPLOY.md step 6.8).

- **Built and live:** the face, chat, memories with quotes, the memory page, wants, the greeting on return, Chat | Experiment, experiments, work sessions, check-ins, end-of-experiment reviews, Ember Plus, privacy/export/delete, five colour versions.
- **Checked on 2026-11-03:** both checks pass; the live pages load; `/state` without a login is refused (401) and an unsigned webhook is refused (400); Render's logs show no errors (mind: Claude Haiku, invite list 1 person, payments on); with the public key, all four Supabase tables show 0 rows (RLS on, no policies, as intended); Stripe's webhook has 4 deliveries and 0 failures.
- **Supabase hardened (2026-11-03, with Szilard's OK):** the Email sign-in provider is off (only Google is on); `public.rls_auto_enable()` (Supabase's own event-trigger function) can no longer be executed by `public`, `anon` or `authenticated`.
- **Supabase free projects pause after a week with no activity,** so the online server reads it once a day (`keep_awake` in `server/__main__.py`).
- **The mind is Claude Haiku 5.5** ($0.10/$0.50 per million tokens; measured about $0.0003 a reply). The real cost per reply is logged in the `usage` table.
- **iPhone:** iOS 26 draws its own blur under the clock in home-screen web apps, and 26.1+ has a WebKit bug with the status bar area (WebKit bug 301994). Neither is Ember's CSS.

## Next (in order)

1. Go live together, following DEPLOY.md (done 2026-11-03). Left: add to the home screen on his iPhone and check the service worker there. His local Ember is **not** imported: on 2026-11-03 he chose to keep the online one only (it already had his words); `ember_state/` stays on his PC as an archive. Measured cost: 2 replies = 2,589 tokens in / 555 out, about $0.00027 a reply.
2. **Nudges:** phone notifications via Web Push (VAPID, `sw.js`), rare, and they can be turned off. Needs a decision first: VAPID signing is ES256 (not in Python's standard library), so either a small pure-Python P-256 signer or a new dependency (`cryptography`/`pywebpush`, against rule 5). iPhone push only works once Ember is added to the home screen.
   - **End-of-experiment reviews are built (2026-11-03).** `update` says once when an experiment's days are up (`timeup` line; the window shows "Finish and look back" / "3 more days" → `/experiment/extend`). `end_experiment` stores `facts` (each session's day, length, rating, words). `/experiment/end` queues a `review` event, which isn't a free message. The reply is kept as `x["review"]` on a `review` line, shown with a facts card, and goes into later prompts.
3. **Becoming someone:** its character and story grow from your shared history.
4. **Later:** open sign-up, App Store wrappers.
- **The mind's model:** Haiku 5.5 was kept on purpose (2026-11-03; Szilard chose it over a mixed setup or Sonnet).
  - Switching is one Render setting: `EMBER_VOICE_MODEL`.
  - If it ever moves to Sonnet or Opus, add prompt caching first. Move the volatile "Now: …" line to the end of the prompt so the instructions and memories form a stable, cacheable start.
  - With Haiku, caching isn't worth it (about $0.0005 a reply, and the prefix may be under the minimum).
