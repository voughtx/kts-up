# KTS reorder_channel.py — channel messages ko reorder karta hai:
# poster (top) → E1 → E2 → ... → E77 (bottom)
# copy_message = server-side copy, NO forward tag. Purane delete baad mein.
# Supabase + MongoDB update (mid/turl/fid) naye ids ke saath.
import os, json, time, urllib.request as u

K2 = os.environ.get("KEY_2", "").strip()
SBURL = os.environ.get("KEY_20", "").strip().rstrip("/")
SBKEY = os.environ.get("KEY_21", "").strip()
PSESS = os.environ.get("KEY_19", "").strip()
AID = os.environ.get("KEY_16", "").strip()
AHASH = os.environ.get("KEY_17", "").strip()
K7 = os.environ.get("KEY_7", "").strip()
API = os.environ.get("KEY_8", "").strip()
SHOWID = os.environ.get("SHOW_ID", "").strip()

def esc(s):
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

SEP = "\u25AC" * 18

def build_caption(d, dur=None):
    lines = []
    if d.get("title"):
        lines.append(f"\U0001F3AC <b><code>{esc(d['title'])}</code></b>")
    show = d.get("show") or ""
    se = None
    if d.get("season") is not None and d.get("episode") is not None:
        se = f"S{d['season']}-E{d['episode']}"
    if show and se:
        lines.append(f"\U0001F4C0 <b><code>{esc(show)} \u00B7 {se}</code></b>")
    elif show:
        lines.append(f"\U0001F4C0 <b><code>{esc(show)}</code></b>")
    lines.append(SEP)
    if d.get("quality"):
        lines.append(f"\u2699\uFE0F Quality: <b>{esc(d['quality'])}</b>")
    lines.append(f"\U0001F4AC Language: <b>{esc(d.get('lang') or 'Hindi')}</b>")
    sz = ""
    size = d.get("size") or 0
    if size:
        mb = size / (1024 * 1024)
        if mb >= 1024:
            sz = f"{int(round(mb/1024))} GB"
        else:
            sz = f"{int(round(mb))} MB"
    if dur:
        if sz:
            sz = f"{sz} \u2022 {int(dur)} min"
        else:
            sz = f"{int(dur)} min"
    if sz:
        lines.append(f"\U0001F4C2 Size: <b>{sz}</b>")
    tlab = "Movie" if (d.get("type") or "").startswith("movie") else "Show"
    clab = d.get("category") or ""
    lines.append(f"\U0001F5F3\uFE0F Category: <b>{esc(tlab)} \u2022 {esc(clab)}</b>")
    lines.append(SEP)
    tgt = ""
    web = d.get("web") or ""
    thumb = d.get("thumb") or ""
    if web:
        dom = web.split("//")[-1].split("/")[0]
        lab = dom.split(".")[0].capitalize() if "." in dom else dom
        tgt = f"<b><a href=\"{esc(web)}\">{esc(lab)}</a></b>"
    if tgt and thumb:
        lines.append(f"\U0001F3AF {tgt} | <b><a href=\"{esc(thumb)}\">Thumbnail</a></b>")
    elif tgt:
        lines.append(f"\U0001F3AF {tgt}")
    elif thumb:
        lines.append(f"\U0001F3AF <b><a href=\"{esc(thumb)}\">Thumbnail</a></b>")
    return "\n".join(lines)

def sb_get_episodes():
    req = u.Request(f"{SBURL}/rest/v1/episodes?select=*&limit=500&order=mid.asc",
                    headers={"apikey": SBKEY, "Authorization": f"Bearer {SBKEY}"})
    with u.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())

def sb_patch(id_, data):
    req = u.Request(f"{SBURL}/rest/v1/episodes?id=eq.{u.quote(id_)}", data=json.dumps(data).encode(),
                    method="PATCH",
                    headers={"apikey": SBKEY, "Authorization": f"Bearer {SBKEY}",
                             "Content-Type": "application/json", "Prefer": "return=minimal"})
    with u.urlopen(req, timeout=30) as r:
        return r.status

def fetch_durations():
    if not (API and SHOWID):
        return {}
    out = {}
    try:
        h = {"User-Agent": "Mozilla/5.0", "Accept": "application/json",
             "Origin": "https://kartoons.me", "Referer": "https://kartoons.me/"}
        req = u.Request(f"{API}/shows/{SHOWID}", headers=h)
        with u.urlopen(req, timeout=30) as r:
            sj = json.loads(r.read().decode())
        seasons = [s for s in (sj.get("data", {}).get("seasons") or []) if s.get("_id")]
        for s in seasons:
            req2 = u.Request(f"{API}/shows/{SHOWID}/season/{s['_id']}/all-episodes", headers=h)
            with u.urlopen(req2, timeout=30) as r2:
                ej = json.loads(r2.read().decode())
            for e in (ej.get("data") or []):
                out[e.get("_id")] = (e.get("durationMinutes") or 0, e.get("image") or "")
    except Exception as ex:
        print(f"[!] durations fetch fail: {str(ex)[:80]}")
    return out

