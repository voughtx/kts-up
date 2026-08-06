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
BOT_SS = [os.environ.get(f"KEY_{i}", "").strip() for i in range(32, 38)]
BOT_SS = [s for s in BOT_SS if s]
MB = 1024 * 1024

async def make_client(name, bot_token=None, ss=None):
    if bot_token:
        c = Client(name, api_id=int(AID), api_hash=AHASH, bot_token=bot_token, no_updates=True)
    elif ss:
        c = Client(name, api_id=int(AID), api_hash=AHASH, session_string=ss, no_updates=True)
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
                try:
                    res = await app.invoke(GetFile(location=loc, offset=off, limit=chunk,
                                                   precise=1, cdn_supported=True))
                except Exception as e:
                    from pyrogram.errors import FloodWait
                    if isinstance(e, FloodWait):
                        print(f"   [{tag}w{i}] flood {e.value}s — wait...")
                        await asyncio.sleep(e.value)
                        continue
                    raise
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
        s = BOT_SS[i] if i < len(BOT_SS) else None
        apps.append(await make_client(f"bot{i+1}", bot_token=t if not s else None, ss=s))
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
    # HAR SESSION apne se message fetch karta hai (apna file_reference chahiye)
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

    async def session_job(i):
        app = apps[i]
        ch = None
        try:
            ch = await app.get_chat(int(K2))
        except Exception as e:
            # bots: peer cache nahi — channel post ko bot ke DM mein forward karke peer resolve
            if i > 0:
                try:
                    bot_me = await app.get_me()
                    fm = await apps[0].forward_messages(bot_me.username or f"bot{i}", cid, [SRC_MID])
                    fm_id = fm[0].id if isinstance(fm, list) else fm.id
                    dm_msg = await app.get_messages("me", fm_id)
                    fwd = dm_msg.forward_from_chat
                    if fwd:
                        ch = await app.get_chat(fwd.id)
                        print(f"   [session {i}] peer resolved via forward ({fwd.id})")
                except Exception as e2:
                    print(f"   [session {i}] peer resolve fail: {str(e2)[:70]}")
            else:
                print(f"   [session {i}] get_chat fail: {str(e)[:60]}")
        if ch is None:
            return None
        try:
            mm = await app.get_messages(ch.id if hasattr(ch, "id") else ch, SRC_MID)
        except Exception as e:
            print(f"   [session {i}] get_messages fail: {str(e)[:60]}")
            return None
        if mm.empty or not mm.document:
            print(f"   [session {i}] no doc")
            return None
        wk = 8 if i == 0 else 1
        try:
            got, dt = await download_range(app, mm, ranges[i][0], ranges[i][1], wk, f"s{i}", f"/tmp/mb_part_{i}.bin")
            return got
        except Exception as e:
            print(f"   [session {i}] download fail: {str(e)[:80]}")
            return None

    results = await asyncio.gather(*[session_job(i) for i in range(n)])
    for i, r in enumerate(results):
        print(f"   [session {i}] result: {r if r is None else f'{r/MB:.0f} MB'}")
    # join (sirf un sessions ke parts jo complete hue)
    with open(out2, "wb") as fo:
        for i in range(n):
            p = f"/tmp/mb_part_{i}.bin"
            if not os.path.exists(p):
                continue
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
