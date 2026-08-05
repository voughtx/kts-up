# video_test.py — TEST: episode ko VIDEO type mein upload + public channel CDN URL
# 1. E77 (mid 441) file download (runner)
# 2. send_video (video mode) -> main channel
# 3. copy_message -> public channel (instant, server-side)
# 4. t.me/s page scrape -> CDN video URL
# 5. verify + print
import os, json, re, time, urllib.request as u, asyncio
from pyrogram import Client, enums

K2 = os.environ.get("KEY_2", "").strip()
PSESS = os.environ.get("KEY_19", "").strip()
AID = os.environ.get("KEY_16", "").strip()
AHASH = os.environ.get("KEY_17", "").strip()
PUB = os.environ.get("PUB", "").strip()
SRC_MID = int(os.environ.get("MIDS", "441").split(",")[0])
SBURL = os.environ.get("KEY_20", "").strip().rstrip("/")
SBKEY = os.environ.get("KEY_21", "").strip()

def fetch(url):
    req = u.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with u.urlopen(req, timeout=20) as r:
        return r.read()

async def main():
    app = Client("vtsess", session_string=PSESS, api_id=int(AID) if AID else None,
                 api_hash=AHASH or None, no_updates=True)
    await app.start()
    # main channel
    main_chat = None
    try:
        main_chat = await app.get_chat(int(K2))
    except Exception:
        async for d in app.get_dialogs():
            if d.chat and d.chat.id == int(K2):
                main_chat = d.chat
                break
    if main_chat is None:
        print("[x] main chat fail")
        await app.stop()
        return
    cid = main_chat.id if hasattr(main_chat, "id") else main_chat
    # public channel
    pub_chat = await app.get_chat(PUB)
    print(f"[*] pub: {PUB} ({pub_chat.id})")

    # 1. download source
    m = await app.get_messages(cid, SRC_MID)
    if m.empty:
        print("[x] source empty")
        await app.stop()
        return
    want = m.document.file_size if m.document else 0
    print(f"[*] source: {m.document.file_name} ({want/(1024*1024):.0f} MB)")
    path = "/tmp/vtest.mp4"
    got = 0
    for att in range(4):
        try:
            if os.path.exists(path):
                os.remove(path)
            fp = await m.download(file_name=path)
            got = os.path.getsize(fp) if fp and os.path.exists(fp) else 0
            print(f"[*] attempt {att+1}: {got/(1024*1024):.0f} MB")
            if got >= want * 0.98:
                break
        except Exception as e:
            print(f"[!] attempt {att+1} err: {str(e)[:60]}")
            got = 0
    print(f"[*] downloaded: {got/(1024*1024):.0f} MB")
    if got < want * 0.98:
        print("[x] download incomplete")
        await app.stop()
        return

    # thumb (supabase row se)
    thumb_path = None
    try:
        rows = json.loads(u.urlopen(u.Request(f"{SBURL}/rest/v1/episodes?select=thumb&id=eq.{u.quote('686f41b0a19146616d8ab46b')}&limit=1",
                    headers={"apikey": SBKEY, "Authorization": f"Bearer {SBKEY}"}), timeout=20).read().decode())
        th = rows[0].get("thumb") if rows else ""
        if th and th.startswith("http"):
            with open("/tmp/vthumb.jpg", "wb") as f:
                f.write(fetch(th))
            thumb_path = "/tmp/vthumb.jpg"
    except Exception as e:
        print(f"[!] thumb: {str(e)[:40]}")
    cap = m.caption or ""

    # 2. VIDEO upload -> main channel
    t0 = time.time()
    vm = await app.send_video(cid, path, caption=cap, parse_mode=enums.ParseMode.HTML,
                              thumb=thumb_path, disable_notification=True)
    print(f"[ok] VIDEO uploaded to main: mid {vm.id} in {time.time()-t0:.0f}s (video={vm.video is not None})")

    # 3. copy -> public channel
    t1 = time.time()
    pm = await app.copy_message(pub_chat.id, cid, vm.id)
    print(f"[ok] copied to pub: mid {pm.id} in {time.time()-t1:.0f}s (video={pm.video is not None})")

    # 4. CDN scrape (individual post page)
    url = None
    try:
        html = fetch(f"https://t.me/s/{PUB}/{pm.id}").decode("utf-8", "replace")
        vids = re.findall(r'https://cdn\d+\.telesco\.pe/file/[^"\'<>\s]+\.mp4\?token=[^"\'<>\s]+', html)
        if vids:
            url = vids[0]
    except Exception as e:
        print(f"[!] scrape: {str(e)[:40]}")
    if not url:
        try:
            html = fetch(f"https://t.me/s/{PUB}").decode("utf-8", "replace")
            vids = re.findall(r'https://cdn\d+\.telesco\.pe/file/[^"\'<>\s]+\.mp4\?token=[^"\'<>\s]+', html)
            if vids:
                url = vids[-1]
        except Exception as e:
            print(f"[!] scrape2: {str(e)[:40]}")
    print(f"[*] CDN: {(url or 'NONE')[:90]}")

    # 5. verify
    if url:
        try:
            req = u.Request(url, headers={"User-Agent": "Mozilla/5.0", "Range": "bytes=0-0"}, method="HEAD" if False else "GET")
            with u.urlopen(req, timeout=20) as r:
                cl = r.headers.get("content-length", "?")
                ct = r.headers.get("content-type", "?")
                print(f"[verify] content-length: {cl} | type: {ct}")
        except Exception as e:
            print(f"[verify] err: {str(e)[:60]}")
    print("=== DIRECT URL ===")
    print(url)
    await app.stop()

asyncio.run(main())
