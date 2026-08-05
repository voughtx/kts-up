# cleanup_test.py — channel se test message (mid 199, caption "TEST COPY") delete karo
import os, asyncio
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
        # saare "TEST COPY" wale messages dhundo + delete
        cnt = 0
        async for m in app.get_chat_history(chat.id, limit=300):
            cap = (m.caption or "").strip() if m.caption else ""
            if cap.startswith("TEST COPY"):
                await app.delete_messages(chat.id, m.id)
                print("deleted test msg:", m.id)
                cnt += 1
        if cnt == 0:
            print("koi TEST COPY msg nahi mila (pehle hi delete ho gaya?)")
    await app.stop()

asyncio.run(main())
