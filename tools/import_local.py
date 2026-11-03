"""
Move your local Ember (ember_state/) into your online account, so it keeps its
memories, experiments and your whole conversation.

1. Log in to the online Ember once with Google (that creates your account).
2. In Render, Suspend the service. (Not a restart: on the way down the server saves the
   Ember it holds in memory, which would undo the import.)
3. Run this on your PC with the Supabase settings in the environment:
       set SUPABASE_URL=https://xxxx.supabase.co
       set SUPABASE_SERVICE_KEY=...        (the service_role key; never share it)
       python tools/import_local.py you@gmail.com
4. In Render, Resume the service.

It replaces the online Ember with your local one, so only use it while the online one is
still fresh: anything said to it online is lost. The local files are not changed.
"""
import json
import os
import sys
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from server.store import FileStore, SupabaseStore  # noqa: E402


def find_user(url, key, email):
    page = 1
    while True:
        req = urllib.request.Request(f"{url}/auth/v1/admin/users?page={page}&per_page=200",
                                     headers={"apikey": key, **({"Authorization": f"Bearer {key}"} if key.startswith("eyJ") else {})})
        with urllib.request.urlopen(req, timeout=15) as r:
            users = json.loads(r.read()).get("users", [])
        for u in users:
            if (u.get("email") or "").lower() == email.lower():
                return u["id"]
        if len(users) < 200:
            return None
        page += 1


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    url, key = os.environ.get("SUPABASE_URL", "").rstrip("/"), os.environ.get("SUPABASE_SERVICE_KEY")
    if not url or not key:
        sys.exit("Set SUPABASE_URL and SUPABASE_SERVICE_KEY first (see the top of this file).")
    state = os.path.join(ROOT, "ember_state")
    local = FileStore(state, fixed=state)
    me = local.load_self("local")
    if not me:
        sys.exit("No local Ember found in ember_state/.")
    uid = find_user(url, key, sys.argv[1])
    if not uid:
        sys.exit("No online account with that email yet: log in to the online Ember once first.")
    online = SupabaseStore(url, key)
    lines = local.lines("local")
    online.save_self(uid, me)
    for i in range(0, len(lines), 500):
        online.append_lines(uid, lines[i:i + 500])
    print(f"Imported: {len(me.get('memories', []))} memories, {len(me.get('experiments', []))} experiments, "
          f"{len(lines)} lines. Now restart the server in Render.")


if __name__ == "__main__":
    main()
