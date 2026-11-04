"""
Make Ember's notification key (VAPID), once.

    python tools/make_vapid.py

It writes VAPID_PRIVATE_KEY into .env (never printed: it's a secret). For Ember online, copy that line's value
into Render (ember → Environment → VAPID_PRIVATE_KEY). Keep the same key afterwards: a new key means every phone
has to turn notifications on again.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from server.push import Push, new_private_key  # noqa: E402

ENV = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")

text = open(ENV, encoding="utf-8").read() if os.path.exists(ENV) else ""
if any(line.startswith("VAPID_PRIVATE_KEY=") for line in text.splitlines()):
    sys.exit(".env already has VAPID_PRIVATE_KEY; keeping it (a new key would turn everyone's notifications off).")
key = new_private_key()
with open(ENV, "a", encoding="utf-8") as f:
    f.write(("" if not text or text.endswith("\n") else "\n") + f"VAPID_PRIVATE_KEY={key}\n")
print("Done: VAPID_PRIVATE_KEY is in .env. Its public half (safe to share):", Push(key).public)
