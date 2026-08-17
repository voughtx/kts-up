#!/usr/bin/env python3
"""pin_check.py — channel ke pinned messages scan karke count karo + poster messages identify.
Channel me har show ka poster pin hota hai (Total • Sx | EpX caption wala).
Count: pinned total + poster-pinned list. Koi mismatch ho to batao."""
import os, sys, asyncio, json, urllib.request

try:
    import cryptg  # noqa
except Exception:
    os.system(f"{sys.executable} -m pip install -q cryptg")

from telethon import TelegramClient
from telethon.sessions import StringSession

AID = int(os.environ.get("KEY_16", "0").strip())
AHASH = os.environ.get("KEY_17", "").strip()
CH = int(os.environ.get("KEY_2", "0").strip())
SBURL = os.environ.get("KEY_20", "").strip().rstrip("/")
SBKEY = os.environ.get("KEY_21", "").strip()

def sb_get(qs):
    url = f"{SBURL}/rest/v1/progress?{qs}"
    req = urllib.request.Request(url, headers={"apikey": SBKEY, "Authorization": f"Bearer {SBKEY}"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())

async def main():
    docs = sb_get("select=state&id=eq.bot_sessions&limit=1")
    state = (docs[0].get("state") or {}) if docs else {}
    bots = {k: v for k, v in state.items() if isinstance(v, list) and len(v) >= 2}
    if not bots:
        print("no bot sessions", flush=True)
        return
    ss = next(iter(bots.values()))[0]
    c = TelegramClient(StringSession(ss), AID, AHASH, connection_retries=2)
    await c.connect()
    print("connected", flush=True)
    ent = await c.get_entity(CH)
    print("channel:", getattr(ent, "title", CH), flush=True)
    pinned = []
    # saare pinned messages dhundho — reverse iterate (posters sabse purane)
    async for m in c.iter_messages(ent, reverse=True, limit=400):
        try:
            if m.pinned:
                pinned.append(m.id)
                cap = (m.message or "")[:80]
                print(f"  PIN #{m.id} | {cap!r}", flush=True)
        except Exception:
            continue
        if len(pinned) >= 200:
            break
    print("TOTAL pinned found:", len(pinned), flush=True)
    # poster-style caption wale pinned count (Total • S)
    posters = []
    async for m in c.iter_messages(ent, reverse=True, limit=600):
        try:
            if m.pinned and "Total" in (m.message or "") and "S" in (m.message or ""):
                posters.append(m.id)
        except Exception:
            continue
    print("pinned with 'Total • S' (posters):", len(posters), flush=True)
    print("pinned ids:", pinned, flush=True)
    await c.disconnect()

asyncio.run(main())
