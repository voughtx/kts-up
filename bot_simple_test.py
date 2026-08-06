# bot_simple_test.py — EK bot ka isolated download test (debug)
import os, time, asyncio
from pyrogram import Client
from pyrogram.raw.functions.upload import GetFile
from pyrogram.raw.types import InputDocumentFileLocation
from pyrogram.utils import FileId

K2 = os.environ.get("KEY_2", "").strip()
AID = os.environ.get("KEY_16", "").strip()
AHASH = os.environ.get("KEY_17", "").strip()
BOT_SS = os.environ.get("KEY_32", "").strip()  # bot1 session
SRC_MID = int(os.environ.get("MIDS", "441").split(",")[0])
MB = 1024 * 1024

async def main():
    print(f"[*] bot session len: {len(BOT_SS)}")
    app = Client("btest", api_id=int(AID), api_hash=AHASH, session_string=BOT_SS, no_updates=True)
    await app.start()
    me = await app.get_me()
    print(f"[*] connected as @{me.username} (bot={me.is_bot})")
    # 1. get_chat
    try:
        ch = await app.get_chat(int(K2))
        print(f"[ok] get_chat: {ch.title}")
    except Exception as e:
        print(f"[!] get_chat fail: {str(e)[:80]}")
        await app.stop()
        return
    cid = ch.id if hasattr(ch, "id") else ch
    # 2. get_messages
    try:
        m = await app.get_messages(cid, SRC_MID)
        print(f"[ok] get_messages: empty={m.empty} doc={m.document is not None}")
    except Exception as e:
        print(f"[!] get_messages fail: {str(e)[:80]}")
        await app.stop()
        return
    if m.empty or not m.document:
        print("[!] no doc")
        await app.stop()
        return
    want = m.document.file_size
    # 3. download 5MB range with 1 worker
    fid = FileId.decode(m.document.file_id)
    loc = InputDocumentFileLocation(id=fid.media_id, access_hash=fid.access_hash,
                                    file_reference=fid.file_reference or b"", thumb_size="")
    off = 0
    got = 0
    t0 = time.time()
    try:
        while off < 5 * MB:
            res = await app.invoke(GetFile(location=loc, offset=off, limit=MB, precise=1, cdn_supported=True))
            data = res.bytes
            if not data:
                print("[!] empty data at", off)
                break
            got += len(data)
            off += len(data)
        dt = time.time() - t0
        print(f"[ok] downloaded {got/MB:.1f} MB in {dt:.1f}s = {got/dt/MB:.2f} MB/s")
    except Exception as e:
        print(f"[!] download fail: {str(e)[:100]}")
    await app.stop()

asyncio.run(main())
