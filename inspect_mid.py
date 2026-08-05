# inspect_mid.py — given mids, print full caption + doc info
import os, asyncio, sys
from pyrogram import Client

K2 = os.environ.get("KEY_2", "").strip()
PSESS = os.environ.get("KEY_19", "").strip()
AID = os.environ.get("KEY_16", "").strip()
AHASH = os.environ.get("KEY_17", "").strip()
MIDS = [int(x) for x in os.environ.get("MIDS", "451").split(",") if x.strip()]

async def main():
    app = Client("inspsess", session_string=PSESS, api_id=int(AID) if AID else None,
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
    for mid in MIDS:
        try:
            m = await app.get_messages(chat.id, mid)
            print(f"===== mid {mid} =====")
            print("file:", m.document.file_name if m.document else None)
            print("size:", (m.document.file_size if m.document else 0) / (1024*1024), "MB")
            print("--- caption ---")
            print(m.caption)
            print("-----")
        except Exception as e:
            print(f"mid {mid}: err {str(e)[:60]}")
    await app.stop()

asyncio.run(main())
