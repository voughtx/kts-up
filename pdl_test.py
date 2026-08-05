# pdl_test.py — PARALLEL CHUNK DOWNLOAD TEST (MTProto raw GetFile)
# File ko N workers mein byte-ranges split karke PARALLEL download + join
# Single download se compare karta hai. Verify size dono mein.
import os, json, time, asyncio
from pyrogram import Client

K2 = os.environ.get("KEY_2", "").strip()
PSESS = os.environ.get("KEY_19", "").strip()
AID = os.environ.get("KEY_16", "").strip()
AHASH = os.environ.get("KEY_17", "").strip()
SRC_MID = int(os.environ.get("MIDS", "441").split(",")[0])
WORKERS = int(os.environ.get("WORKERS", "8"))
MB = 1024 * 1024

async def single_dl(app, msg, path):
    t0 = time.time()
    fp = await msg.download(file_name=path)
    got = os.path.getsize(fp) if fp and os.path.exists(fp) else 0
    dt = time.time() - t0
    return got, dt

async def parallel_dl(app, msg, path, workers=8):
    doc = msg.document
    size = doc.file_size
    from pyrogram.raw.functions.upload import GetFile
    from pyrogram.raw.types import InputDocumentFileLocation
    from pyrogram.utils import FileId
    fid = FileId.decode(doc.file_id)
    loc = InputDocumentFileLocation(id=fid.media_id, access_hash=fid.access_hash,
                                    file_reference=fid.file_reference or b"", thumb_size="")
    chunk = MB  # 1MB max per GetFile (precise=1)
    # byte ranges per worker — 1MB-aligned boundaries (offset 4096 multiple zaroori)
    per = (size // workers) // MB * MB
    if per < MB:
        per = MB
    ranges = []
    start = 0
    for i in range(workers):
        end = size if i == workers - 1 else start + per
        ranges.append((start, end))
        start = end
    t0 = time.time()
    last = [t0]

    async def worker(i, r0, r1):
        path_w = f"/tmp/pdl_w{i}.bin"
        off = r0
        got_w = 0
        with open(path_w, "wb") as f:
            while off < r1:
                lim = min(chunk, r1 - off)
                res = await app.invoke(GetFile(location=loc, offset=off, limit=lim,
                                               precise=1, cdn_supported=True))
                data = res.bytes
                if not data:
                    break
                f.write(data)
                off += len(data)
                got_w += len(data)
                now = time.time()
                if now - last[0] >= 10:
                    sp = got_w / (now - t0)
                    print(f"   [w{i}] {got_w/MB:.0f} MB ({got_w*100//size}%) | ~{sp/MB:.1f} MB/s")
                    last[0] = now
        return path_w

    paths = await asyncio.gather(*[worker(i, r0, r1) for i, (r0, r1) in enumerate(ranges)])
    dt = time.time() - t0
    # join
    with open(path, "wb") as fo:
        for p in paths:
            with open(p, "rb") as fi:
                while True:
                    c = fi.read(MB)
                    if not c:
                        break
                    fo.write(c)
            os.remove(p)
    return os.path.getsize(path), dt

async def main():
    app = Client("pdlsess", session_string=PSESS, api_id=int(AID) if AID else None,
                 api_hash=AHASH or None, no_updates=True)
    await app.start()
    chat = None
    try:
        chat = await app.get_chat(int(K2))
    except Exception:
        async for d in app.get_dialogs():
            if d.chat and d.chat.id == int(K2):
                chat = d.chat
                break
    if chat is None:
        print("[x] chat fail")
        await app.stop()
        return
    cid = chat.id if hasattr(chat, "id") else chat
    m = await app.get_messages(cid, SRC_MID)
    if m.empty:
        print("[x] empty")
        await app.stop()
        return
    want = m.document.file_size if m.document else 0
    print(f"[*] file: {m.document.file_name} | size: {want/MB:.0f} MB | workers: {WORKERS}")

    # 1. SINGLE (baseline)
    p1 = "/tmp/dl_single.mp4"
    if os.path.exists(p1): os.remove(p1)
    g1, t1 = await single_dl(app, m, p1)
    print(f"[single] {g1/MB:.0f} MB in {t1:.1f}s = {g1/t1/MB:.2f} MB/s")
    os.remove(p1)

    # 2. PARALLEL
    p2 = "/tmp/dl_par.mp4"
    if os.path.exists(p2): os.remove(p2)
    g2, t2 = await parallel_dl(app, m, p2, WORKERS)
    print(f"[parallel x{WORKERS}] {g2/MB:.0f} MB in {t2:.1f}s = {g2/t2/MB:.2f} MB/s")
    os.remove(p2)

    ok1 = g1 >= want * 0.98
    ok2 = g2 >= want * 0.98
    print(f"[verify] single:{'OK' if ok1 else 'FAIL'} | parallel:{'OK' if ok2 else 'FAIL'} | expected {want/MB:.0f} MB")
    if t1 > 0 and ok1 and ok2:
        print(f"[speedup] {t1/t2:.1f}x faster")
    await app.stop()

asyncio.run(main())
