# multi7_dl2.py — REFINED: control (user x8) vs multi-7 (2 workers/session)
import os, time, asyncio
from pyrogram import Client
from pyrogram.raw.functions.upload import GetFile
from pyrogram.raw.types import InputDocumentFileLocation
from pyrogram.utils import FileId

K2 = os.environ.get("KEY_2", "").strip()
PSESS = os.environ.get("KEY_19", "").strip()
AID = os.environ.get("KEY_16", "").strip()
AHASH = os.environ.get("KEY_17", "").strip()
BOT_TOKENS = [os.environ.get(f"KEY_{i}", "").strip() for i in range(22, 28)]
BOT_TOKENS = [t for t in BOT_TOKENS if t]
SRC_MID = int(os.environ.get("MIDS", "441").split(",")[0])
MB = 1024 * 1024

async def dl_range(app, msg, r0, r1, workers, tag):
    fid = FileId.decode(msg.document.file_id)
    loc = InputDocumentFileLocation(id=fid.media_id, access_hash=fid.access_hash,
                                    file_reference=fid.file_reference or b"", thumb_size="")
    chunk = MB
    p = (r1 - r0) // workers // MB * MB
    if p < MB:
        p = MB
    sub = []
    s0 = r0
    for i in range(workers):
        s1 = r1 if i == workers - 1 else s0 + p
        sub.append((s0, s1))
        s0 = s1

    async def worker(i, a, b):
        off = a
        got = 0
        with open(f"/tmp/{tag}_{i}.bin", "wb") as f:
            while off < b:
                try:
                    res = await app.invoke(GetFile(location=loc, offset=off, limit=chunk, precise=1, cdn_supported=True))
                except Exception as e:
                    from pyrogram.errors import FloodWait
                    if isinstance(e, FloodWait):
                        await asyncio.sleep(e.value)
                        continue
                    raise
                data = res.bytes
                if not data:
                    break
                w = min(len(data), b - off)
                f.write(data[:w])
                off += w
                got += w
        return got

    results = await asyncio.gather(*[worker(i, a, b) for i, (a, b) in enumerate(sub)])
    return sum(results)

async def main():
    print(f"[*] TEST: control(user x8) vs multi-7 (2 workers/session)")
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
    m = await user.get_messages(ucid, SRC_MID)
    want = m.document.file_size
    print(f"[*] file: {want/MB:.0f} MB")

    # CONTROL: user x8
    t0 = time.time()
    got = await dl_range(user, m, 0, want, 8, "ctl")
    dt = time.time() - t0
    print(f"[CONTROL user-x8] {got/MB:.0f} MB in {dt:.1f}s = {got/dt/MB:.2f} MB/s")

    # MULTI: 7 sessions x 2 workers
    bots = []
    for i, tok in enumerate(BOT_TOKENS):
        b = Client(f"b{i+1}", api_id=int(AID), api_hash=AHASH, bot_token=tok)
        await b.start()
        me = await b.get_me()
        try:
            await user.forward_messages(me.username or f"b{i+1}", ucid, [SRC_MID])
        except Exception:
            pass
        bots.append(b)
    await asyncio.sleep(6)

    sessions = [user] + bots
    n = len(sessions)
    per = (want // n) // MB * MB
    if per < MB:
        per = MB
    ranges = []
    start = 0
    for i in range(n):
        end = want if i == n - 1 else start + per
        ranges.append((start, end))
        start = end

    async def session_job(idx):
        app = sessions[idx]
        try:
            ch = await app.get_chat(int(K2))
        except Exception:
            return None
        cid = ch.id if hasattr(ch, "id") else ch
        mm = await app.get_messages(cid, SRC_MID)
        if mm.empty or not mm.document:
            return None
        return await dl_range(app, mm, ranges[idx][0], ranges[idx][1], 2, f"s{idx}")

    t0 = time.time()
    results = await asyncio.gather(*[session_job(i) for i in range(n)])
    dt = time.time() - t0
    total = sum(r for r in results if r)
    print(f"[*] per-session: {[f'{r/MB:.0f}MB' if r else 'FAIL' for r in results]}")
    print(f"[MULTI-7 x2] {total/MB:.0f} MB in {dt:.1f}s = {total/dt/MB:.2f} MB/s")
    print(f"[VERIFY] {'OK' if total >= want*0.98 else 'FAIL'}")

    await user.stop()
    for b in bots:
        await b.stop()
    print("[done]")

asyncio.run(main())
