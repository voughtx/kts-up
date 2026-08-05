# inspect_other.py — "other" type messages ka detail (194, 40, 198, 1)
import os, asyncio, json
from pyrogram import Client

K2 = os.environ.get("KEY_2", "").strip()
PSESS = os.environ.get("KEY_19", "").strip()
AID = os.environ.get("KEY_16", "").strip()
AHASH = os.environ.get("KEY_17", "").strip()

async def main():
    app = Client("testsess", session_string=PSESS, api_id=int(AID) if AID else None,
                 api_hash=AHASH or None, no_updates=True)
    await app.start()
    chat = None
    try:
        chat = await app.get_chat(int(K2))
    except Exception:
        async for d in app.get_dialogs():
            if d.chat and d.chat.id == int(K2):
                chat = d.chat
                break
    if chat:
        for mid in [1, 40, 41, 194, 198, 199]:
            try:
                m = await app.get_messages(chat.id, mid)
                print(f"--- mid {mid} ---")
                print("  type:", m.__class__.__name__, "| empty:", m.empty)
                print("  text:", repr(m.text)[:80] if m.text else None)
                print("  caption:", repr(m.caption)[:80] if m.caption else None)
                print("  service:", m.service if hasattr(m, "service") else None, "| action:", m.action if hasattr(m, "action") else None)
                print("  media:", m.media if hasattr(m, "media") else None)
                print("  date:", m.date)
            except Exception as e:
                print(f"mid {mid}: err {str(e)[:60]}")
    await app.stop()

asyncio.run(main())
