# bot1_test.py v6 — bot1 max speed: updates ON + forward + parallel x8 GetFile
import os, time, asyncio
from pyrogram import Client
from pyrogram.raw.functions.upload import GetFile
from pyrogram.raw.types import InputDocumentFileLocation
from pyrogram.utils import FileId

K2 = os.environ.get("KEY_2", "").strip()
PSESS = os.environ.get("KEY_19", "").strip()
AID = os.environ.get("KEY_16", "").strip()
AHASH = os.environ.get("KEY_17", "").strip()
BOT1_TOKEN = os.environ.get("KEY_22", "").strip()
SRC_MID = int(os.environ.get("MIDS", "476").split(",")[0] if os.environ.get("MIDS","476").split(",")[0] else 441)
MB = 1024 * 1024
WORKERS = 8
TARGET_MB = 100  # 100MB test

async def main():
    print(f"[*] bot1 max speed test | workers={WORKERS} | target={TARGET_MB}MB")
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
    ucid = uchat.id if hasattr(uchat, "id") else uchat

    bot = Client("b1u", api_id=int(AID), api_hash=AHASH, bot_token=BOT1_TOKEN)  # updates ON
    await bot.start()
    me = await bot.get_me()
    print(f"[*] bot1 connected (updates ON): @{me.username}")

    # forward + wait peer register
    try:
        await user.forward_messages(me.username or "me", ucid, [SRC_MID])
        print("[1] forward OK")
    except Exception as e:
        print(f"[1] forward fail: {str(e)[:60]}")
    await asyncio.sleep(5)

    ch = await bot.get_chat(int(K2))
    print(f"[2] get_chat: OK {ch.title}")
    cid = ch.id if hasattr(ch, "id") else ch
    m = await bot.get_messages(cid, SRC_MID)
    if m.empty or not m.document:
        print("[3] no doc")
        await user.stop()
        await bot.stop()
        return
    want = m.document.file_size
    print(f"[3] file: {want/MB:.0f} MB")

    fid = FileId.decode(m.document.file_id)
    loc = InputDocumentFileLocation(id=fid.media_id, access_hash=fid.access_hash,
                                    file_reference=fid.file_reference or b"", thumb_size="")
    target = min(TARGET_MB * MB, want)
    per = target // WORKERS // MB * MB
    if per < MB:
        per = MB
    ranges = []
    start = 0
    for i in range(WORKERS):
        end = target if i == WORKERS - 1 else start + per
        ranges.append((start, end))
        start = end
    t0 = time.time()

    async def worker(i, a, b):
        off = a
        got = 0
        with open(f"/tmp/bw_{i}.bin", "wb") as f:
            while off < b:
                res = await bot.invoke(GetFile(location=loc, offset=off, limit=MB, precise=1, cdn_supported=True))
                data = res.bytes
                if not data:
                    break
                w = min(len(data), b - off)
                f.write(data[:w])
                off += w
                got += w
        return got

    results = await asyncio.gather(*[worker(i, a, b) for i, (a, b) in enumerate(ranges)])
    dt = time.time() - t0
    total = sum(results)
    print(f"[4] download: {total/MB:.0f} MB in {dt:.1f}s = {total/dt/MB:.2f} MB/s (workers={WORKERS})")
    for i in range(WORKERS):
        try:
            os.remove(f"/tmp/bw_{i}.bin")
        except Exception:
            pass

    await user.stop()
    await bot.stop()
    print("[done]")

asyncio.run(main())
