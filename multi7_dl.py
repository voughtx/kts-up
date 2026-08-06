# multi7_dl.py — FULL MULTI-BOT DOWNLOAD TEST (user + 6 bots, proven pattern)
# Har session: updates ON (bots) + forward peer register + apna 1/7 range, 8 workers each
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
WORKERS = 8

async def main():
    print(f"[*] sessions: user + {len(BOT_TOKENS)} bots | workers/session: {WORKERS}")
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
    print(f"[*] user chat: {uchat.title}")

    # bots (updates ON) + peer register via forward
    bots = []
    for i, tok in enumerate(BOT_TOKENS):
        b = Client(f"b{i+1}", api_id=int(AID), api_hash=AHASH, bot_token=tok)  # updates ON
        await b.start()
        me = await b.get_me()
        try:
            await user.forward_messages(me.username or f"b{i+1}", ucid, [SRC_MID])
        except Exception as e:
            print(f"[!] bot{i+1} forward fail: {str(e)[:50]}")
        bots.append(b)
    print("[*] bots connected + forwarded, waiting 6s for peer register...")
    await asyncio.sleep(6)

    # source doc (user se)
    m = await user.get_messages(ucid, SRC_MID)
    if m.empty or not m.document:
        print("[x] no doc")
        await user.stop()
        for b in bots:
            await b.stop()
        return
    want = m.document.file_size
    print(f"[*] file: {want/MB:.0f} MB")

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

    t0 = time.time()

    async def session_job(idx):
        app = sessions[idx]
        # chat resolve (bot ke liye updates se peer registered hai)
        try:
            ch = await app.get_chat(int(K2))
        except Exception as e:
            print(f"   [s{idx}] get_chat fail: {str(e)[:50]}")
            return None
        cid = ch.id if hasattr(ch, "id") else ch
        mm = await app.get_messages(cid, SRC_MID)
        if mm.empty or not mm.document:
            print(f"   [s{idx}] no doc")
            return None
        fid = FileId.decode(mm.document.file_id)
        loc = InputDocumentFileLocation(id=fid.media_id, access_hash=fid.access_hash,
                                        file_reference=fid.file_reference or b"", thumb_size="")
        r0, r1 = ranges[idx]
        chunk = MB
        p = (r1 - r0) // WORKERS // MB * MB
        if p < MB:
            p = MB
        sub = []
        s0 = r0
        for i in range(WORKERS):
            s1 = r1 if i == WORKERS - 1 else s0 + p
            sub.append((s0, s1))
            s0 = s1

        async def worker(i, a, b):
            off = a
            got = 0
            with open(f"/tmp/m7_{idx}_{i}.bin", "wb") as f:
                while off < b:
                    res = await app.invoke(GetFile(location=loc, offset=off, limit=chunk, precise=1, cdn_supported=True))
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

    results = await asyncio.gather(*[session_job(i) for i in range(n)])
    dt = time.time() - t0
    total = sum(r for r in results if r)
    print(f"[*] per-session: {[f'{r/MB:.0f}MB' if r else 'FAIL' for r in results]}")
    print(f"[RESULT] {total/MB:.0f} MB in {dt:.1f}s = {total/dt/MB:.2f} MB/s (7 sessions x8)")
    # verify expected
    exp = want * 0.98
    print(f"[VERIFY] {'OK' if total >= exp else 'FAIL'} (expected {want/MB:.0f} MB)")

    await user.stop()
    for b in bots:
        await b.stop()
    print("[done]")

asyncio.run(main())
