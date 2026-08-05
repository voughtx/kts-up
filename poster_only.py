# poster_only.py — sirf show ka poster send + pin (delete nahi karta)
import os, json, urllib.request as u, asyncio
from pyrogram import Client, enums

K2 = os.environ.get("KEY_2", "").strip()
PSESS = os.environ.get("KEY_19", "").strip()
AID = os.environ.get("KEY_16", "").strip()
AHASH = os.environ.get("KEY_17", "").strip()
SHOWID = os.environ.get("SHOW_ID", "").strip()
API = os.environ.get("KEY_8", "").strip()

def esc(s):
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

async def main():
    app = Client("postersess", session_string=PSESS, api_id=int(AID) if AID else None,
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
        print("[x] channel resolve fail")
        await app.stop()
        return
    print(f"[*] target: {chat.title}")

    h = {"User-Agent": "Mozilla/5.0", "Accept": "application/json",
         "Origin": "https://kartoons.me", "Referer": "https://kartoons.me/"}
    if not (API and SHOWID):
        print("[!] API/SHOW_ID missing")
        await app.stop()
        return
    try:
        req = u.Request(f"{API}/shows/{SHOWID}", headers=h)
        with u.urlopen(req, timeout=30) as r:
            sj = json.loads(r.read().decode()).get("data", {})
    except Exception as e:
        print("[!] show fetch fail:", str(e)[:80])
        await app.stop()
        return
    title = sj.get("title") or ""
    img = sj.get("image") or ""
    seasons = [s for s in (sj.get("seasons") or []) if s.get("_id")]
    tot = 0
    for s in seasons:
        try:
            req2 = u.Request(f"{API}/shows/{SHOWID}/season/{s['_id']}/all-episodes", headers=h)
            with u.urlopen(req2, timeout=30) as r2:
                tot += len(json.loads(r2.read().decode()).get("data") or [])
        except Exception:
            pass
    n_seasons = len([s for s in seasons if (s.get("seasonNumber") or 0) != 0]) or len(seasons)
    cap = f"<b>{esc(title)}</b>\nTotal S{n_seasons} | Ep{tot}"
    print("[*] poster:", title, "| S", n_seasons, "| Ep", tot)
    if not img:
        print("[!] no image")
        await app.stop()
        return
    tmp = "/tmp/poster_h.jpg"
    try:
        with u.urlopen(u.Request(img, headers={"User-Agent": "Mozilla/5.0"}), timeout=60) as r:
            with open(tmp, "wb") as f:
                f.write(r.read())
        msg = await app.send_photo(chat.id, tmp, caption=cap, parse_mode=enums.ParseMode.HTML)
        try:
            await app.pin_chat_message(chat.id, msg.id)
            print(f"[ok] poster sent + pinned (mid {msg.id})")
        except Exception as e:
            print(f"[ok] poster sent (pin fail: {str(e)[:40]}) (mid {msg.id})")
    except Exception as e:
        print("[!] poster fail:", str(e)[:80])
    await app.stop()

asyncio.run(main())
