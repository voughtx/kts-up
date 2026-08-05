# check_state2.py — full channel state: count, first/last mids, specific mids exist?
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
        # count + collect mids
        mids = []
        async for m in app.get_chat_history(chat.id, limit=500):
            mids.append(m.id)
            if len(mids) > 400:
                break
        print("history count:", len(mids))
        if mids:
            print("first 5:", mids[:5])
            print("last 5:", mids[-5:])
        # specific mids
        for mid in [39, 77, 178, 197, 199]:
            try:
                m = await app.get_messages(chat.id, mid)
                if m.empty:
                    print(f"mid {mid}: EMPTY/deleted")
                else:
                    print(f"mid {mid}: exists | doc:", (m.document.file_name if m.document else None), "| cap:", ((m.caption or "").replace(chr(10)," ")[:40] if m.caption else None))
            except Exception as e:
                print(f"mid {mid}: err {str(e)[:50]}")
    await app.stop()

asyncio.run(main())
