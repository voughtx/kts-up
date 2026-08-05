# reorder_v2.py — FINAL order fix:
#   TOP: CLASSIC poster (pinned) -> CLASSIC E1..E77 -> HUNGAMA poster -> HUNGAMA E1..EN (bottom)
# copy_message = server-side copy, NO forward tag. Purane delete baad mein.
# Supabase + Mongo update naye mids ke saath.
import os, json, time, urllib.request as u

K2 = os.environ.get("KEY_2", "").strip()
SBURL = os.environ.get("KEY_20", "").strip().rstrip("/")
SBKEY = os.environ.get("KEY_21", "").strip()
PSESS = os.environ.get("KEY_19", "").strip()
AID = os.environ.get("KEY_16", "").strip()
AHASH = os.environ.get("KEY_17", "").strip()
K7 = os.environ.get("KEY_7", "").strip()
API = os.environ.get("KEY_8", "").strip()
SID_H = os.environ.get("SHOW_ID", "").strip()   # HUNGAMA
SID_C = os.environ.get("SHOW_ID2", "").strip()  # CLASSIC

SEP = "\u25AC" * 18

def esc(s):
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def build_caption(d, dur=None, showname=None):
    lines = []
    if d.get("title"):
        lines.append(f"\U0001F3AC <b><code>{esc(d['title'])}</code></b>")
    show = showname or d.get("show") or ""
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
        sz = f"{int(round(mb/1024))} GB" if mb >= 1024 else f"{int(round(mb))} MB"
    if dur:
        sz = f"{sz} \u2022 {int(dur)} min" if sz else f"{int(dur)} min"
    if sz:
        lines.append(f"\U0001F4C2 Size: <b>{sz}</b>")
    tlab = "Movie" if (d.get("type") or "").startswith("movie") else "Show"
    lines.append(f"\U0001F5F3\uFE0F Category: <b>{esc(tlab)} \u2022 {esc(d.get('category') or '')}</b>")
    lines.append(SEP)
    web = d.get("web") or ""
    thumb = d.get("thumb") or ""
    tgt = ""
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
    req = u.Request(f"{SBURL}/rest/v1/episodes?select=*&limit=1000",
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

def fetch_show(sid):
    h = {"User-Agent": "Mozilla/5.0", "Accept": "application/json",
         "Origin": "https://kartoons.me", "Referer": "https://kartoons.me/"}
    out = {"title": "", "image": "", "n": 0, "tot": 0, "eps": {}}
    try:
        req = u.Request(f"{API}/shows/{sid}", headers=h)
        with u.urlopen(req, timeout=30) as r:
            sj = json.loads(r.read().decode()).get("data", {})
        out["title"] = sj.get("title") or ""
        out["image"] = sj.get("image") or ""
        seasons = [s for s in (sj.get("seasons") or []) if s.get("_id")]
        out["n"] = len([s for s in seasons if (s.get("seasonNumber") or 0) != 0]) or len(seasons)
        for s in seasons:
            try:
                req2 = u.Request(f"{API}/shows/{sid}/season/{s['_id']}/all-episodes", headers=h)
                with u.urlopen(req2, timeout=30) as r2:
                    ej = json.loads(r2.read().decode())
                for e in (ej.get("data") or []):
                    out["eps"][e.get("_id")] = (e.get("durationMinutes") or 0, e.get("image") or "")
                    out["tot"] += 1
            except Exception:
                pass
    except Exception as ex:
        print(f"[!] fetch_show {sid} fail: {str(ex)[:60]}")
    return out

def main():
    from pyrogram import Client, enums
    import asyncio

    sh_h = fetch_show(SID_H)
    sh_c = fetch_show(SID_C)
    print(f"[*] HUNGAMA: {sh_h['title']} S{sh_h['n']} Ep{sh_h['tot']}")
    print(f"[*] CLASSIC: {sh_c['title']} S{sh_c['n']} Ep{sh_c['tot']}")

    async def run():
        app = Client("r2sess", session_string=PSESS, api_id=int(AID) if AID else None,
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
        print(f"[*] target: {chat.title}")

        eps = sb_get_episodes()
        eps = [e for e in eps if e.get("mid") and e.get("episode") is not None]
        classic = [e for e in eps if (e.get("show") or "").startswith("Doraemon (CLASSIC)")]
        hungama = [e for e in eps if not (e.get("show") or "").startswith("Doraemon (CLASSIC)")]
        classic.sort(key=lambda e: e.get("episode") or 0)
        hungama.sort(key=lambda e: e.get("episode") or 0)
        print(f"[*] classic: {len(classic)} | hungama: {len(hungama)}")

        new_ids = set()
        new_mid_by_id = {}

        # HUNGAMA poster dhundo (photo + Total caption)
        hungama_poster_mid = None
        async for m in app.get_chat_history(chat.id, limit=40):
            if m.photo and m.caption and "Total" in (m.caption or ""):
                hungama_poster_mid = m.id
                break
        print(f"[*] hungama poster mid: {hungama_poster_mid}")

        # 1. HUNGAMA eps (bottom): Ep-max se Ep-1 (taaki E1 upar aaye)
        for e in reversed(hungama):
            dur = sh_h["eps"].get(e["id"], (0, ""))[0]
            cap = build_caption(e, dur, showname="Doraemon (HUNGAMA)")
            m = await app.copy_message(chat.id, chat.id, int(e["mid"]), caption=cap, parse_mode=enums.ParseMode.HTML)
            new_ids.add(m.id)
            new_mid_by_id[e["id"]] = m.id
            sb_patch(e["id"], {"mid": m.id, "turl": f"https://t.me/c/{str(K2).replace('-100','')}/{m.id}",
                               "fid": m.document.file_id if m.document else ""})
            print(f"   [H] E{e.get('episode')} mid {e['mid']} -> {m.id}")
            time.sleep(0.5)

        # 2. HUNGAMA poster (E1 ke upar)
        if hungama_poster_mid:
            cap = f"<b>Doraemon (HUNGAMA)</b>\nTotal \u2022 S{sh_h['n']} | Ep{sh_h['tot']}"
            m = await app.copy_message(chat.id, chat.id, hungama_poster_mid, caption=cap, parse_mode=enums.ParseMode.HTML)
            new_ids.add(m.id)
            print(f"   [H poster] {hungama_poster_mid} -> {m.id}")
            time.sleep(0.5)

        # 3. CLASSIC eps (E77 bottom -> E1 top of classic block)
        for e in reversed(classic):
            dur = sh_c["eps"].get(e["id"], (0, ""))[0]
            cap = build_caption(e, dur, showname="Doraemon (CLASSIC)")
            m = await app.copy_message(chat.id, chat.id, int(e["mid"]), caption=cap, parse_mode=enums.ParseMode.HTML)
            new_ids.add(m.id)
            new_mid_by_id[e["id"]] = m.id
            sb_patch(e["id"], {"mid": m.id, "turl": f"https://t.me/c/{str(K2).replace('-100','')}/{m.id}",
                               "fid": m.document.file_id if m.document else ""})
            print(f"   [C] E{e.get('episode')} mid {e['mid']} -> {m.id}")
            time.sleep(0.5)

        # 4. CLASSIC poster fresh (TOP) + pin
        if sh_c["image"]:
            tmp = "/tmp/poster_c.jpg"
            with u.urlopen(u.Request(sh_c["image"], headers={"User-Agent": "Mozilla/5.0"}), timeout=60) as r:
                with open(tmp, "wb") as f:
                    f.write(r.read())
            cap = f"<b>Doraemon (CLASSIC)</b>\nTotal \u2022 S{sh_c['n']} | Ep{sh_c['tot']}"
            msg = await app.send_photo(chat.id, tmp, caption=cap, parse_mode=enums.ParseMode.HTML)
            new_ids.add(msg.id)
            try:
                await app.pin_chat_message(chat.id, msg.id)
                print(f"[ok] CLASSIC poster {msg.id} sent + pinned")
            except Exception as ex:
                print(f"[ok] CLASSIC poster {msg.id} sent (pin fail: {str(ex)[:40]})")
        else:
            print("[!] classic poster image nahi mili")

        # 5. DELETE saare purane (jo naye nahi hain)
        old = []
        async for m in app.get_chat_history(chat.id, limit=800):
            if m.id not in new_ids and m.id != 1:
                old.append(m.id)
        print(f"[*] delete old: {len(old)}")
        for i in range(0, len(old), 100):
            try:
                await app.delete_messages(chat.id, old[i:i+100])
            except Exception as ex:
                print(f"[!] del chunk fail: {str(ex)[:50]}")
            time.sleep(0.3)
        print(f"[ok] deleted {len(old)}")

        # 6. Mongo update
        if K7:
            try:
                import pymongo
                mc = pymongo.MongoClient(K7, serverSelectionTimeoutMS=8000)
                db = mc.get_database("kts")
                for e in classic + hungama:
                    nm = new_mid_by_id.get(e["id"])
                    if nm:
                        db.episodes.update_one({"id": e["id"]},
                                               {"$set": {"mid": nm, "turl": f"https://t.me/c/{str(K2).replace('-100','')}/{nm}"}})
                print("[ok] mongo updated")
            except Exception as ex:
                print(f"[!] mongo fail: {str(ex)[:50]}")

        # 7. verify
        print("--- TOP 12 ---")
        async for m in app.get_chat_history(chat.id, limit=12):
            cap = (m.caption or "").replace("\n", " | ")[:45] if m.caption else ""
            print(m.id, "|", ("doc" if m.document else ("photo" if m.photo else "?")), "|", cap)
        print(f"[done] reorder v2 complete — copies: {len(new_ids)}")
        await app.stop()

    asyncio.run(run())

if __name__ == "__main__":
    main()
