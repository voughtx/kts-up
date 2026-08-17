#!/usr/bin/env python3
"""scan_msgs.py — channel messages 7840..7900 scan (metadata only):
id, date, media type, pinned, caption ka structure (pehle 40 chars — poster vs ep).
Episode messages ki captions me SxEx hoga. Poster me 'Total • S' hoga."""
import os, sys, asyncio, json

try:
    import cryptg  # noqa
except Exception:
    os.system(f"{sys.executable} -m pip install -q cryptg")

from telethon import TelegramClient
from telethon.sessions import StringSession

AID = int(os.environ.get("KEY_16", "0").strip())
AHASH = os.environ.get("KEY_17", "").strip()
CH = int(os.environ.get("KEY_2", "0").strip())

async def main():
    ss = os.environ.get("KEY_18", "").strip()
    if not ss:
        print("no user session", flush=True)
        return
    c = TelegramClient(StringSession(ss), AID, AHASH, connection_retries=2)
    await c.connect()
    ent = await c.get_entity(CH)
    # iterate from msg 7840 to 7900
    for mid in range(7840, 7901):
        try:
            m = await c.get_messages(ent, ids=mid)
            if m is None:
                print(f"{mid} | (none)", flush=True)
                continue
            cap = (m.message or "")[:42].replace("\n", " ⏎ ")
            has_photo = bool(getattr(m, "photo", None))
            has_doc = bool(getattr(m, "document", None))
            has_video = bool(getattr(m, "video", None))
            typ = "photo" if has_photo else ("video" if has_video else ("doc" if has_doc else "text"))
            pin = "PIN" if m.pinned else ""
            grp = getattr(m, "grouped_id", None)
            print(f"{mid} | {typ:5} | {pin:3} | grp={str(grp)[:8] if grp else '--'} | {cap!r}", flush=True)
        except Exception as e:
            print(f"{mid} | ERR {str(e)[:60]}", flush=True)
        await asyncio.sleep(0.15)
    await c.disconnect()
    print("[done]", flush=True)

asyncio.run(main())
