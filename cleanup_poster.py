# KTS cleanup_poster.py — channel top cleanup + show poster
# 1. S1E1 se upar wale test messages delete karo
# 2. Show ka poster photo send karo caption ke saath + pin karo
import os, json, time, urllib.request as u

K2 = os.environ.get("KEY_2", "").strip()
SBURL = os.environ.get("KEY_20", "").strip().rstrip("/")
SBKEY = os.environ.get("KEY_21", "").strip()
PSESS = os.environ.get("KEY_19", "").strip()
AID = os.environ.get("KEY_16", "").strip()
AHASH = os.environ.get("KEY_17", "").strip()
SHOWID = os.environ.get("SHOW_ID", "").strip()
API = os.environ.get("KEY_8", "").strip()

def esc(s):
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def sb_get_first_mid():
    req = u.Request(f"{SBURL}/rest/v1/episodes?select=mid&order=mid.asc&limit=1",
                    headers={"apikey": SBKEY, "Authorization": f"Bearer {SBKEY}"})
    with u.urlopen(req, timeout=30) as r:
        rows = json.loads(r.read().decode())
    return int(rows[0]["mid"]) if rows else None

def fetch_show():
    h = {"User-Agent": "Mozilla/5.0", "Accept": "application/json",
         "Origin": "https://kartoons.me", "Referer": "https://kartoons.me/"}
    req = u.Request(f"{API}/shows/{SHOWID}", headers=h)
    with u.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode()).get("data", {})

def main():
    from pyrogram import Client, enums
    import asyncio

    show = fetch_show()
    title = show.get("title") or ""
    img = show.get("image") or ""
    seasons = [s for s in (show.get("seasons") or []) if s.get("_id")]
    tot_eps = 0
    h = {"User-Agent": "Mozilla/5.0", "Accept": "application/json",
         "Origin": "https://kartoons.me", "Referer": "https://kartoons.me/"}
    for s in seasons:
        try:
            req = u.Request(f"{API}/shows/{SHOWID}/season/{s['_id']}/all-episodes", headers=h)
            with u.urlopen(req, timeout=30) as r:
                ej = json.loads(r.read().decode())
            tot_eps += len(ej.get("data") or [])
        except Exception:
            pass
    n_seasons = len([s for s in seasons if (s.get("seasonNumber") or 0) != 0]) or len(seasons)
    cap = f"<b>{esc(title)}</b>\nTotal S{n_seasons} | Ep{tot_eps}"
    print(f"[*] poster caption: {cap}")

    async def run():
        app = Client("fixsess", session_string=PSESS, api_id=int(AID) if AID else None,
                     api_hash=AHASH or None, no_updates=True)
        await app.start()
        chat = None
        try:
            chat = await app.get_chat(int(K2))
        except Exception:
            print("[!] get_chat fail — dialogs scan...")
            async for d in app.get_dialogs():
                if d.chat and d.chat.id == int(K2):
                    chat = d.chat
                    break
        if chat is None:
            print("[x] channel resolve fail")
            await app.stop()
            return
        print(f"[*] target resolved: {chat.title}")

        # 1. delete test messages above first episode
        first_mid = sb_get_first_mid()
        print(f"[*] first episode mid: {first_mid}")
        if first_mid:
            del_ids = []
            async for m in app.get_chat_history(chat.id, offset_id=first_mid, limit=100):
                if m.id < first_mid:
                    del_ids.append(m.id)
            print(f"[*] messages above: {len(del_ids)}")
            if del_ids:
                # delete in chunks of 100
                for i in range(0, len(del_ids), 100):
                    chunk = del_ids[i:i+100]
                    try:
                        await app.delete_messages(chat.id, chunk)
                        print(f"[ok] deleted {len(chunk)}")
                    except Exception as e:
                        print(f"[!] delete fail: {str(e)[:60]}")
                    time.sleep(0.5)

        # 2. download poster + send + pin
        if img:
            tmp = "/tmp/poster.jpg"
            try:
                with u.urlopen(u.Request(img, headers={"User-Agent": "Mozilla/5.0"}), timeout=60) as r:
                    with open(tmp, "wb") as f:
                        f.write(r.read())
                msg = await app.send_photo(chat.id, tmp, caption=cap, parse_mode=enums.ParseMode.HTML)
                try:
                    await app.pin_chat_message(chat.id, msg.id)
                    print("[ok] poster sent + pinned")
                except Exception as e:
                    print(f"[!] pin fail: {str(e)[:60]} (poster sent though)")
            except Exception as e:
                print(f"[!] poster fail: {str(e)[:80]}")
        else:
            print("[!] no poster image")

        await app.stop()

    asyncio.run(run())

if __name__ == "__main__":
    main()
