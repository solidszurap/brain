# Putting Ember online

About an hour, done once. You create five accounts; nothing here costs money except Render (about $7 a month) and the Anthropic credit you add. Stripe takes its fee only when someone pays. Keep this page open and go top to bottom. Wherever it says **copy**, paste the value into a private note for a moment. You'll need it a few steps later.

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
   | `EMBER_PLUS_EMAILS` | who gets Ember Plus for free: at least your own Gmail |
   | `STRIPE_SECRET_KEY`, `STRIPE_PRICE_ID`, `STRIPE_WEBHOOK_SECRET` | leave empty for now; step 6 fills them. Until then, the paywall says Plus is "coming soon". |

4. Press **Apply** and wait for "Live" (a few minutes). Your address is at the top, like `https://ember-xxxx.onrender.com`. **Copy** it.

## 5. Connect the pieces

In Supabase, go to **Authentication → URL Configuration**:
- **Site URL**: your Render address from step 4.4.
- **Redirect URLs**: add the same address.

## 6. Stripe: Ember Plus payments (€4.99 / month)

Taking real money needs a registered business (for example egyéni vállalkozó) and, for a Hungarian online service, terms of service (ÁSZF) with a refund/cancellation section and your contact details on the site. Get those from an accountant or lawyer; Ember's code doesn't write them. You can do everything below in **test mode** first: test mode moves no money.

1. Go to **stripe.com** and sign up, with your business's details when you go live.
2. **Product catalog → Add product**:
   - Name: `Ember Plus`.
   - Price: **€4.99**, **Recurring**, **Monthly**.
   - Save, then open the price and **copy** its id (`price_...`). That's `STRIPE_PRICE_ID`.
3. **Developers → API keys**. **Copy** the **Secret key** (`sk_test_...` in test mode, `sk_live_...` later). That's `STRIPE_SECRET_KEY`.
4. **Developers → Webhooks → Add endpoint**:
   - URL: your Render address + `/stripe/webhook` (e.g. `https://ember-xxxx.onrender.com/stripe/webhook`).
   - Events: `checkout.session.completed`, `customer.subscription.created`, `customer.subscription.updated`, `customer.subscription.deleted`.
   - After saving, **copy** the **Signing secret** (`whsec_...`). That's `STRIPE_WEBHOOK_SECRET`.
5. **Settings → Billing → Customer portal**: turn it on, and allow customers to cancel and to update their payment method. ("Manage Ember Plus" opens this.)
6. In Render, under **Environment**, fill in the three `STRIPE_...` values and save. Render restarts by itself.
7. Test it with a free account that isn't in `EMBER_PLUS_EMAILS`:
   - Use up today's free messages, press **Get Ember Plus**, and pay with Stripe's test card (Stripe shows it on its test checkout page). Ember Plus should switch on within seconds.
   - Then cancel via the menu → **Manage Ember Plus**.
8. **Going live:** switch Stripe to live mode, then redo steps 2–4 there (live mode has its own product, price, keys and webhook secret), and put the live values in Render.

## 7. Try it

1. On your iPhone, open the Render address in **Safari**, then tap **Continue with Google**.
2. Ember greets you. Say something.
3. **Share → Add to Home Screen**. Now Ember has its own icon and opens full screen.
4. Optional: bring your local Ember's memories over with `tools/import_local.py` (instructions at the top of that file), then in Render: **Manual Deploy → Restart service**.

## Afterwards

- **Free messages:** `EMBER_FREE_PER_DAY` (5) per day for people without Plus. Comped Plus: `EMBER_PLUS_EMAILS`.
- **New tester:** add their Gmail to `EMBER_ALLOWED_EMAILS` in Render (Environment). Render restarts by itself. Also add them as a test user in Google (step 2.2).
- **Changes:** every `git push` to `main` redeploys Ember automatically.
- **Costs:** see Anthropic's console (Usage) and Render's billing. The `usage` table in Supabase shows calls and tokens per person per day.
- **If something breaks:** Render → your service → **Logs**. Logs contain ids and errors only, never what anyone said.
