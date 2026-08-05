# relay_fast.py — FastTelethon parallel download (20 connections) + join + GitHub release link
# Speed: real-world 20MB/s (vs pyrogram ~3MB/s). Byte-join = original file, no encoding.
import os, json, time, subprocess, urllib.request as u, asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession

K2 = os.environ.get("KEY_2", "").strip()
SS = os.environ.get("KEY_18", "").strip()
AID = os.environ.get("KEY_16", "").strip()
AHASH = os.environ.get("KEY_17", "").strip()
SBURL = os.environ.get("KEY_20", "").strip().rstrip("/")
SBKEY = os.environ.get("KEY_21", "").strip()
GH_TOKEN = os.environ.get("GH_TOKEN", "").strip() or os.environ.get("GITHUB_TOKEN", "").strip()
REPO = os.environ.get("GITHUB_REPOSITORY", "").strip()
MIDS = [int(x) for x in os.environ.get("MIDS", "").split(",") if x.strip()]
LINK_ID = os.environ.get("LINK_ID", "relay_fast").strip()
OUT_NAME = os.environ.get("OUT_NAME", "joined.mp4").strip()
CONNS = int(os.environ.get("CONNS", "20"))  # FastTelethon connections (max 20)

from FastTelethon import download_file

def run(cmd, timeout=3600):
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)

async def main():
    if not MIDS:
        print("[x] MIDS required")
        return
    if not SS:
        print("[x] KEY_18 (Telethon session) missing")
        return
    client = TelegramClient(StringSession(SS), int(AID), AHASH)
    await client.connect()
    me = await client.get_me()
    print(f"[*] connected: {me.first_name} (dc={client.session.dc_id})")
    chat = await client.get_entity(int(K2))
    outd = "/tmp/join"
    os.makedirs(outd, exist_ok=True)

    async def dl_one(idx, mid):
        msg = await client.get_messages(chat, ids=mid)
        if not msg or not msg.document:
            return None, f"mid {mid} not doc"
        dest = os.path.join(outd, f"part_{idx:03d}")
        want = msg.document.size
        t0 = time.time()
        last = [0]; lt = [t0]
        def prog(cur, tot):
            now = time.time()
            if now - lt[0] >= 10 and tot > 0:
                sp = (cur - last[0]) / (now - lt[0]) / (1024 * 1024)
                print(f"   [dl] part {idx+1}/{len(MIDS)}: {cur/(1024*1024):.0f}/{tot/(1024*1024):.0f} MB ({cur*100//tot}%) | {sp:.1f} MB/s")
                last[0] = cur; lt[0] = now
        print(f"[*] downloading {msg.document.attributes[0].file_name if msg.document.attributes else '?'} ({want/(1024*1024):.0f} MB) x{CONNS} conns...")
        try:
            with open(dest, "wb") as f:
                await download_file(client, msg.document, f, progress_callback=prog)
        except Exception as e:
            return None, f"mid {mid}: {str(e)[:100]}"
        got = os.path.getsize(dest)
        if got < want * 0.98:
            return None, f"mid {mid} incomplete {got/(1024*1024):.0f}/{want/(1024*1024):.0f}MB"
        print(f"   [ok] part {idx+1}/{len(MIDS)} done ({got/(1024*1024):.0f} MB in {time.time()-t0:.0f}s)")
        return dest, None

    # parallel parts download
    res = await asyncio.gather(*[dl_one(i, m) for i, m in enumerate(MIDS)])
    paths = []
    ok = True
    for r, err in res:
        if err or not r:
            print(f"[x] {err}")
            ok = False
        else:
            paths.append(r)
    if not ok or len(paths) != len(MIDS):
        print("[x] download incomplete — ABORT")
        await client.disconnect()
        return

    # join
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
    await client.disconnect()

    # gh release
    tag = f"rel-{int(time.time()*1000)}"
    env = dict(os.environ); env["GH_TOKEN"] = GH_TOKEN
    r1 = run(["gh", "release", "create", tag, "--repo", REPO, "--title", tag, "--notes", "temp"], 120)
    if r1.returncode != 0:
        print("[x] release create fail:", (r1.stdout + r1.stderr)[-200:])
        return
    print("[*] release created")
    r2 = run(["gh", "release", "upload", tag, out, "--repo", REPO, "--clobber"], 3600)
    if r2.returncode != 0:
        print("[x] release upload fail:", (r2.stdout + r2.stderr)[-200:])
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
            print(f"[!] link save fail: {str(e)[:80]}")
    print("[done]")

asyncio.run(main())
