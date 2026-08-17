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
    out = []
    for mid in range(7852, 7877):
        try:
            m = await c.get_messages(ent, ids=mid)
            if m is None:
                out.append(f"=== msg {mid} ===\n(none)")
                continue
            cap = (m.message or "")
            typ = "photo" if getattr(m,"photo",None) else ("video" if getattr(m,"video",None) else ("doc" if getattr(m,"document",None) else "text"))
            pin = " [PINNED]" if m.pinned else ""
            out.append(f"=== msg {mid} | {typ}{pin} ===\n{cap}\n")
        except Exception as e:
            out.append(f"=== msg {mid} | ERR {str(e)[:60]} ===\n")
        await asyncio.sleep(0.12)
    # write to workspace file (user reads it — not me)
    with open("/home/user/captions_7852_7876.txt", "w") as f:
        f.write("\n".join(out))
    print("written captions file", flush=True)
    await c.disconnect()
    print("[done]", flush=True)

asyncio.run(main())
