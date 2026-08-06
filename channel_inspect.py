# channel_inspect.py — channel messages 515-585 ka detail dump
# (user ne bola: 536-555 mein testing/S10, 557-573 sahi order but no thumb, 572 status msg)
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
    print(f"[*] chat: {getattr(ch, 'title', ch)}", flush=True)
    msgs = await c.get_messages(ch, min_id=300, max_id=585)
    msgs = sorted(msgs, key=lambda m: m.id)
    for m in msgs:
        mt = "?"
        fn = ""
        th = ""
        sz = ""
        if m.document:
            mt = "doc"
            fn = m.document.attributes[0].file_name if m.document.attributes else ""
            th = "thumb" if m.document.thumbs else "no-thumb"
            sz = f"{m.document.size/1024/1024:.0f}MB"
        elif m.video:
            mt = "video"
            th = "thumb" if m.video.thumbs else "no-thumb"
            sz = f"{m.video.size/1024/1024:.0f}MB"
        elif m.photo:
            mt = "photo"
        elif m.text:
            mt = "text"
        cap = (m.message or "")[:70].replace("\n", " | ")
        if mt == "text":
                print(f"{m.id} | TEXT | {cap}", flush=True)
            else:
                print(f"{m.id} | {mt} | {fn} | {th} | {sz} | {cap}", flush=True)
    await c.disconnect()
    print("[done]", flush=True)

asyncio.run(main())
