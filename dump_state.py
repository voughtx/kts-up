# dump_state.py — channel ke saare messages ka full dump (mid, type, doc, caption head)
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
        print("chat:", chat.title, chat.id)
        lines = []
        async for m in app.get_chat_history(chat.id, limit=500):
            typ = "doc" if m.document else ("photo" if m.photo else ("empty" if m.empty else "other"))
            fname = m.document.file_name if m.document else ""
            cap = ((m.caption or "").replace("\n", " | ")[:50] if m.caption else "")
            lines.append(f"{m.id}\t{typ}\t{fname}\t{cap}")
        print("TOTAL:", len(lines))
        for ln in lines:
            print(ln)
    await app.stop()

asyncio.run(main())
