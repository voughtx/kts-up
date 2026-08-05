# dump_all.py — channel ke HAR EK message ka dump: mid | type | fname | caption (full)
import os, asyncio
from pyrogram import Client

K2 = os.environ.get("KEY_2", "").strip()
PSESS = os.environ.get("KEY_19", "").strip()
AID = os.environ.get("KEY_16", "").strip()
AHASH = os.environ.get("KEY_17", "").strip()

async def main():
    app = Client("dumpsess", session_string=PSESS, api_id=int(AID) if AID else None,
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
    if chat is None:
        print("[x] chat fail")
        await app.stop()
        return
    print(f"=== CHANNEL: {chat.title} ({chat.id}) ===")
    count = 0
    async for m in app.get_chat_history(chat.id, limit=1000):
        count += 1
        if m.service:
            typ = "SERVICE:" + str(m.service)
        elif m.document:
            typ = "DOC"
        elif m.photo:
            typ = "PHOTO"
        elif m.text:
            typ = "TEXT"
        else:
            typ = "?"
        fname = m.document.file_name if m.document else ""
        cap = (m.caption or "") if m.caption else ""
        cap1 = cap.replace("\n", " | ")
        print(f"{m.id}\t{typ}\t{fname}\t{cap1}")
        if count > 500:
            break
    print(f"=== TOTAL: {count} ===")
    await app.stop()

asyncio.run(main())
