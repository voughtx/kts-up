# movie_poster_test.py — movie ka poster bhejo (title + release year) + pin
# TEST ke liye — production mein app.py _movie_poster() auto karta hai
import os, json, urllib.request as u, asyncio
from pyrogram import Client, enums

K2 = os.environ.get("KEY_2", "").strip()
PSESS = os.environ.get("KEY_19", "").strip()
AID = os.environ.get("KEY_16", "").strip()
AHASH = os.environ.get("KEY_17", "").strip()
API = os.environ.get("KEY_8", "").strip()
MID = os.environ.get("MOVIE_ID", "").strip()
PIN = os.environ.get("PIN", "0").strip() == "1"

def esc(s):
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

async def main():
    app = Client("mpsess", session_string=PSESS, api_id=int(AID) if AID else None,
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
    # fetch movie
    h = {"User-Agent": "Mozilla/5.0", "Accept": "application/json",
         "Origin": "https://kartoons.me", "Referer": "https://kartoons.me/"}
    req = u.Request(f"{API}/movies/{MID}", headers=h)
    with u.urlopen(req, timeout=30) as r:
        d = json.loads(r.read().decode()).get("data", {})
    title = d.get("title") or ""
    img = d.get("image") or ""
    year = d.get("releaseYear") or 0
    cap = f"\U0001F3AC <b>{esc(title)}</b>"
    if year:
        cap += f"\n\U0001F4C5 <b>{year}</b>"
    print("[*] poster caption:", cap.replace("\n", " | "))
    tmp = "/tmp/mposter.jpg"
    with u.urlopen(u.Request(img, headers={"User-Agent": "Mozilla/5.0"}), timeout=60) as r:
        with open(tmp, "wb") as f:
            f.write(r.read())
    msg = await app.send_photo(chat.id, tmp, caption=cap, parse_mode=enums.ParseMode.HTML)
    print(f"[ok] poster sent mid {msg.id}")
    if PIN:
        try:
            await app.pin_chat_message(chat.id, msg.id)
            print(f"[ok] pinned {msg.id}")
        except Exception as e:
            print(f"[!] pin fail: {str(e)[:60]}")
    await app.stop()

asyncio.run(main())
