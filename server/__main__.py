"""
Run Ember's server.

Online (Render):   python -m server
    needs ANTHROPIC_API_KEY, SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_KEY,
    EMBER_ALLOWED_EMAILS (comma-separated invite list, or * for everyone); PORT is set by Render.
    Notifications: VAPID_PRIVATE_KEY (tools/make_vapid.py), VAPID_SUBJECT (optional).
    Ember Plus: STRIPE_SECRET_KEY, STRIPE_PRICE_ID, STRIPE_WEBHOOK_SECRET (without them the paywall
    says Plus is coming soon), EMBER_FREE_PER_DAY (10), EMBER_PLUS_EMAILS (Plus for free, comma-separated, or * for everyone),
    EMBER_UNLOCK_EMAILS (testers: every look unlocked, XP unchanged), EMBER_OWNER_EMAILS (who can open the owner page), EMBER_MIND_THREADS (how many answers are thought up at once; default 4), EMBER_PUBLIC_URL (Ember's address; pages opened at …onrender.com move there; default https://yourember.app), EMBER_PRICE_LABEL ("$4.99 / month"), EMBER_TERMS_URL (your ÁSZF page; with a live Stripe key, Plus is only sold once it's set), EMBER_ANALYTICS_TOKEN (Cloudflare Web Analytics; default: yourember.app's; empty switches it off).
Local (your PC):   python ember.py   (one Ember, yours, in ember_state/, no login)
"""
import logging
import os
import sys
import threading
import time

import uvicorn

from mind import llm
from .app import create_app
from .auth import LocalAuth, SupabaseAuth
from .billing import Billing
from .push import Push
from .store import FileStore, SupabaseStore

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ANALYTICS_TOKEN = "68c2f801192443c3beacd59c5ae32b26"   # Cloudflare Web Analytics for yourember.app (not a secret: it's in every page)


def run_local(state_dir, port):
    llm.load_dotenv(os.path.join(ROOT, ".env"))
    cfg = llm.LLMConfig()
    store = FileStore(state_dir, fixed=state_dir)
    key = os.environ.get("VAPID_PRIVATE_KEY")
    app = create_app(store, LocalAuth(), cfg, push=Push(key) if key else None)
    print(f"Its mind: {cfg.describe()}" + (f"  (problem: {cfg.problem})" if cfg.problem else ""))
    print(f"Its window: http://localhost:{port}   (Ctrl+C to close)")
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")


def keep_awake(store, every=86400):
    """Supabase pauses a free project after a week without use; one small read a day keeps it awake."""
    while True:
        time.sleep(every)
        try:
            store.all_uids()
        except Exception as e:
            logging.getLogger("ember").warning("keep-awake read failed: %s", type(e).__name__)


def run_online():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    env = os.environ
    missing = [k for k in ("ANTHROPIC_API_KEY", "SUPABASE_URL", "SUPABASE_ANON_KEY", "SUPABASE_SERVICE_KEY")
               if not env.get(k)]
    if missing:
        sys.exit("Missing settings: " + ", ".join(missing))
    cfg = llm.LLMConfig(env={**env, "EMBER_VOICE": env.get("EMBER_VOICE", "anthropic")})
    if not cfg.usable:
        sys.exit(f"Ember's mind isn't usable online: {cfg.problem or cfg.provider}")
    store = SupabaseStore(env["SUPABASE_URL"], env["SUPABASE_SERVICE_KEY"])
    auth = SupabaseAuth(env["SUPABASE_URL"], env["SUPABASE_ANON_KEY"], env.get("EMBER_ALLOWED_EMAILS", ""))
    billing = Billing(env.get("STRIPE_SECRET_KEY"), env.get("STRIPE_PRICE_ID"), env.get("STRIPE_WEBHOOK_SECRET"),
                      terms_url=env.get("EMBER_TERMS_URL"), yearly_id=env.get("STRIPE_PRICE_YEARLY"))
    push = Push(env["VAPID_PRIVATE_KEY"], env.get("VAPID_SUBJECT")) if env.get("VAPID_PRIVATE_KEY") else None
    app = create_app(store, auth, cfg, daily_cap=int(env.get("EMBER_DAILY_CAP", "150")),
                     public_config={"supabase_url": env["SUPABASE_URL"],
                                    "supabase_anon_key": env["SUPABASE_ANON_KEY"]},
                     billing=billing, free_per_day=int(env.get("EMBER_FREE_PER_DAY", "10")),
                     plus_emails=env.get("EMBER_PLUS_EMAILS", "").split(","), push=push,
                     unlock_emails=env.get("EMBER_UNLOCK_EMAILS", "").split(","),
                     owner_emails=env.get("EMBER_OWNER_EMAILS", "").split(","),
                     mind_threads=int(env.get("EMBER_MIND_THREADS", "4")),
                     public_url=env.get("EMBER_PUBLIC_URL", "https://yourember.app"),
                     analytics_token=env.get("EMBER_ANALYTICS_TOKEN", ANALYTICS_TOKEN) or None)
    plus = [e.strip() for e in env.get("EMBER_PLUS_EMAILS", "").split(",") if e.strip()]
    logging.getLogger("ember").info("mind: %s; invite list: %s; Plus for free: %s; payments: %s; notifications: %s",
                                    cfg.describe(), "everyone" if auth.everyone else f"{len(auth.allowed)} people",
                                    "everyone" if "*" in plus else f"{len(plus)} people",
                                    ("closed: live key, but no EMBER_TERMS_URL yet" if billing.enabled and not billing.selling else ("on (live)" if billing.live else "on (test mode)")) if billing.enabled else "off (Plus coming soon)", "on" if push else "off")
    threading.Thread(target=keep_awake, args=(store,), daemon=True).start()
    # access logs off: request paths are harmless, but keep logs to ids and errors
    uvicorn.run(app, host="0.0.0.0", port=int(env.get("PORT", "8000")), access_log=False,
                proxy_headers=True, forwarded_allow_ips="*")


if __name__ == "__main__":
    run_online()
