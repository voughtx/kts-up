# make_bot_sessions.py — paced bot session factory
# Har bot ke liye naye auth-key sessions banata hai (45s pause), Supabase mein save karta hai
# Use: ek baar chalao, sessions store ho jayenge — production wahi reuse karega
import os, sys, time, json, urllib.request

try:
    import cryptg  # noqa
except Exception:
    os.system(f"{sys.executable} -m pip install -q cryptg")

import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession

AID = int(os.environ.get("KEY_16", "0").strip())
AHASH = os.environ.get("KEY_17", "").strip()
SBURL = os.environ.get("KEY_20", "").strip()
SBKEY = os.environ.get("KEY_21", "").strip()
BOT_TOKENS = [os.environ.get(f"KEY_{i}", "").strip() for i in range(22, 28)]
BOT_TOKENS = [t for t in BOT_TOKENS if t]
PER_BOT = int(os.environ.get("PER_BOT", "4").strip())
PAUSE = int(os.environ.get("PAUSE_S", "30").strip())

def sb_get():
    try:
        req = urllib.request.Request(f"{SBURL}/rest/v1/progress?select=state&id=eq.bot_sessions&limit=1",
                                     headers={"apikey": SBKEY, "Authorization": f"Bearer {SBKEY}"})
        with urllib.request.urlopen(req, timeout=30) as r:
            d = json.loads(r.read().decode())
        return (d[0].get("state") or {}) if d else {}
    except Exception as e:
        print(f"[!] sb get fail: {str(e)[:80]}")
        return {}

def sb_save(state):
    body = json.dumps({"id": "bot_sessions", "state": state}).encode()
    req = urllib.request.Request(f"{SBURL}/rest/v1/progress",
                                 data=body,
                                 headers={"apikey": SBKEY, "Authorization": f"Bearer {SBKEY}",
                                          "Content-Type": "application/json",
                                          "Prefer": "resolution=merge-duplicates"},
                                 method="POST")
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.status

async def make_one(token, name):
    c = TelegramClient(StringSession(), AID, AHASH, connection_retries=2)
    await c.connect()
    await c.start(bot_token=token)
    me = await c.get_me()
    ss = c.session.save()
    await c.disconnect()
    print(f"  [ok] {name}: @{me.username} session len={len(ss)}", flush=True)
    return ss

async def main():
    print(f"[*] bots: {len(BOT_TOKENS)} | per_bot: {PER_BOT} | pause: {PAUSE}s", flush=True)
    state = sb_get()
    # tokens bhi store (file_id capture ke liye posting bot ka token chahiye)
    state["tokens"] = {f"bot{i+1}": tok for i, tok in enumerate(BOT_TOKENS)}
    sb_save(state)
    print(f"[*] existing sessions: {sum(len(v) for v in state.values() if isinstance(v, list))}", flush=True)
    for i, tok in enumerate(BOT_TOKENS):
        name = f"bot{i+1}"
        have = state.get(name) or []
        need = PER_BOT - len(have)
        if need <= 0:
            print(f"[*] {name}: already {len(have)} — skip", flush=True)
            continue
        print(f"[*] {name}: creating {need} new...", flush=True)
        for k in range(need):
            try:
                ss = await make_one(tok, name)
                have.append(ss)
                state[name] = have
                sb_save(state)
                print(f"  saved ({len(have)} total)", flush=True)
            except Exception as e:
                print(f"  [x] {name} create fail: {str(e)[:90]}", flush=True)
                break
            if k < need - 1:
                await asyncio.sleep(PAUSE)
        await asyncio.sleep(PAUSE)  # bots ke beech bhi pause
    print(f"\n[*] final: {sum(len(v) for v in state.values() if isinstance(v, list))} sessions saved", flush=True)
    print("[done]", flush=True)

asyncio.run(main())
