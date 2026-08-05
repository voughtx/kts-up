# bot_peer_cache.py — channel ki ek post har bot ko forward karo (peer cache)
# Bot private channel ko tabhi resolve kar sakta hai jab usne kabhi us channel ka message dekha ho
import os, asyncio
from pyrogram import Client

K2 = os.environ.get("KEY_2", "").strip()
PSESS = os.environ.get("KEY_19", "").strip()
AID = os.environ.get("KEY_16", "").strip()
AHASH = os.environ.get("KEY_17", "").strip()
BOT_TOKENS = [os.environ.get(f"KEY_{i}", "").strip() for i in range(22, 28)]
BOT_TOKENS = [t for t in BOT_TOKENS if t]
SRC_MID = int(os.environ.get("MIDS", "441").split(",")[0])  # chhoti file

async def main():
    user = Client("user", api_id=int(AID), api_hash=AHASH, session_string=PSESS, no_updates=True)
    await user.start()
    # channel resolve
    try:
        ch = await user.get_chat(int(K2))
    except Exception:
        ch = None
        async for d in user.get_dialogs():
            if d.chat and d.chat.id == int(K2):
                ch = d.chat
                break
    if ch is None:
        print("[x] chat fail")
        await user.stop()
        return
    cid = ch.id if hasattr(ch, "id") else ch
    print(f"[*] channel: {ch.title} | msg: {SRC_MID}")

    bots = []
    for i, t in enumerate(BOT_TOKENS):
        b = Client(f"bot{i+1}", api_id=int(AID), api_hash=AHASH, bot_token=t, no_updates=True)
        await b.start()
        me = await b.get_me()
        # forward channel post -> bot (bot ko private channel peer mil jata hai)
        try:
            fm = await user.forward_messages(me.username or f"bot{i+1}", cid, [SRC_MID])
            print(f"[ok] bot{i+1} @{me.username}: forwarded -> {fm.id if fm else '?'}")
        except Exception as e:
            print(f"[!] bot{i+1} forward fail: {str(e)[:70]}")
        # bot ab channel resolve karke message dekh sakta hai?
        try:
            ch2 = await b.get_chat(int(K2))
            print(f"    -> get_chat OK: {ch2.title}")
            m = await b.get_messages(int(K2), SRC_MID)
            print(f"    -> get_messages OK: doc={m.document is not None}")
        except Exception as e:
            print(f"    -> resolve fail: {str(e)[:60]}")
        bots.append(b)
    await user.stop()
    for b in bots:
        await b.stop()
    print("[done]")

asyncio.run(main())
