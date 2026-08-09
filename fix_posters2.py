#!/usr/bin/env python3
# fix_posters2.py — edit posters 2123 (Takopi) + 2131 (Kiteretsu) with CORRECT show images + full captions (stay pinned)
import os, sys, json, asyncio, urllib.request as q

def log(*a): print("[fp3]", *a, flush=True)

KID = os.environ.get("KEY_16", "")
KHASH = os.environ.get("KEY_17", "")
SBURL = os.environ.get("KEY_20", "").rstrip("/")
SBKEY = os.environ.get("KEY_21", "")
CHAT = os.environ.get("KEY_2", "")

# (message_id, show_id, show_title)
TARGETS = [
    (2123, "699d51646befdca0902b5eaa", "Takopi's Original Sin"),
    (2131, "68b5b2c2d862b6766f3958c0", "Kiteretsu Daihyakka"),
]

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
    bots = load_sessions()
    bname = "bot1" if "bot1" in bots else sorted(bots.keys())[0]
    cli = await connect(bots[bname][0])
    try:
        ch = int(CHAT) if str(CHAT).lstrip("-").isdigit() else CHAT
        for mid, show_id, title in TARGETS:
            log(f"\n=== msg {mid} | {title} ===")
            # fetch show info
            img = ""
            seasons_n = 1
            eps = 0
            try:
                r = q.Request(f"https://api.kartoons.me/api/shows/{show_id}", headers={"User-Agent": "Mozilla/5.0"})
                with q.urlopen(r, timeout=30) as resp:
                    d = json.loads(resp.read().decode()).get("data") or {}
                img = d.get("image") or ""
                title = d.get("title") or title
                ss = [s for s in (d.get("seasons") or []) if s.get("_id") and (s.get("seasonNumber") or 0) != 0]
                seasons_n = len(ss)
                for s in ss:
                    r2 = q.Request(f"https://api.kartoons.me/api/shows/{show_id}/season/{s['_id']}/all-episodes", headers={"User-Agent": "Mozilla/5.0"})
                    with q.urlopen(r2, timeout=30) as resp2:
                        j2 = json.loads(resp2.read().decode())
                    eps += len([e for e in (j2.get("data") or []) if e.get("_id")])
            except Exception as ex:
                log(f"api fail: {str(ex)[:80]}")
            cap = f"<b>{title}</b>\nTotal \u2022 S{seasons_n} | Ep{eps}"
            log(f"img: {img[:70]}")
            log(f"cap: {cap!r}")
            # download correct image
            tmp = f"/tmp/poster_{mid}.jpg"
            try:
                req = q.Request(img, headers={"User-Agent": "Mozilla/5.0"})
                with q.urlopen(req, timeout=60) as resp:
                    with open(tmp, "wb") as f:
                        f.write(resp.read())
                log(f"img downloaded: {os.path.getsize(tmp)} bytes")
            except Exception as ex:
                log(f"img download FAIL: {str(ex)[:100]}")
                continue
            # check current msg
            msgs = await cli.get_messages(ch, ids=[mid])
            for m in msgs:
                if m is not None:
                    log(f"current: {m.id} | pinned={getattr(m,'pinned',False)} | {(m.message or '')[:50]!r}")
            # edit
            try:
                res = await cli.edit_message(ch, mid, file=tmp, text=cap, parse_mode="html")
                log(f"EDIT OK: msg {res.id} | pinned={getattr(res,'pinned',False)}")
            except Exception as ex:
                log(f"edit FAIL: {str(ex)[:150]}")
                continue
            # ensure pinned
            try:
                await cli.pin_message(ch, mid)
                log(">>> RE-PINNED OK")
            except Exception as ex:
                log(f"pin FAIL: {str(ex)[:120]}")
    finally:
        await cli.disconnect()
    log("DONE")

if __name__ == "__main__":
    asyncio.run(main())
    sys.exit(0)
