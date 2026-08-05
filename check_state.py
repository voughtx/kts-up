# check_state.py — msg 199 status + channel top 12 messages (mid, caption head, doc?)
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
        try:
            m = await app.get_messages(chat.id, 199)
            print("msg199:", m.id, "| caption:", (m.caption or "")[:40] if m.caption else None, "| doc:", m.document.file_name if m.document else None)
        except Exception as e:
            print("msg199 err:", str(e)[:60])
        print("--- top 12 ---")
        async for m in app.get_chat_history(chat.id, limit=12):
            cap = (m.caption or "").replace("\n", " | ")[:60] if m.caption else ""
            print(m.id, "|", m.document.file_name if m.document else ("photo" if m.photo else "?"), "|", cap)
    await app.stop()

asyncio.run(main())
