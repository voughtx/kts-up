#!/usr/bin/env python3
# inspect2.py — deep inspect posters 2123, 2131 (caption/media/pinned) + surrounding msgs
import os, sys, json, asyncio, urllib.request as q

def log(*a): print("[i2]", *a, flush=True)

KID = os.environ.get("KEY_16", "")
KHASH = os.environ.get("KEY_17", "")
SBURL = os.environ.get("KEY_20", "").rstrip("/")
SBKEY = os.environ.get("KEY_21", "")
CHAT = os.environ.get("KEY_2", "")

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
        ids = list(range(2122, 2134))
        msgs = await cli.get_messages(ch, ids=ids)
        found = {}
        for m in msgs:
            if m is not None:
                found[m.id] = m
        log(f"found {len(found)}/{len(ids)}")
        for mid in sorted(found.keys()):
            m = found[mid]
            media = "?"
            try:
                if m.photo: media = "PHOTO"
                elif m.document: media = "DOC"
                elif m.video: media = "VIDEO"
                elif m.text: media = "TEXT"
            except Exception: pass
            cap = ""
            try: cap = (m.message or "")[:80].replace("\n", " | ")
            except Exception: pass
            pinned = ""
            try:
                if m.pinned: pinned = " PINNED"
            except Exception: pass
            log(f"msg {mid} | {media}{pinned} | {cap}")
    finally:
        await cli.disconnect()
    log("DONE")

if __name__ == "__main__":
    asyncio.run(main())
    sys.exit(0)
