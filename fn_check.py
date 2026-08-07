# fn_check.py — channel ke last 6 messages ke filenames check (.mp4?)
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
        fn = ""
        if m.document and m.document.attributes:
            for a in m.document.attributes:
                if hasattr(a, "file_name") and a.file_name:
                    fn = a.file_name
                    break
        elif m.video:
            fn = "(video)"
        mp4 = "✅ .mp4" if fn.lower().endswith(".mp4") else ("❌ NO .mp4" if fn else "(no name)")
        print(f"{m.id} | {fn[:60]} | {mp4}", flush=True)
    await c.disconnect()
    print("[done]", flush=True)

asyncio.run(main())
