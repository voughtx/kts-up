# bot_simple_test.py — EK bot ka isolated download test (forward peer pattern + debug)
import os, time, asyncio
from pyrogram import Client
from pyrogram.raw.functions.upload import GetFile
from pyrogram.raw.types import InputDocumentFileLocation
from pyrogram.utils import FileId

K2 = os.environ.get("KEY_2", "").strip()
PSESS = os.environ.get("KEY_19", "").strip()
AID = os.environ.get("KEY_16", "").strip()
AHASH = os.environ.get("KEY_17", "").strip()
BOT_SS = os.environ.get("KEY_32", "").strip()  # bot1 session
SRC_MID = int(os.environ.get("MIDS", "441").split(",")[0])
MB = 1024 * 1024

async def main():
    print(f"[*] bot session len: {len(BOT_SS)}")
    user = Client("usert", api_id=int(AID), api_hash=AHASH, session_string=PSESS, no_updates=True)
    await user.start()
    # user se channel resolve
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

    app = Client("btest", api_id=int(AID), api_hash=AHASH, session_string=BOT_SS, no_updates=True)
    await app.start()
    me = await app.get_me()
    print(f"[*] bot connected: @{me.username}")

    # STEP 1: get_chat direct
    try:
        ch = await app.get_chat(int(K2))
        print(f"[ok] get_chat direct: {ch.title}")
    except Exception as e:
        print(f"[!] get_chat direct fail: {str(e)[:60]}")
        # STEP 2: forward channel post -> bot DM
        try:
            fm = await user.forward_messages(me.username or "me", ucid, [SRC_MID])
            fm_id = fm[0].id if isinstance(fm, list) else fm.id
            print(f"[ok] forwarded to bot DM: {fm_id}")
        except Exception as e2:
            print(f"[!] forward fail: {str(e2)[:80]}")
        # STEP 3: bot apne DM se message uthao
        try:
            dm = await app.get_messages("me", fm_id)
            print(f"[ok] bot got DM msg: fwd_from_chat={'YES' if dm.forward_from_chat else 'NO'} fwd_from={'YES' if dm.forward_from else 'NO'}")
            if dm.forward_from_chat:
                fc = dm.forward_from_chat
                print(f"[dbg] fwd chat id={fc.id} type={getattr(fc, 'type', '?')}")
        except Exception as e3:
            print(f"[!] bot DM read fail: {str(e3)[:80]}")
        # STEP 4: get_chat phir try
        try:
            ch = await app.get_chat(int(K2))
            print(f"[ok] get_chat after forward: {ch.title}")
        except Exception as e4:
            print(f"[!] get_chat after forward fail: {str(e4)[:60]}")
            await user.stop()
            await app.stop()
            return
    cid = ch.id if hasattr(ch, "id") else ch

    # STEP 5: get_messages + download 5MB
    try:
        m = await app.get_messages(cid, SRC_MID)
        print(f"[ok] get_messages: doc={m.document is not None}")
    except Exception as e:
        print(f"[!] get_messages fail: {str(e)[:80]}")
        await user.stop()
        await app.stop()
        return
    if m.empty or not m.document:
        print("[!] no doc")
        await user.stop()
        await app.stop()
        return
    want = m.document.file_size
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
    await user.stop()
    await app.stop()

asyncio.run(main())
