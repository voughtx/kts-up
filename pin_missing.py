#!/usr/bin/env python3
"""pin_missing.py — missing posters send + pin (Beyblade HUNGAMA, Kick Buttowski).
User session (KEY_18) se channel pe poster image bhejo + pin karo.
Caption format: <b>Title</b>\nTotal • S{seasons} | Ep{total} (app jaisa)."""
import os, sys, asyncio, json, urllib.request

try:
    import cryptg  # noqa
except Exception:
    os.system(f"{sys.executable} -m pip install -q cryptg")

from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.types import InputPeerChannel, DocumentAttributeFilename

AID = int(os.environ.get("KEY_16", "0").strip())
AHASH = os.environ.get("KEY_17", "").strip()
CH = int(os.environ.get("KEY_2", "0").strip())
SBURL = os.environ.get("KEY_20", "").strip().rstrip("/")
SBKEY = os.environ.get("KEY_21", "").strip()

TARGETS = [
    {"id": "688c932afef9b1290056ea0b", "name": "Beyblade (HUNGAMA)", "seasons": 3, "total": 154},
    {"id": "69d1e50e6e1f7f50c4bb0f40", "name": "Kick Buttowski: Suburban Daredevil", "seasons": 2, "total": 52},
]

def sb_get(qs):
    url = f"{SBURL}/rest/v1/progress?{qs}"
    req = urllib.request.Request(url, headers={"apikey": SBKEY, "Authorization": f"Bearer {SBKEY}"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())

async def main():
    docs = sb_get("select=state&id=eq.showlist&limit=1")
    state = (docs[0].get("state") or {}) if docs else {}
    shows = state.get("shows") or []
    ss = os.environ.get("KEY_18", "").strip()
    if not ss:
        print("no user session KEY_18", flush=True)
        return
    c = TelegramClient(StringSession(ss), AID, AHASH, connection_retries=2)
    await c.connect()
    print("connected", flush=True)
    ent = await c.get_entity(CH)
    print("channel:", getattr(ent, "title", CH), flush=True)

    for t in TARGETS:
        show = next((s for s in shows if s.get("id") == t["id"]), None)
        poster = (show or {}).get("poster") or ""
        if not poster:
            print(f"SKIP {t['name']}: no poster", flush=True)
            continue
        # download poster
        try:
            req = urllib.request.Request(poster, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=40) as r:
                data = r.read()
            tmp = f"/tmp/poster_{t['id']}.jpg"
            open(tmp, "wb").write(data)
            print(f"{t['name']}: poster downloaded {len(data)}B", flush=True)
        except Exception as e:
            print(f"{t['name']}: dl fail {str(e)[:60]}", flush=True)
            continue
        cap = f"<b>{t['name']}</b>\nTotal \u2022 S{t['seasons']} | Ep{t['total']}"
        try:
            msg = await c.send_file(ent, tmp, caption=cap, parse_mode="html",
                                    attributes=[DocumentAttributeFilename(file_name="poster.jpg")])
            await c.pin_message(ent, msg.id)
            print(f"PINNED #{msg.id} | {t['name']}", flush=True)
        except Exception as e:
            print(f"{t['name']}: send/pin fail {str(e)[:80]}", flush=True)
        await asyncio.sleep(2)
    await c.disconnect()
    print("[done]", flush=True)

asyncio.run(main())
