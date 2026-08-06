# bot1_test.py — SIRF EK BOT (bot1, session KEY_32) — teldrive-style access_hash test v2
# User session raw dialogs se channel ka access_hash nikalta hai
# Bot channels.GetMessages (InputChannel) se apna fresh file_reference leta hai -> GetFile
import os, time, asyncio
from pyrogram import Client
from pyrogram.raw.functions.upload import GetFile
from pyrogram.raw.types import InputDocumentFileLocation, InputChannel, InputMessageID, Channel
from pyrogram.raw.functions.messages import GetDialogs
from pyrogram.raw.functions.channels import GetMessages as ChannelsGetMessages
from pyrogram.raw.types import InputPeerEmpty

K2 = os.environ.get("KEY_2", "").strip()
PSESS = os.environ.get("KEY_19", "").strip()
AID = os.environ.get("KEY_16", "").strip()
AHASH = os.environ.get("KEY_17", "").strip()
BOT1_SS = os.environ.get("KEY_32", "").strip()
SRC_MID = int(os.environ.get("MIDS", "441").split(",")[0])
MB = 1024 * 1024

async def main():
    print(f"[*] bot1 session len: {len(BOT1_SS)}")
    user = Client("u1", api_id=int(AID), api_hash=AHASH, session_string=PSESS, no_updates=True)
    await user.start()

    # raw dialogs se channel access_hash
    access_hash = None
    channel_num = int(str(K2).replace("-100", ""))
    try:
        r = await user.invoke(GetDialogs(offset_date=0, offset_id=0, offset_peer=InputPeerEmpty(), limit=200, hash=0))
        for c in r.chats:
            if isinstance(c, Channel) and c.id == channel_num:
                access_hash = c.access_hash
                print(f"[*] channel raw found: id={c.id} access_hash={'YES' if access_hash else 'NO'}")
                break
        if access_hash is None:
            print("[!] channel raw dialogs mein nahi mila")
    except Exception as e:
        print(f"[!] GetDialogs fail: {str(e)[:80]}")
    await user.stop()
    if access_hash is None:
        return

    bot = Client("b1", api_id=int(AID), api_hash=AHASH, session_string=BOT1_SS, no_updates=True)
    await bot.start()
    me = await bot.get_me()
    print(f"[*] bot1 connected: @{me.username}")

    # A: get_chat direct (expected fail — record)
    try:
        ch = await bot.get_chat(int(K2))
        print(f"[A] get_chat direct: OK {ch.title}")
    except Exception as e:
        print(f"[A] get_chat direct FAIL: {str(e)[:50]}")

    # B: channels.GetMessages with InputChannel (access_hash user se)
    try:
        r = await bot.invoke(ChannelsGetMessages(
            channel=InputChannel(channel_id=channel_num, access_hash=access_hash),
            id=[InputMessageID(id=SRC_MID)],
        ))
        msgs = r.messages
        if msgs:
            m0 = msgs[0]
            doc = getattr(m0, "document", None)
            print(f"[B] channels.GetMessages OK (msg_type={type(m0).__name__}, doc={'YES' if doc else 'NO'})")
            if doc:
                fref = bytes(doc.file_reference) if hasattr(doc, "file_reference") else b""
                print(f"[B] doc id={doc.id} ah={'YES'} fref_len={len(fref)}")
                loc = InputDocumentFileLocation(id=doc.id, access_hash=doc.access_hash,
                                                file_reference=fref, thumb_size="")
                off, got, t0 = 0, 0, time.time()
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
            print("[B] channels.GetMessages: no messages")
    except Exception as e:
        print(f"[B] channels.GetMessages FAIL: {str(e)[:100]}")

    await bot.stop()
    print("[done]")

asyncio.run(main())
