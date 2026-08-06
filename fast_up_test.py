# fast_up_test.py — REAL-SIZE upload test: FastTelethon user vs bot (67MB file)
import os, time, asyncio, random
from telethon import TelegramClient
from telethon.sessions import StringSession
from FastTelethon import upload_file

K2 = os.environ.get("K2", "").strip() or os.environ.get("KEY_2", "").strip()
TSESS = os.environ.get("KEY_18", "").strip()
AID = os.environ.get("KEY_16", "").strip()
AHASH = os.environ.get("KEY_17", "").strip()
BOT1 = os.environ.get("KEY_22", "").strip()  # bot1 token
MB = 1024 * 1024
FSZ = 67 * MB  # S1E8 jaisa size

def make_file(path, size):
    with open(path, "wb") as f:
        f.write(os.urandom(size))

async def resolve_chat(client):
    try:
        return await client.get_entity(int(K2))
    except Exception:
        async for d in client.iter_dialogs():
            if d.id == int(K2):
                return d.entity
    return None

async def main():
    make_file("/tmp/upu.bin", FSZ)
    make_file("/tmp/upb.bin", FSZ)

    # ==== USER (telethon session) ====
    print("[*] === USER TEST ===")
    cu = TelegramClient(StringSession(TSESS), int(AID), AHASH)
    await cu.connect()
    me = await cu.get_me()
    print(f"[*] user: {me.first_name}")
    chat = await resolve_chat(cu)
    if chat:
        t0 = time.time()
        with open("/tmp/upu.bin", "rb") as f:
            ff = await upload_file(cu, f)
        dt = time.time() - t0
        print(f"[USER-FAST] {FSZ/MB:.0f} MB in {dt:.1f}s = {FSZ/dt/MB:.2f} MB/s")
        try:
            await cu.send_file(chat, ff, caption="test user fast")
        except Exception as e:
            print(f"[!] send: {str(e)[:50]}")
    await cu.disconnect()

    # ==== BOT1 (token se) ====
    print("[*] === BOT1 TEST ===")
    cb = TelegramClient("bot1t", int(AID), AHASH)
    await cb.start(bot_token=BOT1)
    bme = await cb.get_me()
    print(f"[*] bot: {bme.username}")
    try:
        chatb = await cb.get_entity(int(K2))
    except Exception:
        chatb = None
    if chatb:
        t0 = time.time()
        with open("/tmp/upb.bin", "rb") as f:
            ff = await upload_file(cb, f)
        dt = time.time() - t0
        print(f"[BOT-FAST] {FSZ/MB:.0f} MB in {dt:.1f}s = {FSZ/dt/MB:.2f} MB/s")
        try:
            await cb.send_file(chatb, ff, caption="test bot fast")
        except Exception as e:
            print(f"[!] send: {str(e)[:50]}")
    else:
        print("[x] bot chat resolve fail")
    await cb.disconnect()
    print("[done]")

asyncio.run(main())
