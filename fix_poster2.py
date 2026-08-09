#!/usr/bin/env python3
# fix_poster2.py — inspect + fix msg 2084 (Gon poster): correct image + full caption + PIN
import os, sys, json, asyncio, urllib.request as q

def log(*a): print("[fp2]", *a, flush=True)

KID = os.environ.get("KEY_16", "")
KHASH = os.environ.get("KEY_17", "")
SBURL = os.environ.get("KEY_20", "").rstrip("/")
SBKEY = os.environ.get("KEY_21", "")
CHAT = os.environ.get("KEY_2", "")

POSTER_MID = 2084
SHOW_ID = "68135629a8180912513e807c"  # Gon The Stone Age Boy

def sb_get(path):
    req = q.Request(SBURL + path, headers={"apikey": SBKEY, "Authorization": "Bearer " + SBKEY})
    with q.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())

def load_sessions():
    st = (sb_get("/rest/v1/progress?select=state&id=eq.bot_sessions&limit=1") or [{}])[0].get("state") or {}
    return {k: v for k, v in st.items() if isinstance(v, list) and len(v) >= 1}

async def connect(sess):
    from telethon import TelegramClient
    from telethon.sessions import StringSession
    cli = TelegramClient(StringSession(sess), int(KID), KHASH, connection_retries=2, request_retries=2)
    await cli.connect()
    return cli

async def main():
    # fetch Gon show info
    img = ""
    title = "Gon The Stone Age Boy"
    seasons_n = 1
    eps = 37
    try:
        r = q.Request(f"https://api.kartoons.me/api/shows/{SHOW_ID}", headers={"User-Agent": "Mozilla/5.0"})
        with q.urlopen(r, timeout=30) as resp:
            d = json.loads(resp.read().decode()).get("data") or {}
        img = d.get("image") or ""
        title = d.get("title") or title
        ss = [s for s in (d.get("seasons") or []) if s.get("_id") and (s.get("seasonNumber") or 0) != 0]
        seasons_n = len(ss)
        eps = 0
        for s in ss:
            r2 = q.Request(f"https://api.kartoons.me/api/shows/{SHOW_ID}/season/{s['_id']}/all-episodes", headers={"User-Agent": "Mozilla/5.0"})
            with q.urlopen(r2, timeout=30) as resp2:
                j2 = json.loads(resp2.read().decode())
            eps += len([e for e in (j2.get("data") or []) if e.get("_id")])
    except Exception as ex:
        log("api fetch fail:", str(ex)[:80])
    cap = f"<b>{title}</b>\nTotal \u2022 S{seasons_n} | Ep{eps}"
    log(f"show: {title} | img: {img[:60]} | S{seasons_n} | Ep{eps}")
    log(f"caption: {cap!r}")

    bots = load_sessions()
    bname = "bot1" if "bot1" in bots else sorted(bots.keys())[0]
    cli = await connect(bots[bname][0])
    try:
        ch = int(CHAT) if str(CHAT).lstrip("-").isdigit() else CHAT
        # 1) inspect current msg
        msgs = await cli.get_messages(ch, ids=[POSTER_MID])
        for m in msgs:
            if m is None:
                log(f"msg {POSTER_MID} NOT FOUND")
                continue
            media = "?"
            try:
                if m.photo: media = "PHOTO"
                elif m.document: media = "DOC"
                elif m.text: media = "TEXT"
            except Exception: pass
            log(f"msg {m.id} | {media} | caption: {(m.message or '')[:80]!r}")
        # 2) download correct image
        tmp = "/tmp/gon_poster.jpg"
        try:
            req = q.Request(img, headers={"User-Agent": "Mozilla/5.0"})
            with q.urlopen(req, timeout=60) as resp:
                with open(tmp, "wb") as f:
                    f.write(resp.read())
            log(f"image downloaded: {os.path.getsize(tmp)} bytes")
        except Exception as ex:
            log(f"image download FAIL: {str(ex)[:100]}")
            await cli.disconnect()
            return
        # 3) edit message (media + caption)
        try:
            res = await cli.edit_message(ch, POSTER_MID, file=tmp, text=cap, parse_mode="html")
            log(f"EDIT OK: msg {res.id}")
        except Exception as ex:
            log(f"edit FAIL: {str(ex)[:200]}")
            await cli.disconnect()
            return
        # 4) PIN the message
        try:
            await cli.pin_message(ch, POSTER_MID)
            log(">>> PINNED OK!")
        except Exception as ex:
            log(f"pin FAIL: {str(ex)[:150]}")
    finally:
        await cli.disconnect()
    log("DONE")

if __name__ == "__main__":
    asyncio.run(main())
    sys.exit(0)
