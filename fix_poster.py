# fix_poster.py — poster captions exact format mein edit (in-place, no copy)
# 362: Doraemon (CLASSIC)\nTotal: S1 | E77
# 284: Doraemon (HUNGAMA)\nTotal • S22 | Ep1095
import os, asyncio
from pyrogram import Client, enums

K2 = os.environ.get("KEY_2", "").strip()
PSESS = os.environ.get("KEY_19", "").strip()
AID = os.environ.get("KEY_16", "").strip()
AHASH = os.environ.get("KEY_17", "").strip()

EDITS = {
    362: "Doraemon (CLASSIC)\nTotal: S1 | E77",
    284: "Doraemon (HUNGAMA)\nTotal \u2022 S22 | Ep1095",
}

async def main():
    app = Client("fixsess", session_string=PSESS, api_id=int(AID) if AID else None,
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
    for mid, cap in EDITS.items():
        try:
            m = await app.get_messages(chat.id, mid)
            if m.empty:
                print(f"[!] mid {mid} EMPTY")
                continue
            await app.edit_message_caption(chat.id, mid, cap, parse_mode=enums.ParseMode.HTML)
            print(f"[ok] {mid} caption updated")
        except Exception as e:
            print(f"[!] {mid} fail: {str(e)[:80]}")
        await asyncio.sleep(0.5)
    # verify
    for mid in EDITS:
        try:
            m = await app.get_messages(chat.id, mid)
            print(f"verify {mid}: {(m.caption or '').replace(chr(10),' | ')}")
        except Exception as e:
            print(f"verify {mid}: err {str(e)[:40]}")
    await app.stop()

asyncio.run(main())
