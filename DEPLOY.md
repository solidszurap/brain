# Putting Ember online

About 45 minutes, done once. You create four accounts; nothing here costs money except Render (about $7 a month) and the Anthropic credit you add. Keep this page open and go top to bottom. Wherever it says **copy**, paste the value into a private note for a moment. You'll need it a few steps later.

Never put any key in the code or send it in a chat. Keys only go into Render's settings.

---

## 1. Supabase: logins and the database (free)

1. Go to **supabase.com**, sign up (with GitHub is easiest), then **New project**:
   - Name: `ember`. Region: **Frankfurt (eu-central-1)**. Make up a strong database password (you won't need it again).
2. When the project is ready, open **Project Settings → API** (or "Data API" / "API Keys"). **Copy** three values:
   - **Project URL**, like `https://abcdxyz.supabase.co`, which becomes `SUPABASE_URL`;
   - **anon public** key, which becomes `SUPABASE_ANON_KEY`;
   - **service_role** key, which becomes `SUPABASE_SERVICE_KEY` (secret!).
3. Open **SQL Editor → New query**, paste the whole content of `server/schema.sql` from this repo, and press **Run**. You should see "Success".

## 2. Google: the "Continue with Google" button (free)

1. Go to **console.cloud.google.com**, then create a project named `Ember`.
2. **APIs & Services → OAuth consent screen**:
   - User type: **External**. App name: `Ember`. Support email: yours. Save.
   - Under "Test users", add your Gmail and your testers' Gmail addresses. While the app is "in testing", only these can log in, which suits the invite-only phase.
3. **APIs & Services → Credentials → Create credentials → OAuth client ID**:
   - Type: **Web application**. Name: `Ember`.
   - **Authorized redirect URIs**: add `https://abcdxyz.supabase.co/auth/v1/callback`, using your own Project URL from step 1.2.
   - Create, then **copy** the **Client ID** and the **Client secret**.
4. Back in Supabase: **Authentication → Sign In / Providers → Google**. Turn it on, paste the Client ID and the Client secret, and save.

## 3. Anthropic: Ember's mind (Claude Haiku)

1. Go to **console.anthropic.com** and sign up.
2. **Billing**: add **$5** of credit.
3. **Limits**: set a **monthly spend limit** of, say, $10, so costs can never run away.
4. **API Keys → Create key**, named `ember-server`. **Copy** it: this is `ANTHROPIC_API_KEY`. It's shown only once.

## 4. Render: the server that runs Ember (~$7/month)

1. Push this repo to GitHub first (`git push`).
2. Go to **render.com** and sign up with GitHub. Then **New → Blueprint**, pick the `solidszurap/brain` repo, and Render reads `render.yaml`:
   - a web service called `ember`, in Frankfurt, on the Starter plan.
   - The free plan isn't enough: it sleeps when idle, and Ember's mind would stop mid-thought.
3. Render asks for the secret values. Paste:

   | Setting | Value |
   |---|---|
   | `ANTHROPIC_API_KEY` | from step 3 |
   | `SUPABASE_URL` | from step 1 |
   | `SUPABASE_ANON_KEY` | from step 1 |
   | `SUPABASE_SERVICE_KEY` | from step 1 |
   | `EMBER_ALLOWED_EMAILS` | your Gmail, plus testers', separated by commas (e.g. `you@gmail.com,friend@gmail.com`) |

4. Press **Apply** and wait for "Live" (a few minutes). Your address is at the top, like `https://ember-xxxx.onrender.com`. **Copy** it.

## 5. Connect the pieces

In Supabase, go to **Authentication → URL Configuration**:
- **Site URL**: your Render address from step 4.4.
- **Redirect URLs**: add the same address.

## 6. Try it

1. On your iPhone, open the Render address in **Safari**, then tap **Continue with Google**.
2. Ember greets you. Say something.
3. **Share → Add to Home Screen**. Now Ember has its own icon and opens full screen.
4. Optional: bring your local Ember's memories over with `tools/import_local.py` (instructions at the top of that file), then in Render: **Manual Deploy → Restart service**.

## Afterwards

- **New tester:** add their Gmail to `EMBER_ALLOWED_EMAILS` in Render (Environment). Render restarts by itself. Also add them as a test user in Google (step 2.2).
- **Changes:** every `git push` to `main` redeploys Ember automatically.
- **Costs:** see Anthropic's console (Usage) and Render's billing. The `usage` table in Supabase shows calls and tokens per person per day.
- **If something breaks:** Render → your service → **Logs**. Logs contain ids and errors only, never what anyone said.
