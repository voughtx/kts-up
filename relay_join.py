# relay_join.py — split parts ko byte-join karke ek file banao + GitHub release direct link
# Parts download (Pyrogram) -> cat (byte-join, NO encoding) -> gh release upload -> 24h link
# Link + expiry Supabase links table mein save
import os, json, time, subprocess, urllib.request as u, urllib.parse as p

K2 = os.environ.get("KEY_2", "").strip()
PSESS = os.environ.get("KEY_19", "").strip()
AID = os.environ.get("KEY_16", "").strip()
AHASH = os.environ.get("KEY_17", "").strip()
SBURL = os.environ.get("KEY_20", "").strip().rstrip("/")
SBKEY = os.environ.get("KEY_21", "").strip()
GH_TOKEN = os.environ.get("GH_TOKEN", "").strip() or os.environ.get("GITHUB_TOKEN", "").strip()
REPO = os.environ.get("GITHUB_REPOSITORY", "").strip()
MIDS = [int(x) for x in os.environ.get("MIDS", "").split(",") if x.strip()]
LINK_ID = os.environ.get("LINK_ID", "movie_test").strip()
OUT_NAME = os.environ.get("OUT_NAME", "joined.mp4").strip()

def run(cmd, timeout=3000):
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    return r

def main():
    from pyrogram import Client
    import asyncio

    if not MIDS:
        print("[x] MIDS required")
        raise SystemExit(1)

    async def parallel_dl(app, msg, dest, workers=8):
        """MTProto raw GetFile — byte-ranges split + N workers parallel download"""
        doc = msg.document
        size = doc.file_size
        MB = 1024 * 1024
        from pyrogram.raw.functions.upload import GetFile
        from pyrogram.raw.types import InputDocumentFileLocation
        from pyrogram.utils import FileId
        fid = FileId.decode(doc.file_id)
        loc = InputDocumentFileLocation(id=fid.media_id, access_hash=fid.access_hash,
                                        file_reference=fid.file_reference or b"", thumb_size="")
        chunk = MB
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

        async def worker(i, r0, r1):
            path_w = f"/tmp/rj_w{i}.bin"
            off = r0
            got_w = 0
            with open(path_w, "wb") as f:
                while off < r1:
                    res = await app.invoke(GetFile(location=loc, offset=off, limit=chunk,
                                                   precise=1, cdn_supported=True))
                    data = res.bytes
                    if not data:
                        break
                    w = min(len(data), r1 - off)
                    f.write(data[:w])
                    off += w
                    got_w += w
                    if time.time() - t0 >= 30:
                        print(f"   [w{i}] {got_w/MB:.0f} MB | ~{got_w/(time.time()-t0)/MB:.1f} MB/s")
            return path_w

        paths = await asyncio.gather(*[worker(i, r0, r1) for i, (r0, r1) in enumerate(ranges)])
        dt = time.time() - t0
        with open(dest, "wb") as fo:
            for p in paths:
                with open(p, "rb") as fi:
                    while True:
                        c = fi.read(MB)
                        if not c:
                            break
                        fo.write(c)
                os.remove(p)
        return os.path.getsize(dest), dt

    async def download_one(app, chat, mid, dest):
        m = await app.get_messages(chat, mid)
        if m.empty or not m.document:
            return None, f"mid {mid} empty/not doc"
        want = m.document.file_size or 0
        print(f"[*] downloading {m.document.file_name} ({want/(1024*1024):.0f} MB) PARALLEL x8...")
        try:
            if os.path.exists(dest):
                os.remove(dest)
            got, dt = await parallel_dl(app, m, dest, 8)
            print(f"    done: {got/(1024*1024):.0f} MB in {dt:.0f}s ({got/dt/MB:.1f} MB/s)")
            if got >= want * 0.98:
                return dest, None
        except Exception as e:
            print(f"    parallel err: {str(e)[:100]}")
            # fallback: normal download
            try:
                if os.path.exists(dest):
                    os.remove(dest)
                fp = await m.download(file_name=dest)
                got = os.path.getsize(fp) if fp and os.path.exists(fp) else 0
                print(f"    fallback: {got/(1024*1024):.0f} MB")
                if got >= want * 0.98:
                    return dest, None
            except Exception as e2:
                print(f"    fallback err: {str(e2)[:80]}")
        return None, f"mid {mid} incomplete"

    async def run_async():
        app = Client("joinsess", session_string=PSESS, api_id=int(AID) if AID else None,
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
        outd = "/tmp/join"
        os.makedirs(outd, exist_ok=True)
        # PARALLEL download (gather) — sab parts ek saath, retry + size verify
        tasks = []
        for i, mid in enumerate(MIDS):
            dest = os.path.join(outd, f"part_{i:03d}")
            tasks.append(download_one(app, cid, mid, dest))
        res = await asyncio.gather(*tasks)
        paths = []
        ok_all = True
        for r, err in res:
            if err or not r:
                print(f"[x] {err}")
                ok_all = False
            else:
                paths.append(r)
        await app.stop()
        if not ok_all or len(paths) != len(MIDS):
            print("[x] download incomplete")
            return
        # byte-join (cat) — NO encoding
        out = os.path.join(outd, OUT_NAME)
        with open(out, "wb") as fo:
            for fp in paths:
                with open(fp, "rb") as fi:
                    while True:
                        c = fi.read(1 << 20)
                        if not c:
                            break
                        fo.write(c)
        print(f"[ok] joined -> {out} ({os.path.getsize(out)/(1024*1024):.0f} MB)")
        # gh release
        tag = f"rel-{int(time.time()*1000)}"
        env = dict(os.environ)
        env["GH_TOKEN"] = GH_TOKEN
        r1 = run(["gh", "release", "create", tag, "--repo", REPO, "--title", tag, "--notes", "temp"], 120)
        print("[*] release create:", r1.returncode)
        if r1.returncode != 0:
            print("   ", (r1.stdout + r1.stderr)[-300:])
        r2 = run(["gh", "release", "upload", tag, out, "--repo", REPO, "--clobber"], 3600)
        print("[*] release upload:", r2.returncode)
        if r2.returncode != 0:
            print("   ", (r2.stdout + r2.stderr)[-300:])
            return
        base = os.path.basename(out)
        url = f"https://github.com/{REPO}/releases/download/{tag}/{base}"
        print(f"[*] LINK: {url}")
        # save to supabase links
        if SBURL and SBKEY:
            try:
                row = {"id": LINK_ID, "url": url, "expires_at": int(time.time()) + 86400, "created_at": int(time.time())}
                req = u.Request(f"{SBURL}/rest/v1/links", data=json.dumps(row).encode(), method="POST",
                                headers={"apikey": SBKEY, "Authorization": f"Bearer {SBKEY}",
                                         "Content-Type": "application/json", "Prefer": "resolution=merge-duplicates"})
                with u.urlopen(req, timeout=30) as r:
                    print(f"[ok] link saved ({r.status})")
            except Exception as e:
                print(f"[!] link save fail: {str(e)[:80]}")
        print("[done]")

    try:
        asyncio.run(run_async())
    except RuntimeError:
        import nest_asyncio
        nest_asyncio.apply()
        asyncio.run(run_async())

if __name__ == "__main__":
    main()
