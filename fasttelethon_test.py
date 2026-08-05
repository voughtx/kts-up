# fasttelethon_test.py — FastTelethon (Telethon parallel) download speed test
# Compare: Pyrogram single vs Pyrogram parallel x8 vs FastTelethon
import os, json, time, asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession
from FastTelethon import download_file

K2 = os.environ.get("KEY_2", "").strip()
PSESS = os.environ.get("KEY_18", "").strip()  # Telethon session string
AID = os.environ.get("KEY_16", "").strip()
AHASH = os.environ.get("KEY_17", "").strip()
SRC_MID = int(os.environ.get("MIDS", "476").split(",")[0])
MB = 1024 * 1024

async def main():
    client = TelegramClient(StringSession(PSESS), int(AID), AHASH)
    await client.start()
    me = await client.get_me()
    print(f"[*] connected as {me.first_name}")

    # resolve channel via dialogs (peer id invalid issue)
    chat = None
    try:
        chat = await client.get_entity(int(K2))
    except Exception:
        async for d in client.iter_dialogs():
            if d.id == int(K2):
                chat = d.entity
                break
    if chat is None:
        print("[x] chat fail")
        await client.disconnect()
        return
    print(f"[*] chat: {chat.title}")

    msg = await client.get_messages(chat, ids=SRC_MID)
    if not msg or not msg.document:
        print("[x] no doc")
        await client.disconnect()
        return
    want = msg.document.size
    print(f"[*] file: {msg.document.attributes and msg.document.attributes[0].file_name or '?'} | size: {want/MB:.0f} MB")

    t0 = time.time()
    last = [t0]
    def prog(cur, tot):
        now = time.time()
        if now - last[0] >= 10 and tot:
            sp = cur / (now - t0) / MB
            print(f"   {cur/MB:.0f}/{tot/MB:.0f} MB ({cur*100//tot}%) | ~{sp:.1f} MB/s")
            last[0] = now
    out = "/tmp/ft_dl.mp4"
    if os.path.exists(out):
        os.remove(out)
    with open(out, "wb") as f:
        await download_file(client, msg.document, f, progress_callback=prog)
    dt = time.time() - t0
    got = os.path.getsize(out)
    os.remove(out)
    ok = got >= want * 0.98
    print(f"[fasttelethon] {got/MB:.0f} MB in {dt:.1f}s = {got/dt/MB:.2f} MB/s | verify: {'OK' if ok else 'FAIL'}")
    await client.disconnect()

asyncio.run(main())
