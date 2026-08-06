# bot1_test.py — SIRF EK BOT (bot1, session KEY_32) — teldrive-style access_hash test
# User session channel ka access_hash nikalta hai -> bot usse InputPeerChannel banata hai
# -> bot apna fresh file_reference leta hai -> GetFile (download)
import os, time, asyncio
from pyrogram import Client
from pyrogram.raw.functions.upload import GetFile
from pyrogram.raw.types import InputDocumentFileLocation, InputPeerChannel
from pyrogram.raw.functions.messages import GetMessages as RawGetMessages
from pyrogram.raw.types import InputMessageID
from pyrogram.utils import FileId

K2 = os.environ.get("KEY_2", "").strip()
PSESS = os.environ.get("KEY_19", "").strip()
AID = os.environ.get("KEY_16", "").strip()
AHASH = os.environ.get("KEY_17", "").strip()
BOT1_SS = os.environ.get("KEY_32", "").strip()  # sirf bot1
SRC_MID = int(os.environ.get("MIDS", "441").split(",")[0])
MB = 1024 * 1024

async def main():
    print(f"[*] bot1 session len: {len(BOT1_SS)}")

    # ==== USER SESSION: channel resolve + access_hash nikalo ====
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
    channel_id = uchat.id if hasattr(uchat, "id") else uchat
    access_hash = getattr(uchat, "access_hash", None)
    print(f"[*] user chat: {uchat.title} | id: {channel_id} | access_hash: {'YES' if access_hash else 'NO'}")

    # ==== BOT1: session string se connect (koi re-auth nahi) ====
    bot = Client("b1", api_id=int(AID), api_hash=AHASH, session_string=BOT1_SS, no_updates=True)
    await bot.start()
    me = await bot.get_me()
    print(f"[*] bot1 connected: @{me.username}")

    # ==== TEST A: get_chat direct ====
    try:
        ch = await bot.get_chat(int(K2))
        print(f"[A] get_chat direct: OK {ch.title}")
    except Exception as e:
        print(f"[A] get_chat direct FAIL: {str(e)[:60]}")

    # ==== TEST B: access_hash se raw InputPeerChannel + GetMessages ====
    try:
        peer = InputPeerChannel(channel_id=int(str(channel_id).replace("-100", "")), access_hash=access_hash)
        r = await bot.invoke(RawGetMessages(peer=peer, id=[InputMessageID(id=SRC_MID)]))
        msgs = r.messages
        if msgs:
            m0 = msgs[0]
            doc = getattr(m0, "document", None)
            print(f"[B] raw GetMessages: OK (type={type(m0).__name__}, doc={'YES' if doc else 'NO'})")
            if doc:
                # bot ka fresh file_reference + access_hash
                from pyrogram.raw.types import Document
                d = doc if isinstance(doc, Document) else doc
                fref = bytes(d.file_reference) if hasattr(d, "file_reference") else b""
                daccess = d.access_hash
                did = d.id
                print(f"[B] doc id={did} access_hash={'YES'} fref_len={len(fref)}")
                # GetFile 5MB test
                loc = InputDocumentFileLocation(id=did, access_hash=daccess, file_reference=fref, thumb_size="")
                off = 0
                got = 0
                t0 = time.time()
                try:
                    while off < 5 * MB:
                        res = await bot.invoke(GetFile(location=loc, offset=off, limit=MB, precise=1, cdn_supported=True))
                        data = res.bytes
                        if not data:
                            print(f"[B] empty at {off}")
                            break
                        got += len(data)
                        off += len(data)
                    dt = time.time() - t0
                    print(f"[B] download: {got/MB:.1f} MB in {dt:.1f}s = {got/dt/MB:.2f} MB/s")
                except Exception as e:
                    print(f"[B] GetFile FAIL: {str(e)[:100]}")
        else:
            print(f"[B] raw GetMessages: no messages")
    except Exception as e:
        print(f"[B] raw GetMessages FAIL: {str(e)[:100]}")

    await user.stop()
    await bot.stop()
    print("[done]")

asyncio.run(main())
