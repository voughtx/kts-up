#!/usr/bin/env python3
# edit_poster.py — inspect msg 2031 (poster) + fix caption/image
import os, sys, json, asyncio, urllib.request as q

def log(*a): print("[ep]", *a, flush=True)

KID = os.environ.get("KEY_16", "")
KHASH = os.environ.get("KEY_17", "")
SBURL = os.environ.get("KEY_20", "").rstrip("/")
SBKEY = os.environ.get("KEY_21", "")
CHAT = os.environ.get("KEY_2", "")

POSTER_MID = 2031
# Expected: Kick Buttowski poster — correct image + caption
KICKB_IMG = "https://image.tmdb.org/t/p/w500/l6ZQhEHjtOd9t6lOvVGzs5YEHcG.jpg"
# fetch real image url from API instead
import urllib.parse as up

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
    # fetch kick buttowski show info from API
    img = ""
    title = "Kick Buttowski: Suburban Daredevil"
    seasons = 2
    eps = 52
    try:
        import urllib.request as qu
        r = qu.Request("https://api.kartoons.me/api/shows/69d1e50e6e1f7f50c4bb0f40", headers={"User-Agent": "Mozilla/5.0"})
        with qu.urlopen(r, timeout=30) as resp:
            d = json.loads(resp.read().decode()).get("data") or {}
        img = d.get("image") or ""
        title = d.get("title") or title
        ss = [s for s in (d.get("seasons") or []) if s.get("_id") and (s.get("seasonNumber") or 0) != 0]
        seasons = len(ss)
        eps = 0
        for s in ss:
            r2 = qu.Request(f"https://api.kartoons.me/api/shows/69d1e50e6e1f7f50c4bb0f40/season/{s['_id']}/all-episodes", headers={"User-Agent": "Mozilla/5.0"})
            with qu.urlopen(r2, timeout=30) as resp2:
                j2 = json.loads(resp2.read().decode())
            eps += len([e for e in (j2.get("data") or []) if e.get("_id")])
    except Exception as ex:
        log("api fetch fail:", str(ex)[:80])
    log(f"show: {title} | img: {img[:60]} | S{seasons} | Ep{eps}")
    cap = f"<b>{title}</b>\nTotal \u2022 S{seasons} | Ep{eps}"

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
            log(f"msg {m.id} | {media} | caption: {(m.message or '')[:60]}")
        # 2) download correct image
        tmp = "/tmp/kickb_poster.jpg"
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
        # 3) EDIT the message media + caption
        try:
            from telethon.tl.types import InputMediaUploadedPhoto
            res = await cli.edit_message(ch, POSTER_MID, file=tmp, caption=cap, parse_mode="html")
            log(f"EDIT RESULT: msg {res.id} | new caption: {(res.message or '')[:60]}")
            log(">>> POSTER EDITED OK!")
        except Exception as ex:
            log(f"edit FAIL: {str(ex)[:200]}")
    finally:
        await cli.disconnect()
    log("DONE")

if __name__ == "__main__":
    asyncio.run(main())
    sys.exit(0)
