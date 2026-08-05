# reorder_movie.py — movie poster ko docs se PEHLE karo (fast: copy_message server-side)
# poster naya send (top) -> parts copy (001 upar, 002 neeche) -> purane delete -> DB update
import os, json, time, urllib.request as u, asyncio
from pyrogram import Client, enums

K2 = os.environ.get("KEY_2", "").strip()
SBURL = os.environ.get("KEY_20", "").strip().rstrip("/")
SBKEY = os.environ.get("KEY_21", "").strip()
PSESS = os.environ.get("KEY_19", "").strip()
AID = os.environ.get("KEY_16", "").strip()
AHASH = os.environ.get("KEY_17", "").strip()
K7 = os.environ.get("KEY_7", "").strip()
API = os.environ.get("KEY_8", "").strip()
MOVIE_ID = os.environ.get("MOVIE_ID", "").strip()

OLD_POSTER = 452
PARTS = [450, 451]  # 001, 002

def esc(s):
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

async def main():
    app = Client("rmovsess", session_string=PSESS, api_id=int(AID) if AID else None,
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
    print(f"[*] target: {chat.title}")

    # 1. last part (451) ka caption le lo (reuse)
    m451 = await app.get_messages(cid, 451)
    last_cap = m451.caption if m451.caption else None
    print("[*] last part caption len:", len(last_cap or ""))

    # 2. movie data (poster caption)
    h = {"User-Agent": "Mozilla/5.0", "Accept": "application/json",
         "Origin": "https://kartoons.me", "Referer": "https://kartoons.me/"}
    req = u.Request(f"{API}/movies/{MOVIE_ID}", headers=h)
    with u.urlopen(req, timeout=30) as r:
        d = json.loads(r.read().decode()).get("data", {})
    title = d.get("title") or ""
    img = d.get("image") or ""
    year = d.get("releaseYear") or 0
    pcap = f"\U0001F3AC <b>{esc(title)}</b>"
    if year:
        pcap += f"\n\U0001F4C5 <b>{year}</b>"
    print("[*] poster cap:", pcap.replace("\n", " | "))

    # 3. purana poster delete + parts delete (baad mein copy ke baad)
    try:
        await app.delete_messages(cid, [OLD_POSTER])
        print(f"[ok] old poster {OLD_POSTER} deleted")
    except Exception as e:
        print(f"[!] poster del fail: {str(e)[:60]}")

    # 4. naya poster send (TOP - sabse pehle)
    tmp = "/tmp/mp2.jpg"
    with u.urlopen(u.Request(img, headers={"User-Agent": "Mozilla/5.0"}), timeout=60) as r:
        with open(tmp, "wb") as f:
            f.write(r.read())
    pmsg = await app.send_photo(cid, tmp, caption=pcap, parse_mode=enums.ParseMode.HTML)
    print(f"[ok] new poster {pmsg.id}")
    time.sleep(0.5)

    # 5. parts copy (001 pehle -> upar, 002 baad -> neeche)
    new_part_ids = {}
    for i, mid in enumerate(PARTS):
        cap = last_cap if i == len(PARTS) - 1 else None
        m = await app.copy_message(cid, cid, mid, caption=cap, parse_mode=enums.ParseMode.HTML if cap else None)
        new_part_ids[mid] = m.id
        fid = m.document.file_id if m.document else ""
        print(f"[ok] part {mid} -> {m.id} (fid {fid[:25]}...)")
        time.sleep(0.5)

    # 6. purane parts delete
    try:
        await app.delete_messages(cid, PARTS)
        print(f"[ok] old parts {PARTS} deleted")
    except Exception as e:
        print(f"[!] parts del fail: {str(e)[:60]}")

    # 7. pin poster
    try:
        await app.pin_chat_message(cid, pmsg.id)
        print(f"[ok] poster pinned {pmsg.id}")
    except Exception as e:
        print(f"[!] pin fail: {str(e)[:60]}")

    # 8. DB update (movie row)
    first_new = new_part_ids[PARTS[0]]
    mf = await app.get_messages(cid, first_new)
    fid0 = mf.document.file_id if mf.document else ""
    try:
        rows = json.loads(u.urlopen(u.Request(f"{SBURL}/rest/v1/episodes?select=id&limit=1000",
                    headers={"apikey": SBKEY, "Authorization": f"Bearer {SBKEY}"}), timeout=30).read().decode())
        movie_row = [r for r in rows if str(r.get("id", "")).startswith("movie:")]
        if movie_row:
            mid_id = movie_row[0]["id"]
            turl = f"https://t.me/c/{str(K2).replace('-100','')}/{first_new}"
            req = u.Request(f"{SBURL}/rest/v1/episodes?id=eq.{u.quote(mid_id)}",
                            data=json.dumps({"mid": first_new, "turl": turl, "fid": fid0}).encode(),
                            method="PATCH", headers={"apikey": SBKEY, "Authorization": f"Bearer {SBKEY}",
                                                     "Content-Type": "application/json", "Prefer": "return=minimal"})
            with u.urlopen(req, timeout=30):
                print(f"[ok] sb movie row updated (mid={first_new})")
            if K7:
                import pymongo
                mc = pymongo.MongoClient(K7, serverSelectionTimeoutMS=8000)
                mc.get_database("kts").episodes.update_one({"id": mid_id}, {"$set": {"mid": first_new, "turl": turl}})
                print("[ok] mongo updated")
        else:
            print("[!] movie row nahi mila")
    except Exception as e:
        print(f"[!] db update fail: {str(e)[:80]}")

    # 9. verify top 6
    print("--- TOP 6 ---")
    all_mids = []
    async for m in app.get_chat_history(cid, limit=100):
        all_mids.append(m.id)
    for mid in sorted(all_mids)[:6]:
        m = await app.get_messages(cid, mid)
        cap = (m.caption or "").replace("\n", " | ")[:55] if m.caption else ""
        print(m.id, "|", ("doc" if m.document else ("photo" if m.photo else "?")), "|", cap)
    await app.stop()

asyncio.run(main())
