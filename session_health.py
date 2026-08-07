# session_health.py — saare bot sessions test: alive/dead
# Dead sessions (auth key kill) ko bot_sessions se hatao — alive rakho
import os, sys, asyncio, json, urllib.request

try:
    import cryptg  # noqa
except Exception:
    os.system(f"{sys.executable} -m pip install -q cryptg")

from telethon import TelegramClient
from telethon.sessions import StringSession

AID = int(os.environ.get("KEY_16", "0").strip())
AHASH = os.environ.get("KEY_17", "").strip()
SBURL = os.environ.get("KEY_20", "").strip().rstrip("/")
SBKEY = os.environ.get("KEY_21", "").strip()

def sb_get():
    url = f"{SBURL}/rest/v1/progress?select=state&id=eq.bot_sessions&limit=1"
    req = urllib.request.Request(url, headers={"apikey": SBKEY, "Authorization": f"Bearer {SBKEY}"})
    with urllib.request.urlopen(req, timeout=30) as r:
        d = json.loads(r.read().decode())
    return (d[0].get("state") or {}) if d else {}

def sb_save(state):
    body = json.dumps({"id": "bot_sessions", "state": state}).encode()
    req = urllib.request.Request(f"{SBURL}/rest/v1/progress", data=body, method="POST",
        headers={"apikey": SBKEY, "Authorization": f"Bearer {SBKEY}",
                 "Content-Type": "application/json", "Prefer": "resolution=merge-duplicates"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.status

async def test_one(ss, tag):
    c = TelegramClient(StringSession(ss), AID, AHASH, connection_retries=1)
    try:
        await c.connect()
        me = await c.get_me()
        await c.disconnect()
        return True, getattr(me, "username", "?")
    except Exception as e:
        try:
            await c.disconnect()
        except Exception:
            pass
        return False, str(e)[:60]

async def main():
    st = sb_get()
    tokens = dict(st.get("tokens") or {})
    print(f"[*] bots in store: {[k for k in st if isinstance(st[k], list)]}", flush=True)
    total_alive = 0
    for name in sorted([k for k in st if isinstance(st[k], list)]):
        sesses = st[name]
        alive = []
        for i, ss in enumerate(sesses):
            ok, info = await test_one(ss, f"{name}#{i+1}")
            if ok:
                alive.append(ss)
                total_alive += 1
                print(f"  [ok] {name}#{i+1}: @{info}", flush=True)
            else:
                print(f"  [x] {name}#{i+1}: DEAD ({info})", flush=True)
        st[name] = alive
        if alive:
            print(f"  -> {name}: {len(alive)} alive sessions", flush=True)
    st["tokens"] = tokens
    st["checked_at"] = int(__import__("time").time())
    r = sb_save(st)
    print(f"[*] saved — total alive: {total_alive} | HTTP {r}", flush=True)
    # per-bot summary
    for name in sorted([k for k in st if isinstance(st[k], list)]):
        print(f"  {name}: {len(st[name])} sessions", flush=True)
    print("[done]", flush=True)

asyncio.run(main())
