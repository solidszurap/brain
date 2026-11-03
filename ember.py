"""
Ember on your own computer: the same server that runs online (server/), in local
mode: one Ember, yours, kept in ember_state/, no login.

    python ember.py              then open http://localhost:8765 (start_ember.bat does both)
    python ember.py --port 8800 --state scratch_dir   (a separate Ember, for trying things out)

Its mind is set in .env (see mind/llm.py). Everything it is lives in
ember_state/: ember.json (its self and what it remembers about you),
conversation.jsonl (every line said) and usage.json (mind calls per day).

The Ember that lived in a grid world (until 2026-11) is in old/; its life is
archived in ember_state/archive/, never deleted.
"""
import argparse
import os
import shutil
import time

HERE = os.path.dirname(os.path.abspath(__file__))
STATE_DIR = os.path.join(HERE, "ember_state")


def archive_old_life(state_dir=STATE_DIR, now=None):
    """The grid-world Ember's files move to ember_state/archive/<date>_grid_ember/. Never deleted."""
    if not os.path.isdir(state_dir):
        return None
    keep = {"ember.json", "ember.json.bak", "conversation.jsonl", "usage.json", "archive"}
    old = [f for f in os.listdir(state_dir) if f not in keep]
    if not old:
        return None
    stamp = time.strftime("%Y-%m-%d", time.localtime(now or time.time()))
    dest = os.path.join(state_dir, "archive", f"{stamp}_grid_ember")
    os.makedirs(dest, exist_ok=True)
    for f in old:
        shutil.move(os.path.join(state_dir, f), os.path.join(dest, f))
    return dest


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--state", default=None, help="a different folder for its self (for trying things out)")
    args = ap.parse_args()
    state = os.path.abspath(args.state) if args.state else STATE_DIR
    os.makedirs(state, exist_ok=True)
    moved = archive_old_life(state)
    if moved:
        print(f"The grid-world Ember's life was archived (not deleted) in {os.path.relpath(moved, HERE)}")
    from server.__main__ import run_local
    run_local(state, args.port)


if __name__ == "__main__":
    main()
