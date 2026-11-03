"""
Run Ember's server.

Online (Render):   python -m server
    needs ANTHROPIC_API_KEY, SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_KEY,
    EMBER_ALLOWED_EMAILS (comma-separated invite list, or * for everyone); PORT is set by Render.
    Ember Plus: STRIPE_SECRET_KEY, STRIPE_PRICE_ID, STRIPE_WEBHOOK_SECRET (without them the paywall
    says Plus is coming soon), EMBER_FREE_PER_DAY (5), EMBER_PLUS_EMAILS (Plus for free, comma-separated),
    EMBER_PRICE_LABEL ("€4.99 / month").
Local (your PC):   python ember.py   (one Ember, yours, in ember_state/, no login)
"""
import logging
import os
import sys

import uvicorn

from mind import llm
from .app import create_app
from .auth import LocalAuth, SupabaseAuth
from .billing import Billing
from .store import FileStore, SupabaseStore

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def run_local(state_dir, port):
    llm.load_dotenv(os.path.join(ROOT, ".env"))
    cfg = llm.LLMConfig()
    store = FileStore(state_dir, fixed=state_dir)
    app = create_app(store, LocalAuth(), cfg)
    print(f"Its mind: {cfg.describe()}" + (f"  (problem: {cfg.problem})" if cfg.problem else ""))
    print(f"Its window: http://localhost:{port}   (Ctrl+C to close)")
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")


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
                      env.get("EMBER_PRICE_LABEL", "€4.99 / month"))
    app = create_app(store, auth, cfg, daily_cap=int(env.get("EMBER_DAILY_CAP", "150")),
                     public_config={"supabase_url": env["SUPABASE_URL"],
                                    "supabase_anon_key": env["SUPABASE_ANON_KEY"]},
                     billing=billing, free_per_day=int(env.get("EMBER_FREE_PER_DAY", "5")),
                     plus_emails=env.get("EMBER_PLUS_EMAILS", "").split(","))
    logging.getLogger("ember").info("mind: %s; invite list: %s; payments: %s", cfg.describe(),
                                    "everyone" if auth.everyone else f"{len(auth.allowed)} people",
                                    "on" if billing.enabled else "off (Plus coming soon)")
    # access logs off: request paths are harmless, but keep logs to ids and errors
    uvicorn.run(app, host="0.0.0.0", port=int(env.get("PORT", "8000")), access_log=False,
                proxy_headers=True, forwarded_allow_ips="*")


if __name__ == "__main__":
    run_online()
