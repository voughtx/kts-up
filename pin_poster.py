# pin_poster.py — HUNGAMA poster (442) pin karo (naya show ka poster pin)
import os, asyncio
from pyrogram import Client

K2 = os.environ.get("KEY_2", "").strip()
PSESS = os.environ.get("KEY_19", "").strip()
AID = os.environ.get("KEY_16", "").strip()
AHASH = os.environ.get("KEY_17", "").strip()
MID = int(os.environ.get("PIN_MID", "442"))

async def main():
    app = Client("pinsess", session_string=PSESS, api_id=int(AID) if AID else None,
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
    m = await app.get_messages(chat.id, MID)
    if m.empty:
        print(f"[!] mid {MID} EMPTY")
        await app.stop()
        return
    try:
        await app.pin_chat_message(chat.id, MID)
        print(f"[ok] pinned {MID}: {(m.caption or '').replace(chr(10),' | ')[:60]}")
    except Exception as e:
        print(f"[!] pin fail: {str(e)[:80]}")
    # verify
    try:
        c = await app.get_chat(chat.id)
        pm = c.pinned_message
        print(f"[verify] pinned now: {pm.id if pm else 'none'}")
    except Exception as e:
        print(f"[verify] err: {str(e)[:50]}")
    await app.stop()

asyncio.run(main())
