# Putting Ember online

About an hour, done once. You create five accounts; nothing here costs money except Render (about $7 a month) and the Anthropic credit you add. Stripe takes its fee only when someone pays. Keep this page open and go top to bottom. Wherever it says **copy**, paste the value into a private note for a moment. You'll need it a few steps later.

Never put any key in the code or send it in a chat. Keys only go into Render's settings.

---

## 1. Supabase: logins and the database (free)

1. Go to **supabase.com**, sign up (with GitHub is easiest), then **New project**:
   - Name: `ember`. Region: the EU option (Ember's runs in Ireland, eu-west-1; Frankfurt is fine too). Make up a strong database password (you won't need it again).
2. When the project is ready, **copy** three values:
   - **Project URL**, on the project's home page, like `https://abcdxyz.supabase.co`, which becomes `SUPABASE_URL`;
   - **Project Settings → API Keys → Publishable key** (`sb_publishable_...`), which becomes `SUPABASE_ANON_KEY`;
   - **Secret key** on the same page (`sb_secret_...`; create one named `ember-server` if there isn't one), which becomes `SUPABASE_SERVICE_KEY` (secret!).
   - Older projects show "anon" and "service_role" keys instead. Those work too.
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

## 6. Stripe: Ember Plus payments ($4.99 / month)

Taking real money needs a registered business (for example egyéni vállalkozó) and, for a Hungarian online service, terms of service (ÁSZF) with a refund/cancellation section and your contact details on the site. Get those from an accountant or lawyer; Ember's code doesn't write them. You can do everything below in **test mode** first: test mode moves no money.

1. Go to **stripe.com** and sign up, with your business's details when you go live.
2. **Product catalog → Add product**:
   - Name: `Ember Plus`.
   - Price: **$4.99 USD**, **Recurring**, **Monthly**. Optional: under the price, **Add another currency** (e.g. EUR 4.99), so people in Europe pay in euros; Stripe picks the currency by where the customer is.
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
8. **Going live (real money).** Do these in order. Ember has a safety catch: with a live key (`sk_live_…`) it sells nothing until `EMBER_TERMS_URL` is set (the paywall says Plus is coming soon, and Render's log says "payments: closed").
   1. **Business:**
      - Register as an egyéni vállalkozó (or a company), with a tax number and a business bank account.
      - With an accountant, settle your VAT (e.g. alanyi adómentesség) and how each payment gets an invoice reported to NAV (e.g. Billingo or Számlázz.hu). Stripe's receipts are not Hungarian invoices. Later we can connect the invoicing service to Ember's Stripe webhook so invoices go out by themselves.
   2. **ÁSZF and an updated privacy notice,** from a lawyer or a trusted template service. They cover:
      - who sells (your name, address, tax number, email);
      - the price ($4.99 a month) and that it renews monthly;
      - how to cancel (any time, via Manage Ember Plus);
      - the 14-day withdrawal right for digital services;
      - that Stripe processes the payments.

      Put it online. Or send us the text, and we put it at `/terms` exactly as it is.
   3. **Stripe → activate your account:** business details, bank account and identity check.
   4. **Switch to live mode** and redo steps 2–5 there: the product Ember Plus at $4.99 monthly; the secret key; the webhook to `/stripe/webhook` with the same 4 events; the customer portal. Live mode has its own product, price, keys and webhook secret.
   5. **Stripe → Settings → Public details:** your terms URL and a support email. **Settings → Emails:** turn on receipts for successful payments.
   6. **Render → Environment:**
      - paste the live `STRIPE_SECRET_KEY`, `STRIPE_PRICE_ID` and `STRIPE_WEBHOOK_SECRET` (never into a chat);
      - set `EMBER_TERMS_URL` to your ÁSZF page;
      - set `EMBER_FREE_PER_DAY` to `10`, or delete it (10 is the default).

      Save, and Render restarts. Its log should say "payments: on (live)".
   7. **A real test:**
      - with an account that isn't in `EMBER_PLUS_EMAILS`, use up the 10 free messages and buy Plus with your own card;
      - check that Plus switches on, that Stripe asks you to accept the ÁSZF, and that the invoice is made;
      - then refund the payment in Stripe and cancel via Manage Ember Plus.
   8. **Open sign-up is a separate step** (step 8 below): until you change `EMBER_ALLOWED_EMAILS` to `*`, only invited people can use Ember at all.

## 6b. Phone notifications (Ember's check-ups)

1. On your PC, in the `brain` folder: `python tools/make_vapid.py`. It puts `VAPID_PRIVATE_KEY` into `.env` (it doesn't show it).
2. Open `.env` in Notepad, copy the text after `VAPID_PRIVATE_KEY=`, and add it in **Render → ember → Environment** as `VAPID_PRIVATE_KEY`. Save; Render restarts, and its log says "notifications: on".
3. Keep that key forever: a new one would switch everyone's notifications off.
4. On iPhone: notifications only work in the home-screen app (iOS 16.4 or later). Open Ember from its home-screen icon, then **⋯ → Turn on notifications** and allow them.

## 7. Try it

1. On your iPhone, open the Render address in **Safari**, then tap **Continue with Google**.
2. Ember greets you. Say something.
3. **Share → Add to Home Screen**. Now Ember has its own icon and opens full screen.
4. Optional, and only before you talk to the online Ember: bring your local Ember over with `tools/import_local.py`. It replaces the online one; the steps (suspend the service, import, resume) are at the top of that file.

## 8. Opening Ember to everyone

Anyone with a Google account can then log in and get their own Ember. Do these in order.

1. **Anthropic → Limits:** check the monthly spend limit (step 3.3) and set it to what you're willing to spend at most, e.g. $30. It's the one cap over everyone together. If it's reached, Ember tells people it can't think right now, until next month or until you raise it. Each person is also capped at `EMBER_DAILY_CAP` (150) replies a day, which is under $0.10 a day even for the busiest person.
2. **Push the code** (`git push`), so the server understands `*` for Plus.
3. **Google Cloud** (project `ember-513617`) → **Google Auth Platform → Branding** first: Application home page `https://ember-dztb.onrender.com/home` (the public front page), privacy policy link `https://ember-dztb.onrender.com/privacy`, and under Authorized domains add `ember-dztb.onrender.com`; Save. Until then the Publish button is greyed out. Then **Audience** (older menus: APIs & Services → OAuth consent screen) → **Publish app** → Confirm. Don't upload a logo: a logo makes Google review the app first. Ember asks Google only for the name and email, so Google doesn't need to review it. While it's "in testing", only the test users can log in. If Google asks for verification, don't fill anything in; ask us first.
4. **Render → ember → Environment:**
   - `EMBER_ALLOWED_EMAILS` = `*` (everyone can log in);
   - `EMBER_PLUS_EMAILS` = `*` (everyone has Plus for free, for now).

   Save; Render restarts. Its log should say "invite list: everyone; Plus for free: everyone".
5. **Try it** with a Google account that was never a test user.

To go back: put your own Gmail back in `EMBER_PLUS_EMAILS` to end free Plus (everyone else then gets 10 free messages a day). To close sign-up again, put the invite list back in `EMBER_ALLOWED_EMAILS`: people who aren't on it see "not invited", and their Embers are kept.

## Afterwards

- **The owner page (easiest):** put your Gmail in `EMBER_OWNER_EMAILS` in Render. Then in Ember, ⋯ → **Owner: who uses Ember** shows how many people use it, who was here today and this week, whether people come back after their first day and after their first week, the cost, the feedback, and one line per person (email, started, last seen, days, messages, level, goals). It never shows what anyone said.
- **Who has logged in:** Supabase → your project → **Authentication → Users**. It lists everyone who has ever signed in: their email, when they first signed in, and when they last signed in. Their **UID** there is the `user_id` in the database tables.
- **Feedback:** people send it from ⋯ → Send feedback (an idea, something's wrong, or something else). Read it in Supabase → **Table Editor → `feedback`**: the text, their email (to answer them), the kind, and `extra` (level, Plus, where they were, browser). The table comes from `server/schema.sql`: if it isn't there yet, run the whole file once more in the SQL Editor (it only adds what's missing). Until then, sending feedback says "Couldn't send it right now".
- **How much each person uses it:** Supabase → **Table Editor → `usage`**: replies (`calls`), counted messages and tokens per person per day.
- **Try every look:** add your Gmail to `EMBER_UNLOCK_EMAILS` in Render. Every look is unlocked for you; your level and XP don't change.
- **If Ember is slow:** Render → Logs, search for `mind answered`: each answer's time is there (a warning when it took over 20 seconds).
- **Free messages:** `EMBER_FREE_PER_DAY` (10) per day for people without Plus. Comped Plus: `EMBER_PLUS_EMAILS`, or `*` for everyone.
- **New tester** (while it's invite-only): add their Gmail to `EMBER_ALLOWED_EMAILS` in Render (Environment). Render restarts by itself. Also add them as a test user in Google (step 2.2).
- **How many people it can take:** one server thinks up 4 answers at once (Render setting `EMBER_MIND_THREADS`), and an Ember nobody has used for an hour leaves its memory until it's needed again. That's fine for several hundred people. Every 5 minutes it still reads everyone's Ember to see whose check-up is due: well before a few thousand people, tell us, and we change that.
- **Changes:** every `git push` to `main` redeploys Ember automatically.
- **Costs:** see Anthropic's console (Usage) and Render's billing. The `usage` table in Supabase shows calls and tokens per person per day.
- **If something breaks:** Render → your service → **Logs**. Logs contain ids and errors only, never what anyone said.
