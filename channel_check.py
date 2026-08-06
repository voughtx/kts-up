# channel_check.py — channel ke last 8 messages (thumb verify)
import os, sys, asyncio

try:
    import cryptg  # noqa
except Exception:
    os.system(f"{sys.executable} -m pip install -q cryptg")

from telethon import TelegramClient
from telethon.sessions import StringSession

CHAT = os.environ.get("KEY_2", "").strip()
AID = int(os.environ.get("KEY_16", "0").strip())
AHASH = os.environ.get("KEY_17", "").strip()
SS = os.environ.get("KEY_18", "").strip()

async def main():
    c = TelegramClient(StringSession(SS), AID, AHASH)
    await c.connect()
    ch = await c.get_entity(int(CHAT))
    msgs = await c.get_messages(ch, limit=8)
    msgs = sorted(msgs, key=lambda m: m.id)
    for m in msgs:
        mt = "?"
        fn = ""
        th = ""
        if m.document:
            mt = "doc"
            fn = m.document.attributes[0].file_name if m.document.attributes else ""
            th = "thumb" if m.document.thumbs else "NO-THUMB"
        elif m.text:
            mt = "TEXT"
        print(f"{m.id} | {mt} | {fn[:55]} | {th} | {(m.message or '')[:40]}", flush=True)
    await c.disconnect()
    print("[done]", flush=True)

asyncio.run(main())
