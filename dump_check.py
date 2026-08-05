# dump_check.py — LIVE check: pinned message + top 20 + bottom 8 + counts
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
    # pinned
    try:
        pm = await app.get_chat(chat.id)
        if pm.pinned_message:
            m = pm.pinned_message
            print(f"PINNED: {m.id} | {'photo' if m.photo else ('doc' if m.document else '?')} | {(m.caption or '').replace(chr(10),' | ')[:80]}")
        else:
            print("PINNED: none")
    except Exception as e:
        print(f"PINNED err: {str(e)[:60]}")

    # top 20 (newest first)
    print("--- TOP 20 (newest->older) ---")
    async for m in app.get_chat_history(chat.id, limit=20):
        typ = "DOC" if m.document else ("PHOTO" if m.photo else ("TEXT" if m.text else ("SVC" if m.service else "?")))
        fname = m.document.file_name if m.document else ""
        cap = (m.caption or "").replace("\n", " | ")[:60] if m.caption else (m.text or "").replace("\n"," | ")[:60] if m.text else ""
        print(f"{m.id}\t{typ}\t{fname}\t{cap}")

    # bottom 8 (oldest)
    print("--- BOTTOM 8 (oldest) ---")
    mids = []
    async for m in app.get_chat_history(chat.id, limit=100):
        mids.append(m.id)
    oldest = sorted(mids)[:8]
    for mid in oldest:
        m = await app.get_messages(chat.id, mid)
        typ = "DOC" if m.document else ("PHOTO" if m.photo else ("TEXT" if m.text else ("SVC" if m.service else "?")))
        fname = m.document.file_name if m.document else ""
        cap = (m.caption or "").replace("\n", " | ")[:60] if m.caption else (m.text or "").replace("\n"," | ")[:60] if m.text else ""
        print(f"{m.id}\t{typ}\t{fname}\t{cap}")

    # counts
    cnt = 0
    docs = 0
    photos = 0
    async for m in app.get_chat_history(chat.id, limit=1000):
        cnt += 1
        if m.document: docs += 1
        elif m.photo: photos += 1
    print(f"=== TOTAL: {cnt} | docs: {docs} | photos: {photos} ===")
    await app.stop()

asyncio.run(main())
