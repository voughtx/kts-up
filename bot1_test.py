# bot1_test.py v5 — bot updates ENABLED (no_updates=False) + wait -> peer register -> GetFile
import os, time, asyncio
from pyrogram import Client
from pyrogram.raw.functions.upload import GetFile
from pyrogram.raw.types import InputDocumentFileLocation
from pyrogram.utils import FileId
from pyrogram import filters

K2 = os.environ.get("KEY_2", "").strip()
PSESS = os.environ.get("KEY_19", "").strip()
AID = os.environ.get("KEY_16", "").strip()
AHASH = os.environ.get("KEY_17", "").strip()
BOT1_TOKEN = os.environ.get("KEY_22", "").strip()
SRC_MID = int(os.environ.get("MIDS", "441").split(",")[0])
MB = 1024 * 1024

async def main():
    print(f"[*] bot1 token len: {len(BOT1_TOKEN)}")
    user = Client("u1", api_id=int(AID), api_hash=AHASH, session_string=PSESS, no_updates=True)
    await user.start()
    try:
        uchat = await user.get_chat(int(K2))
    except Exception:
        uchat = None
        async for d in user.get_dialogs():
            if d.chat and d.chat.id == int(K2):
                uchat = d.chat
                break
    if uchat is None:
        print("[!] user chat fail")
        await user.stop()
        return
    ucid = uchat.id if hasattr(uchat, "id") else uchat
    print(f"[*] user chat: {uchat.title}")

    # bot1 — updates ENABLED (peer register hone de)
    bot = Client("b1u", api_id=int(AID), api_hash=AHASH, bot_token=BOT1_TOKEN)
    await bot.start()
    me = await bot.get_me()
    print(f"[*] bot1 connected (updates ON): @{me.username}")

    # user se channel post bot ke DM forward karo (update trigger)
    try:
        fm = await user.forward_messages(me.username or "me", ucid, [SRC_MID])
        print(f"[1] forward OK")
    except Exception as e:
        print(f"[1] forward fail: {str(e)[:70]}")

    # updates process hone ka wait (2 round)
    for w in (5, 10):
        print(f"[*] waiting {w}s for updates...")
        await asyncio.sleep(w)
        try:
            ch = await bot.get_chat(int(K2))
            print(f"[2] get_chat: OK {ch.title}")
            break
        except Exception as e:
            print(f"[2] get_chat FAIL after {w}s: {str(e)[:50]}")
    else:
        await user.stop()
        await bot.stop()
        return

    cid = ch.id if hasattr(ch, "id") else ch
    try:
        m = await bot.get_messages(cid, SRC_MID)
        print(f"[3] get_messages: doc={m.document is not None}")
    except Exception as e:
        print(f"[3] get_messages FAIL: {str(e)[:60]}")
        await user.stop()
        await bot.stop()
        return
    if m.empty or not m.document:
        print("[3] no doc")
        await user.stop()
        await bot.stop()
        return

    fid = FileId.decode(m.document.file_id)
    loc = InputDocumentFileLocation(id=fid.media_id, access_hash=fid.access_hash,
                                    file_reference=fid.file_reference or b"", thumb_size="")
    off, got, t0 = 0, 0, time.time()
    try:
        while off < 5 * MB:
            res = await bot.invoke(GetFile(location=loc, offset=off, limit=MB, precise=1, cdn_supported=True))
            data = res.bytes
            if not data:
                print(f"[4] empty at {off}")
                break
            got += len(data)
            off += len(data)
        dt = time.time() - t0
        print(f"[4] download: {got/MB:.1f} MB in {dt:.1f}s = {got/dt/MB:.2f} MB/s")
    except Exception as e:
        print(f"[4] GetFile FAIL: {str(e)[:100]}")

    await user.stop()
    await bot.stop()
    print("[done]")

asyncio.run(main())