def main():
    from pyrogram import Client, enums
    import asyncio

    durs = fetch_durations()
    print(f"[*] durations map: {len(durs)}")

    async def run():
        app = Client("reordersess", session_string=PSESS, api_id=int(AID) if AID else None,
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
        print(f"[*] target: {chat.title} ({chat.id})")

        eps = sb_get_episodes()
        eps = [e for e in eps if e.get("mid") and e.get("episode") is not None]
        eps.sort(key=lambda e: (e.get("season") or 0, e.get("episode") or 0), reverse=True)  # E77 first
        print(f"[*] episodes to reorder: {len(eps)}")

        # 1. COPY (reverse: E77 sabse pehle = bottom, E1 upar, poster sabse last = top)
        mapping = {}  # old_mid -> new_mid
        for i, e in enumerate(eps):
            old_mid = int(e["mid"])
            dur_info = durs.get(e.get("id") or "", (0, ""))
            cap = build_caption(e, dur_info[0] or None)
            try:
                m = await app.copy_message(chat.id, chat.id, old_mid, caption=cap, parse_mode=enums.ParseMode.HTML)
                mapping[old_mid] = m.id
                fid = m.document.file_id if m.document else ""
                # thumb fix (E1): API se image mila to update
                new_thumb = dur_info[1] or e.get("thumb") or ""
                if e.get("episode") == 1 and not e.get("thumb") and new_thumb:
                    try:
                        sb_patch(e["id"], {"thumb": new_thumb})
                        print(f"   [thumb] E1 updated: {new_thumb[:60]}")
                    except Exception as ex:
                        print(f"   [thumb] fail: {str(ex)[:50]}")
                # DB update abhi (mid/turl/fid)
                try:
                    sb_patch(e["id"], {"mid": m.id, "turl": f"https://t.me/c/{str(K2).replace('-100','')}/{m.id}", "fid": fid})
                except Exception as ex:
                    print(f"   [db] patch fail {old_mid}: {str(ex)[:50]}")
                print(f"   [{i+1}/{len(eps)}] E{e.get('episode')} mid {old_mid} -> {m.id}")
            except Exception as ex:
                print(f"   [x] copy fail {old_mid}: {str(ex)[:80]}")
            time.sleep(0.6)

        # 2. POSTER (sabse upar) — purana poster dhundo + delete, naya send
        poster_mid = None
        try:
            async for m in app.get_chat_history(chat.id, limit=200):
                cap = (m.caption or "") if m.caption else ""
                if m.id not in mapping.values() and "Total S" in cap:
                    poster_mid = m.id
                    break
        except Exception:
            pass
        if poster_mid:
            try:
                await app.delete_messages(chat.id, poster_mid)
                print(f"[ok] old poster deleted ({poster_mid})")
            except Exception as ex:
                print(f"[!] poster delete fail: {str(ex)[:60]}")

        # naya poster send (top)
        try:
            img = ""
            cap = ""
            h = {"User-Agent": "Mozilla/5.0", "Accept": "application/json",
                 "Origin": "https://kartoons.me", "Referer": "https://kartoons.me/"}
            if API and SHOWID:
                req = u.Request(f"{API}/shows/{SHOWID}", headers=h)
                with u.urlopen(req, timeout=30) as r:
                    sj = json.loads(r.read().decode()).get("data", {})
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
                cap = f"<b>{esc(sj.get('title') or '')}</b>\nTotal S{n_seasons} | Ep{tot}"
            if img:
                tmp = "/tmp/poster2.jpg"
                with u.urlopen(u.Request(img, headers={"User-Agent": "Mozilla/5.0"}), timeout=60) as r:
                    with open(tmp, "wb") as f:
                        f.write(r.read())
                msg = await app.send_photo(chat.id, tmp, caption=cap, parse_mode=enums.ParseMode.HTML)
                try:
                    await app.pin_chat_message(chat.id, msg.id)
                except Exception:
                    pass
                print(f"[ok] new poster sent + pinned (mid {msg.id})")
            else:
                print("[!] no poster img")
        except Exception as ex:
            print(f"[!] poster fail: {str(ex)[:80]}")

        # 3. DELETE purane (jo abhi bhi channel mein hain)
        old_ids = [int(e["mid"]) for e in eps]
        try:
            await app.delete_messages(chat.id, old_ids)
            print(f"[ok] deleted {len(old_ids)} old episode messages")
        except Exception as ex:
            print(f"[!] delete fail (kuch bache honge): {str(ex)[:80]}")

        # 4. Mongo update (best effort)
        if K7:
            try:
                import pymongo
                mc = pymongo.MongoClient(K7, serverSelectionTimeoutMS=8000)
                db = mc.get_database("kts")
                for e in eps:
                    nm = mapping.get(int(e["mid"]))
                    if nm:
                        db.episodes.update_one({"id": e["id"]}, {"$set": {"mid": nm, "turl": f"https://t.me/c/{str(K2).replace('-100','')}/{nm}"}})
                print("[ok] mongo updated")
            except Exception as ex:
                print(f"[!] mongo update fail: {str(ex)[:60]}")

        print(f"[done] reorder complete — mapping size: {len(mapping)}")
        await app.stop()

    asyncio.run(run())

if __name__ == "__main__":
    main()
