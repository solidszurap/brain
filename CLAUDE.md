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
  - The POST guard: `X-Ember` header and same host. Plus `/me/export` and `/me/delete`.
- `server/store.py`: `FileStore` (a folder; `fixed=` for local mode; delete = archive) and `SupabaseStore` (PostgREST via urllib with the service key; delete = rows plus the auth user).
- `server/auth.py`: `SupabaseAuth` (`/auth/v1/user`, 5-minute cache, `EMBER_ALLOWED_EMAILS` or `*`) and `LocalAuth`.
- `server/__main__.py`: `run_online` (env, refuses to start without a usable mind) and `run_local` (used by `ember.py`).
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
  - Boot reads `/config`. Online, it loads supabase-js (pinned 2.45.4 from jsdelivr) for Google login. `api()` adds the bearer token; a 401 shows the login cover and a 403 shows "not invited".
  - The canvas face (`EXPR`) sits above the conversation. Experiment cards render under an Ember line's `exps`; the check-in renders under the last `checkin` line while `checkin_due`. The experiment line is `#sessionbar`, with its pop-up `#expcard`.
  - The menu (⋯): install guide, privacy, export, log out, delete. Confirmations are a second click (`sure`), because `confirm()` is blocked in the app's browser.
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
7. **No long runs.** Verify with `check_ember.py`, `check_server.py`, and by trying it in the browser (phone size 375 px and desktop) on a scratch Ember.
8. **Saved selves must keep loading.** `Ember.from_dict` only copies known fields, so new fields get their defaults; keep it that way.
9. **Commits:** small, straight to main, only when Szilard asks (don't ask him whether to commit). He pushes. Update README.md in the same change.

## Where things stand (2026-11-03)

- **Slices 1 and 2 are built:** the face, chat, memories with quotes, the memory page, wants, the greeting on return, experiments and work sessions in the conversation.
- **The online version is built and checked locally, but not deployed:**
  - `check_server.py`: all checks pass, including SupabaseStore and SupabaseAuth against a fake Supabase.
  - The phone layout was tried at 375 px.
  - The service worker can't register in the app's built-in browser; check it on a real phone.
  - Real Supabase and Google login are untested until Szilard creates the accounts (DEPLOY.md).
- **The mind is Claude Haiku 5.5** ($0.10/$0.50 per million tokens; about $0.0005 per reply, estimated). Szilard funds $5 to start. The real cost per reply is logged in the `usage` table.

## Next (in order)

1. Go live together, following DEPLOY.md. Then: log in on his iPhone, add to the home screen, import his local Ember, and check the real token costs.
2. **Nudges:** phone notifications via Web Push (VAPID, `sw.js`), rare, and they can be turned off. Plus **honest end-of-experiment reviews**.
3. **Becoming someone:** its character and story grow from your shared history.
4. **Later:** Ember Plus (Stripe), open sign-up, App Store wrappers.
