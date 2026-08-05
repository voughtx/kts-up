# copy_test.py — 1 message copy (mid 77) verify: forward tag? caption? phir delete
import os, asyncio
from pyrogram import Client, enums

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
    print("chat:", chat.title if chat else None)
    if chat:
        m = await app.copy_message(chat.id, chat.id, 77, caption="TEST COPY <b>bold</b>", parse_mode=enums.ParseMode.HTML)
        print("copied mid:", m.id)
        print("forward_origin:", m.forward_origin)
        print("document:", m.document.file_name if m.document else None)
        print("caption:", m.caption)
        await app.delete_messages(chat.id, m.id)
        print("test copy deleted")
    await app.stop()

asyncio.run(main())
