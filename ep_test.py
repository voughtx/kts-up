# ep_test.py — REAL EPISODE TEST: S1E8 (mid 499) download + FastTelethon upload
# Download: multi-bot x8 (fast) | Upload: FastTelethon parallel (user)
import os, time, asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession
from FastTelethon import upload_file

K2 = os.environ.get("KEY_2", "").strip()
TSESS = os.environ.get("KEY_18", "").strip()
AID = os.environ.get("KEY_16", "").strip()
AHASH = os.environ.get("KEY_17", "").strip()
SRC_MID = int(os.environ.get("MIDS", "499").split(",")[0])
MB = 1024 * 1024

async def main():
    print(f"[*] episode test: mid {SRC_MID}")
    cu = TelegramClient(StringSession(TSESS), int(AID), AHASH)
    await cu.connect()
    me = await cu.get_me()
    print(f"[*] connected: {me.first_name}")
    try:
        chat = await cu.get_entity(int(K2))
    except Exception:
        chat = None
        async for d in cu.iter_dialogs():
            if d.id == int(K2):
                chat = d.entity
                break
    if chat is None:
        print("[x] chat fail")
        await cu.disconnect()
        return

    # 1. DOWNLOAD S1E8
    msg = await cu.get_messages(chat, ids=SRC_MID)
    if not msg or not msg.document:
        print("[x] no doc")
        await cu.disconnect()
        return
    want = msg.document.size
    print(f"[*] file: {msg.document.attributes[0].file_name if msg.document.attributes else '?'} | {want/MB:.0f} MB")
    path = "/tmp/ep8.mp4"
    t0 = time.time()
    await msg.download_media(file=path)
    dt = time.time() - t0
    got = os.path.getsize(path)
    print(f"[DL] {got/MB:.0f} MB in {dt:.1f}s = {got/dt/MB:.2f} MB/s")

    # 2. UPLOAD via FastTelethon
    t0 = time.time()
    with open(path, "rb") as f:
        ff = await upload_file(cu, f)
    dt = time.time() - t0
    print(f"[UL-FAST] {got/MB:.0f} MB in {dt:.1f}s = {got/dt/MB:.2f} MB/s")
    try:
        await cu.send_file(chat, ff, caption="TEST S1E8 fast-upload")
        print("[ok] sent")
    except Exception as e:
        print(f"[!] send: {str(e)[:60]}")
    await cu.disconnect()
    print("[done]")

asyncio.run(main())
