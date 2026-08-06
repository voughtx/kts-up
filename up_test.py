# up_test.py — UPLOAD SPEED TEST: normal vs FastTelethon parallel (same telethon session)
# FastTelethon = raw SaveBigFilePart multiple connections (Telegram official parallel upload)
import os, time, asyncio, random
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.types import InputFile
from FastTelethon import upload_file

K2 = os.environ.get("KEY_2", "").strip()
TSESS = os.environ.get("KEY_18", "").strip()  # telethon session
AID = os.environ.get("KEY_16", "").strip()
AHASH = os.environ.get("KEY_17", "").strip()
MB = 1024 * 1024
FSZ = 20 * MB  # 20MB test

def make_file(path, size):
    with open(path, "wb") as f:
        f.write(os.urandom(size))

async def main():
    print(f"[*] telethon session len: {len(TSESS)}")
    client = TelegramClient(StringSession(TSESS), int(AID), AHASH)
    await client.connect()
    me = await client.get_me()
    print(f"[*] connected: {me.first_name}")

    # channel resolve
    try:
        chat = await client.get_entity(int(K2))
    except Exception:
        chat = None
        async for d in client.iter_dialogs():
            if d.id == int(K2):
                chat = d.entity
                break
    if chat is None:
        print("[x] chat fail")
        await client.disconnect()
        return
    print(f"[*] chat: {chat.title}")

    make_file("/tmp/upn.bin", FSZ)
    make_file("/tmp/upf.bin", FSZ)

    # TEST A: normal upload (single connection)
    t0 = time.time()
    with open("/tmp/upn.bin", "rb") as f:
        fn = await client.upload_file(f, file_name="upn.bin")
    dt = time.time() - t0
    print(f"[NORMAL] {FSZ/MB:.0f} MB in {dt:.1f}s = {FSZ/dt/MB:.2f} MB/s")
    # send (time not counted, just cleanup)
    try:
        await client.send_file(chat, fn, caption="test normal")
    except Exception as e:
        print(f"[!] send normal: {str(e)[:50]}")

    # TEST B: FastTelethon parallel upload
    t0 = time.time()
    with open("/tmp/upf.bin", "rb") as f:
        ff = await upload_file(client, f)
    dt = time.time() - t0
    print(f"[FASTTELETHON] {FSZ/MB:.0f} MB in {dt:.1f}s = {FSZ/dt/MB:.2f} MB/s")
    try:
        await client.send_file(chat, ff, caption="test fast")
    except Exception as e:
        print(f"[!] send fast: {str(e)[:50]}")

    await client.disconnect()
    print("[done]")

asyncio.run(main())
