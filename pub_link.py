# pub_link.py — instant direct link via public channel + telesco.pe CDN
# Steps: copy parts (server-side, 2s) -> public channel
#        scrape t.me/s/<pub>/<mid> -> CDN URL (1s)
#        save links (Supabase) -> print
# No re-upload, no runner download. Link = Telegram CDN (fast worldwide).
import os, json, re, time, urllib.request as u, asyncio, subprocess
from pyrogram import Client

K2 = os.environ.get("KEY_2", "").strip()
SBURL = os.environ.get("KEY_20", "").strip().rstrip("/")
SBKEY = os.environ.get("KEY_21", "").strip()
PSESS = os.environ.get("KEY_19", "").strip()
AID = os.environ.get("KEY_16", "").strip()
AHASH = os.environ.get("KEY_17", "").strip()
MIDS = [int(x) for x in os.environ.get("MIDS", "").split(",") if x.strip()]
PUB = os.environ.get("PUB", "").strip()
LINK_ID = os.environ.get("LINK_ID", "link").strip()
EXP_H = int(os.environ.get("EXP_H", "24"))

def fetch_cdn(msg_url):
    """t.me/<pub>/<mid>?single follow -> final CDN URL; fallback t.me/s scrape"""
    try:
        r = subprocess.run(["curl", "-s", "-o", "/dev/null", "-w", "%{url_effective}",
                            "-L", "--max-time", "20", "-A", "Mozilla/5.0", msg_url],
                           capture_output=True, text=True, timeout=30)
        final = r.stdout.strip()
        if "telesco.pe" in final or "cdn" in final.lower():
            return final
    except Exception:
        pass
    # fallback: t.me/s page scrape
    try:
        s_url = msg_url.replace("https://t.me/", "https://t.me/s/")
        req = u.Request(s_url, headers={"User-Agent": "Mozilla/5.0"})
        with u.urlopen(req, timeout=20) as resp:
            html = resp.read().decode("utf-8", "replace")
        m = re.search(r'https://cdn\d+\.telesco\.pe/[^"\s&]+', html)
        if m:
            return m.group(0)
    except Exception:
        pass
    return None

async def main():
    app = Client("publinksess", session_string=PSESS, api_id=int(AID) if AID else None,
                 api_hash=AHASH or None, no_updates=True)
    await app.start()
    # main channel resolve
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
    # public channel resolve
    pub_chat = await app.get_chat(PUB)
    print(f"[*] pub: {pub_chat.username or PUB} ({pub_chat.id})")

    links = []
    t0 = time.time()
    for i, mid in enumerate(MIDS):
        m = await app.get_messages(main_chat.id, mid)
        if m.empty:
            print(f"[x] mid {mid} empty")
            continue
        # server-side copy -> public channel
        nm = await app.copy_message(pub_chat.id, main_chat.id, mid)
        pmid = nm.id
        print(f"[ok] copied {mid} -> pub {pmid} ({time.time()-t0:.1f}s)")
        # CDN URL
        url = fetch_cdn(f"https://t.me/{PUB}/{pmid}?single")
        if not url:
            url = fetch_cdn(f"https://t.me/{PUB}/{pmid}")
        print(f"[ok] CDN: {(url or 'NONE')[:80]}")
        if url:
            links.append({"part": i + 1, "mid": pmid, "url": url})
        time.sleep(0.5)
    elapsed = time.time() - t0
    print(f"[*] total: {elapsed:.1f}s for {len(MIDS)} parts")

    # save supabase
    if links and SBURL and SBKEY:
        for L in links:
            try:
                row = {"id": f"{LINK_ID}_{L['part']}", "url": L["url"],
                       "expires_at": int(time.time()) + EXP_H * 3600,
                       "created_at": int(time.time())}
                req = u.Request(f"{SBURL}/rest/v1/links", data=json.dumps(row).encode(), method="POST",
                                headers={"apikey": SBKEY, "Authorization": f"Bearer {SBKEY}",
                                         "Content-Type": "application/json",
                                         "Prefer": "resolution=merge-duplicates"})
                with u.urlopen(req, timeout=30) as r:
                    print(f"[ok] saved {L['part']} ({r.status})")
            except Exception as e:
                print(f"[!] save fail: {str(e)[:60]}")
    print("=== LINKS ===")
    for L in links:
        print(f"PART {L['part']}: {L['url']}")
    print(f"=== {len(links)} links, {elapsed:.1f}s ===")
    await app.stop()

asyncio.run(main())
