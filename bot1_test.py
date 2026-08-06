# bot1_test.py v3 — forward (peer register) + access_hash + channels.GetMessages + GetFile
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

    # user se channel resolve (peer)
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
    channel_num = int(str(K2).replace("-100", ""))

    # raw dialogs se access_hash
    access_hash = None
    try:
        r = await user.invoke(GetDialogs(offset_date=0, offset_id=0, offset_peer=InputPeerEmpty(), limit=200, hash=0))
        for c in r.chats:
            if isinstance(c, Channel) and c.id == channel_num:
                access_hash = c.access_hash
                print(f"[*] channel raw: id={c.id} access_hash={'YES' if access_hash else 'NO'}")
                break
    except Exception as e:
        print(f"[!] GetDialogs fail: {str(e)[:60]}")
    if access_hash is None:
        await user.stop()
        return

    bot = Client("b1", api_id=int(AID), api_hash=AHASH, session_string=BOT1_SS, no_updates=True)
    await bot.start()
    me = await bot.get_me()
    print(f"[*] bot1 connected: @{me.username}")

    # STEP 1: channel post -> bot DM forward (peer register)
    try:
        fm = await user.forward_messages(me.username or "me", ucid, [SRC_MID])
        print(f"[1] forwarded to bot DM OK")
    except Exception as e:
        print(f"[1] forward fail: {str(e)[:70]}")
    await asyncio.sleep(2)

    # STEP 2: get_chat direct (ab kaam karna chahiye?)
    got_peer = False
    try:
        ch = await bot.get_chat(int(K2))
        print(f"[2] get_chat: OK {ch.title}")
        got_peer = True
    except Exception as e:
        print(f"[2] get_chat FAIL: {str(e)[:50]}")

    # STEP 3: channels.GetMessages (access_hash se) — dono tarike try
    doc_info = None
    for attempt in (1, 2):
        try:
            r = await bot.invoke(ChannelsGetMessages(
                channel=InputChannel(channel_id=channel_num, access_hash=access_hash),
                id=[InputMessageID(id=SRC_MID)],
            ))
            msgs = r.messages
            if msgs:
                m0 = msgs[0]
                doc = getattr(m0, "document", None)
                if doc:
                    doc_info = (doc.id, doc.access_hash, bytes(doc.file_reference))
                    print(f"[3] channels.GetMessages OK (doc id={doc.id} fref_len={len(doc_info[2])})")
                    break
                else:
                    print(f"[3] msg mila par doc nahi (type={type(m0).__name__})")
            else:
                print("[3] no messages")
        except Exception as e:
            print(f"[3] channels.GetMessages attempt {attempt} FAIL: {str(e)[:80]}")
            await asyncio.sleep(2)
            # retry se pehle forward dobara
            try:
                await user.forward_messages(me.username or "me", ucid, [SRC_MID])
                print(f"    re-forwarded")
            except Exception:
                pass
            await asyncio.sleep(2)

    # STEP 4: GetFile download 5MB
    if doc_info:
        loc = InputDocumentFileLocation(id=doc_info[0], access_hash=doc_info[1], file_reference=doc_info[2], thumb_size="")
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
    else:
        print("[4] skip — doc nahi mila")

    await user.stop()
    await bot.stop()
    print("[done]")

asyncio.run(main())
