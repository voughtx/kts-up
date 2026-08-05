# reorder_v3.py — FINAL order fix (Telegram display = date order: oldest TOP, newest BOTTOM)
# Copy sequence = display order (top -> bottom):
#   1. CLASSIC poster (photo)          -> TOP
#   2. CLASSIC E1, E2, ... E77
#   3. HUNGAMA poster (photo)
#   4. HUNGAMA E1                      -> BOTTOM
# Purane messages (283-362) delete after all copies succeed.
# Supabase + Mongo updated with new mids. E1 category/lang fixed.
import os, json, time, urllib.request as u

K2 = os.environ.get("KEY_2", "").strip()
SBURL = os.environ.get("KEY_20", "").strip().rstrip("/")
SBKEY = os.environ.get("KEY_21", "").strip()
PSESS = os.environ.get("KEY_19", "").strip()
AID = os.environ.get("KEY_16", "").strip()
AHASH = os.environ.get("KEY_17", "").strip()
K7 = os.environ.get("KEY_7", "").strip()

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
    cat = d.get("category") or "Cartoon"
    lines.append(f"\U0001F5F3\uFE0F Category: <b>{esc(tlab)} \u2022 {esc(cat)}</b>")
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

def main():
    from pyrogram import Client, enums
    import asyncio

    async def run():
        app = Client("r3sess", session_string=PSESS, api_id=int(AID) if AID else None,
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
        classic.sort(key=lambda e: e.get("episode") or 0)   # E1, E2, ... E77
        hungama.sort(key=lambda e: e.get("episode") or 0)   # E1
        print(f"[*] classic: {len(classic)} | hungama: {len(hungama)}")

        # source mids (current channel): poster 362, C E1=361 ... C E77=285, H poster=284, H E1=283
        # verify mapping source->episode
        src_by_ep = {}
        for e in classic:
            src_by_ep[("C", e.get("episode"))] = int(e["mid"])
        for e in hungama:
            src_by_ep[("H", e.get("episode"))] = int(e["mid"])
        c_poster_src = 362
        h_poster_src = 284
        print(f"[*] C poster src: {c_poster_src} | H poster src: {h_poster_src}")

        new_ids = set()
        new_mid_by_id = {}
        all_ok = True

        # 1. CLASSIC poster (TOP)
        try:
            m = await app.copy_message(chat.id, chat.id, c_poster_src,
                                       caption="Doraemon (CLASSIC)\nTotal: S1 | E77",
                                       parse_mode=enums.ParseMode.HTML)
            new_ids.add(m.id)
            print(f"[ok] CLASSIC poster -> {m.id}")
            time.sleep(0.5)
        except Exception as ex:
            print(f"[x] C poster copy fail: {str(ex)[:80]}")
            all_ok = False

        # 2. CLASSIC E1..E77 (ascending)
        for e in classic:
            src = src_by_ep.get(("C", e.get("episode")))
            cap = build_caption(e, None, showname="Doraemon (CLASSIC)")
            try:
                m = await app.copy_message(chat.id, chat.id, src, caption=cap, parse_mode=enums.ParseMode.HTML)
                new_ids.add(m.id)
                new_mid_by_id[e["id"]] = m.id
                sb_patch(e["id"], {"mid": m.id, "turl": f"https://t.me/c/{str(K2).replace('-100','')}/{m.id}",
                                   "fid": m.document.file_id if m.document else "",
                                   "category": e.get("category") or "Cartoon",
                                   "lang": e.get("lang") or "Hindi"})
                print(f"[C] E{e.get('episode')} {src} -> {m.id}")
            except Exception as ex:
                print(f"[x] C E{e.get('episode')} copy fail: {str(ex)[:60]}")
                all_ok = False
            time.sleep(0.45)

        # 3. HUNGAMA poster
        try:
            m = await app.copy_message(chat.id, chat.id, h_poster_src,
                                       caption="Doraemon (HUNGAMA)\nTotal \u2022 S22 | Ep1095",
                                       parse_mode=enums.ParseMode.HTML)
            new_ids.add(m.id)
            print(f"[ok] HUNGAMA poster -> {m.id}")
            time.sleep(0.5)
        except Exception as ex:
            print(f"[x] H poster copy fail: {str(ex)[:80]}")
            all_ok = False

        # 4. HUNGAMA E1..EN (ascending, bottom)
        for e in hungama:
            src = src_by_ep.get(("H", e.get("episode")))
            cap = build_caption(e, None, showname="Doraemon (HUNGAMA)")
            try:
                m = await app.copy_message(chat.id, chat.id, src, caption=cap, parse_mode=enums.ParseMode.HTML)
                new_ids.add(m.id)
                new_mid_by_id[e["id"]] = m.id
                sb_patch(e["id"], {"mid": m.id, "turl": f"https://t.me/c/{str(K2).replace('-100','')}/{m.id}",
                                   "fid": m.document.file_id if m.document else ""})
                print(f"[H] E{e.get('episode')} {src} -> {m.id}")
            except Exception as ex:
                print(f"[x] H E{e.get('episode')} copy fail: {str(ex)[:60]}")
                all_ok = False
            time.sleep(0.45)

        if not all_ok:
            print("[x] ABORT — koi copy fail hua, delete SKIP")
            await app.stop()
            return

        # 5. PIN CLASSIC poster (sabse pehla naya message = top)
        first_new = min(new_ids)
        try:
            await app.pin_chat_message(chat.id, first_new)
            print(f"[ok] pinned CLASSIC poster {first_new}")
        except Exception as ex:
            print(f"[!] pin fail: {str(ex)[:60]}")

        # 6. DELETE purane (283..362 + koi bhi jo naya nahi)
        old = []
        async for m in app.get_chat_history(chat.id, limit=1000):
            if m.id not in new_ids and m.id != 1:
                old.append(m.id)
        print(f"[*] delete old: {len(old)}")
        for i in range(0, len(old), 100):
            try:
                await app.delete_messages(chat.id, old[i:i+100])
            except Exception as ex:
                print(f"[!] del fail: {str(ex)[:50]}")
            time.sleep(0.3)
        print(f"[ok] deleted {len(old)}")

        # 7. Mongo update
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

        # 8. verify TOP (oldest = top in Telegram)
        all_mids = []
        async for m in app.get_chat_history(chat.id, limit=200):
            all_mids.append(m.id)
        top_mids = sorted(all_mids)[:12]  # sabse chhote ids = sabse purane = top
        print("--- TOP 12 (oldest) ---")
        for mid in top_mids:
            m = await app.get_messages(chat.id, mid)
            cap = (m.caption or "").replace("\n", " | ")[:45] if m.caption else ""
            print(m.id, "|", ("doc" if m.document else ("photo" if m.photo else "?")), "|", cap)
        print(f"[done] reorder v3 — copies: {len(new_ids)}")
        await app.stop()

    asyncio.run(run())

if __name__ == "__main__":
    main()
