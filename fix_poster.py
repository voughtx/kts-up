#!/usr/bin/env python3
# fix_poster.py — inspect & delete premature poster 2027 + clear lock + postctl reset to BLUE LOCK S2E12
import os, sys, json, asyncio, urllib.request as q

def log(*a): print("[fxp]", *a, flush=True)

KID = os.environ.get("KEY_16", "")
KHASH = os.environ.get("KEY_17", "")
SBURL = os.environ.get("KEY_20", "").rstrip("/")
SBKEY = os.environ.get("KEY_21", "")
MURI = os.environ.get("KEY_7", "")
CHAT = os.environ.get("KEY_2", "")

POSTER_MID = 2027
KICKB_SHOW_ID = "69d1e50e6e1f7f50c4bb0f40"  # Kick Buttowski show_posters lock to remove
SEQ = 1422  # BLUE LOCK S2E12 (Flowers) — first pending episode

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
        # 1) inspect 2027-2032
        msgs = await cli.get_messages(ch, ids=list(range(2027, 2033)))
        found = {}
        for m in msgs:
            if m is not None:
                found[m.id] = m
        log(f"msgs found: {sorted(found.keys())}")
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
            try: cap = (m.message or "")[:60].replace("\n", " ")
            except Exception: pass
            log(f"  msg {mid} | {media} | {cap}")
        # 2) delete poster 2027 + anything after it (premature poster/ghosts)
        del_ids = [i for i in range(2027, 2033) if i in found]
        if del_ids:
            r = await cli.delete_messages(ch, del_ids)
            log(f"deleted {del_ids} -> {r}")
        else:
            log("nothing to delete in 2027-2032")
    finally:
        await cli.disconnect()
    # 3) mongo: remove kickb poster lock + clear claims + postctl reset
    if MURI:
        try:
            import pymongo
        except Exception:
            import subprocess
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "pymongo[srv]"])
            import pymongo
        mc = pymongo.MongoClient(MURI, serverSelectionTimeoutMS=10000)
        db = mc.get_database("kts")
        # show_posters lock remove for kick buttowski
        try:
            r1 = db.show_posters.delete_one({"_id": KICKB_SHOW_ID})
            log(f"show_posters lock removed for {KICKB_SHOW_ID}: {r1.deleted_count}")
        except Exception as ex:
            log("show_posters err:", str(ex)[:80])
        # clear claims (stuck BLUE LOCK S2E12-14 claims)
        r2 = db.claims.delete_many({})
        log(f"claims cleared: {r2.deleted_count}")
        # postctl reset
        db.postctl.update_one({"_id": "post"}, {"$set": {"next_seq": SEQ, "lock": "", "lock_at": 0}}, upsert=True)
        pc = db.postctl.find_one({"_id": "post"}) or {}
        log(f"postctl -> next_seq={pc.get('next_seq')}")
        mc.close()
    log("DONE")

if __name__ == "__main__":
    asyncio.run(main())
    sys.exit(0)
