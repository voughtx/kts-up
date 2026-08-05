# mtbot_test.py — MULTI-BOT parallel download test
# User + 6 bots = 7 sessions, har session file ka alag byte-range download karta hai
# Compare: single session vs multi-bot (sab parallel workers ke saath)
import os, json, time, asyncio
from pyrogram import Client
from pyrogram.raw.functions.upload import GetFile
from pyrogram.raw.types import InputDocumentFileLocation
from pyrogram.utils import FileId

K2 = os.environ.get("KEY_2", "").strip()
PSESS = os.environ.get("KEY_19", "").strip()
AID = os.environ.get("KEY_16", "").strip()
AHASH = os.environ.get("KEY_17", "").strip()
SRC_MID = int(os.environ.get("MIDS", "476").split(",")[0])
BOT_TOKENS = [os.environ.get(f"KEY_{i}", "").strip() for i in range(22, 28)]
BOT_TOKENS = [t for t in BOT_TOKENS if t]
MB = 1024 * 1024

async def make_client(name, bot_token=None):
    if bot_token:
        c = Client(name, api_id=int(AID), api_hash=AHASH, bot_token=bot_token, no_updates=True)
    else:
        c = Client(name, api_id=int(AID), api_hash=AHASH, session_string=PSESS, no_updates=True)
    await c.start()
    return c

async def resolve_chat(app):
    try:
        return await app.get_chat(int(K2))
    except Exception:
        async for d in app.get_dialogs():
            if d.chat and d.chat.id == int(K2):
                return d.chat
    return None

async def download_range(app, msg, r0, r1, workers, tag, out_path):
    """Ek session apne range ko N workers se parallel download karta hai"""
    doc = msg.document
    fid = FileId.decode(doc.file_id)
    loc = InputDocumentFileLocation(id=fid.media_id, access_hash=fid.access_hash,
                                    file_reference=fid.file_reference or b"", thumb_size="")
    chunk = MB
    per = (r1 - r0) // workers // MB * MB
    if per < MB:
        per = MB
    ranges = []
    start = r0
    for i in range(workers):
        end = r1 if i == workers - 1 else start + per
        ranges.append((start, end))
        start = end
    t0 = time.time()

    async def worker(i, a, b):
        path_w = f"/tmp/mb_{tag}_{i}.bin"
        off = a
        with open(path_w, "wb") as f:
            while off < b:
                res = await app.invoke(GetFile(location=loc, offset=off, limit=chunk,
                                               precise=1, cdn_supported=True))
                data = res.bytes
                if not data:
                    break
                w = min(len(data), b - off)
                f.write(data[:w])
                off += w
        return path_w

    paths = await asyncio.gather(*[worker(i, a, b) for i, (a, b) in enumerate(ranges)])
    dt = time.time() - t0
    with open(out_path, "wb") as fo:
        for p in paths:
            with open(p, "rb") as fi:
                while True:
                    c = fi.read(MB)
                    if not c:
                        break
                    fo.write(c)
            os.remove(p)
    got = os.path.getsize(out_path)
    return got, dt

async def main():
    # session list: user + bots
    print(f"[*] bots: {len(BOT_TOKENS)} | user: yes")
    apps = []
    apps.append(await make_client("user"))
    for i, t in enumerate(BOT_TOKENS):
        apps.append(await make_client(f"bot{i+1}", bot_token=t))
    # source message (user se)
    chat = await resolve_chat(apps[0])
    if chat is None:
        print("[x] chat fail")
        await asyncio.gather(*[a.stop() for a in apps])
        return
    m = await apps[0].get_messages(chat.id if hasattr(chat, "id") else chat, SRC_MID)
    if m.empty or not m.document:
        print("[x] no doc")
        await asyncio.gather(*[a.stop() for a in apps])
        return
    want = m.document.file_size
    print(f"[*] file: {want/MB:.0f} MB | sessions: {len(apps)}")

    # 1. SINGLE (user, 8 workers) baseline
    out1 = "/tmp/mb_single.bin"
    if os.path.exists(out1): os.remove(out1)
    g1, t1 = await download_range(apps[0], m, 0, want, 8, "s1", out1)
    print(f"[single-user x8] {g1/MB:.0f} MB in {t1:.0f}s = {g1/t1/MB:.2f} MB/s")
    os.remove(out1)

    # 2. MULTI-BOT (har session apna range, 4 workers each) — MB-aligned ranges
    n = len(apps)
    out2 = "/tmp/mb_multi.bin"
    if os.path.exists(out2): os.remove(out2)
    t0 = time.time()
    ranges = []
    start = 0
    per = (want // n) // MB * MB
    if per < MB:
        per = MB
    for i in range(n):
        end = want if i == n - 1 else start + per
        ranges.append((start, end))
        start = end
    results = await asyncio.gather(*[
        download_range(apps[i], m, ranges[i][0], ranges[i][1], 4, f"s{i}", f"/tmp/mb_part_{i}.bin")
        for i in range(n)
    ])
    # join
    with open(out2, "wb") as fo:
        for i in range(n):
            p = f"/tmp/mb_part_{i}.bin"
            with open(p, "rb") as fi:
                while True:
                    c = fi.read(MB)
                    if not c:
                        break
                    fo.write(c)
            os.remove(p)
    g2 = os.path.getsize(out2)
    t2 = time.time() - t0
    print(f"[multi {n} sessions] {g2/MB:.0f} MB in {t2:.0f}s = {g2/t2/MB:.2f} MB/s")
    os.remove(out2)

    ok1 = g1 >= want * 0.98
    ok2 = g2 >= want * 0.98
    print(f"[verify] single:{'OK' if ok1 else 'FAIL'} | multi:{'OK' if ok2 else 'FAIL'}")
    if t1 > 0 and t2 > 0 and ok1 and ok2:
        print(f"[speedup] {t1/t2:.1f}x faster")
    await asyncio.gather(*[a.stop() for a in apps])

asyncio.run(main())
