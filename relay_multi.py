# relay_join_multi.py — MULTI-BOT direct link: user+6 bots parallel download (proven pattern)
# Har session: updates ON (bots) + forward peer register + apna range, 2 workers each
# Join -> GitHub release -> 24h link -> Supabase
import os, json, time, subprocess, urllib.request as u, asyncio
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
SBURL = os.environ.get("KEY_20", "").strip().rstrip("/")
SBKEY = os.environ.get("KEY_21", "").strip()
GH_TOKEN = os.environ.get("GH_TOKEN", "").strip() or os.environ.get("GITHUB_TOKEN", "").strip()
REPO = os.environ.get("GITHUB_REPOSITORY", "").strip()
MIDS = [int(x) for x in os.environ.get("MIDS", "").split(",") if x.strip()]
LINK_ID = os.environ.get("LINK_ID", "movie_test").strip()
OUT_NAME = os.environ.get("OUT_NAME", "joined.mp4").strip()
MB = 1024 * 1024
WORKERS_PER_SESSION = 2

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
    print(f"[*] MIDS: {MIDS} | bots: {len(BOT_TOKENS)} | out: {OUT_NAME}")
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
        print("[x] chat fail")
        await user.stop()
        return
    ucid = uchat.id if hasattr(uchat, "id") else uchat
    print(f"[*] channel: {uchat.title}")

    # bots + peer register
    bots = []
    for i, tok in enumerate(BOT_TOKENS):
        b = Client(f"b{i+1}", api_id=int(AID), api_hash=AHASH, bot_token=tok)
        await b.start()
        me = await b.get_me()
        try:
            await user.forward_messages(me.username or f"b{i+1}", ucid, [MIDS[0]])
        except Exception:
            pass
        bots.append(b)
    await asyncio.sleep(6)

    outd = "/tmp/joinm"
    os.makedirs(outd, exist_ok=True)
    sessions = [user] + bots
    n = len(sessions)
    overall_t0 = time.time()
    for pi, mid in enumerate(MIDS):
        m = await user.get_messages(ucid, mid)
        if m.empty or not m.document:
            print(f"[x] mid {mid} no doc")
            continue
        want = m.document.file_size
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
            mm = await app.get_messages(cid, mid)
            if mm.empty or not mm.document:
                return None
            return await dl_range(app, mm, ranges[idx][0], ranges[idx][1], WORKERS_PER_SESSION, f"p{pi}s{idx}")
        t0 = time.time()
        results = await asyncio.gather(*[session_job(i) for i in range(n)])
        dt = time.time() - t0
        total = sum(r for r in results if r)
        print(f"[part {pi+1}/{len(MIDS)}] {total/MB:.0f}/{want/MB:.0f} MB in {dt:.0f}s = {total/dt/MB:.2f} MB/s (multi-{n})")
        # join parts
        outp = os.path.join(outd, f"part_{pi}.bin")
        with open(outp, "wb") as fo:
            for i in range(n):
                for w in range(WORKERS_PER_SESSION):
                    p = f"/tmp/p{pi}s{i}_{w}.bin"
                    if os.path.exists(p):
                        with open(p, "rb") as fi:
                            while True:
                                c = fi.read(MB)
                                if not c:
                                    break
                                fo.write(c)
                        os.remove(p)
        print(f"    joined -> {outp} ({os.path.getsize(outp)/MB:.0f} MB)")

    # final join all parts in order
    out = os.path.join(outd, OUT_NAME)
    with open(out, "wb") as fo:
        for pi in range(len(MIDS)):
            p = os.path.join(outd, f"part_{pi}.bin")
            if os.path.exists(p):
                with open(p, "rb") as fi:
                    while True:
                        c = fi.read(MB)
                        if not c:
                            break
                        fo.write(c)
                os.remove(p)
    print(f"[*] final: {out} ({os.path.getsize(out)/MB:.0f} MB) | total {time.time()-overall_t0:.0f}s")

    # GitHub release
    tag = f"rel-{int(time.time()*1000)}"
    env = dict(os.environ)
    env["GH_TOKEN"] = GH_TOKEN
    r1 = subprocess.run(["gh", "release", "create", tag, "--repo", REPO, "--title", tag, "--notes", "temp"], capture_output=True, text=True, timeout=120)
    print("[*] release create:", r1.returncode)
    r2 = subprocess.run(["gh", "release", "upload", tag, out, "--repo", REPO, "--clobber"], capture_output=True, text=True, timeout=3600)
    print("[*] release upload:", r2.returncode)
    if r2.returncode != 0:
        print("   ", (r2.stdout + r2.stderr)[-300:])
        await user.stop()
        for b in bots:
            await b.stop()
        return
    base = os.path.basename(out)
    url = f"https://github.com/{REPO}/releases/download/{tag}/{base}"
    print(f"[*] LINK: {url}")
    if SBURL and SBKEY:
        try:
            row = {"id": LINK_ID, "url": url, "expires_at": int(time.time()) + 86400, "created_at": int(time.time())}
            req = u.Request(f"{SBURL}/rest/v1/links", data=json.dumps(row).encode(), method="POST",
                            headers={"apikey": SBKEY, "Authorization": f"Bearer {SBKEY}",
                                     "Content-Type": "application/json", "Prefer": "resolution=merge-duplicates"})
            with u.urlopen(req, timeout=30) as r:
                print(f"[ok] link saved ({r.status})")
        except Exception as e:
            print(f"[!] link save fail: {str(e)[:60]}")
    print("[done]")
    await user.stop()
    for b in bots:
        await b.stop()

asyncio.run(main())
