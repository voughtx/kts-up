#!/usr/bin/env python3
# diag_tool.py — postctl/claims/sessions dump (kts)
import os, sys, json, asyncio, urllib.request as q

def log(*a): print("[diag]", *a, flush=True)

KID = os.environ.get("KEY_16", "")
KHASH = os.environ.get("KEY_17", "")
SBURL = os.environ.get("KEY_20", "").rstrip("/")
SBKEY = os.environ.get("KEY_21", "")
MURI = os.environ.get("KEY_7", "")

def sb_get(path):
    req = q.Request(SBURL + path, headers={"apikey": SBKEY, "Authorization": "Bearer " + SBKEY})
    with q.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())

def main():
    log("== MONGO STATE ==")
    if MURI:
        try:
            import pymongo
        except Exception:
            import subprocess
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "pymongo[srv]"])
            import pymongo
        mc = pymongo.MongoClient(MURI, serverSelectionTimeoutMS=10000)
        db = mc.get_database("kts")
        pc = db.postctl.find_one({"_id": "post"}) or {}
        log("postctl:", json.dumps(pc))
        claims = list(db.claims.find({}).sort("at", 1))
        log(f"claims count: {len(claims)}")
        import time
        now = int(time.time())
        for c in claims:
            age = now - (c.get("at") or 0)
            log(f"  claim {c['_id']} age={age}s ({age//60}min)")
        # last 12 done episodes
        done = list(db.episodes.find({}, {"id": 1, "mid": 1}).sort("at", -1).limit(12))
        log("last done episodes:")
        for d in done:
            log(f"  mid={d.get('mid')} {d.get('id')}")
        # state doc (progress)
        pr = db.progress.find_one({"_id": "main"}) or {}
        log("progress main keys:", list(pr.keys())[:10])
        mc.close()
    else:
        log("KEY_7 missing")
    log("== SESSIONS (quick connect test) ==")
    try:
        st = (sb_get("/rest/v1/progress?select=state&id=eq.bot_sessions&limit=1") or [{}])[0].get("state") or {}
        bots = {k: v for k, v in st.items() if isinstance(v, list) and len(v) >= 1}
        log("bots:", {k: len(v) for k, v in bots.items()})
        from telethon import TelegramClient
        from telethon.sessions import StringSession
        for bname in sorted(bots.keys()):
            try:
                async def test():
                    c = TelegramClient(StringSession(bots[bname][0]), int(KID), KHASH, connection_retries=1, request_retries=1)
                    await c.connect()
                    me = await c.get_me()
                    await c.disconnect()
                    return getattr(me, "username", None) or getattr(me, "id", None)
                who = asyncio.run(test())
                log(f"  {bname}: OK -> {who}")
            except Exception as ex:
                log(f"  {bname}: FAIL {str(ex)[:100]}")
    except Exception as ex:
        log("sessions err:", str(ex)[:120])

if __name__ == "__main__":
    main()
    sys.exit(0)
