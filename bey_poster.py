#!/usr/bin/env python3
# bey_poster.py — delete Beyblade msgs + cleanup + POST BEYBLADE POSTER
import os, sys, json, asyncio, urllib.request as q

def log(*a): print("[bey]", *a, flush=True)

KID = os.environ.get("KEY_16", "")
KHASH = os.environ.get("KEY_17", "")
SBURL = os.environ.get("KEY_20", "").rstrip("/")
SBKEY = os.environ.get("KEY_21", "")
MURI = os.environ.get("KEY_7", "")
CHAT = os.environ.get("KEY_2", "")

DEL_FROM = 1655
DEL_TO = 1661  # hardcoded: E1-E5 (1655-1659) + posters (1660,1661)
EIDS = [
    "688c93d478acbac754fcaa55",  # S1E1
    "688c93d478acbac754fcaa56",  # S1E2
    "688c93d478acbac754fcaa57",  # S1E3
    "688c93d478acbac754fcaa58",  # S1E4
    "688c93d478acbac754fcaa59",  # S1E5
    "688c93d478acbac754fcaa5a",  # S1E6
]
SEQ = 1102
POSTER_URL = "https://image.tmdb.org/t/p/w500/l6ZQhEHjtOd9t6lOvVGzs5YEHcG.jpg"
POSTER_CAP = "<b>Beyblade (HUNGAMA)</b>\nTotal \u2022 S3 | Ep154"

def sb_get(path):
    req = q.Request(SBURL + path, headers={"apikey": SBKEY, "Authorization": "Bearer " + SBKEY})
    with q.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())

def sb_delete(path):
    req = q.Request(SBURL + path, headers={"apikey": SBKEY, "Authorization": "Bearer " + SBKEY}, method="DELETE")
    with q.urlopen(req, timeout=30) as r:
        return r.status

def load_sessions():
    st = (sb_get("/rest/v1/progress?select=state&id=eq.bot_sessions&limit=1") or [{}])[0].get("state") or {}
    return {k: v for k, v in st.items() if isinstance(v, list) and len(v) >= 1}

async def connect(sess):
    from telethon import TelegramClient
    from telethon.sessions import StringSession
    cli = TelegramClient(StringSession(sess), int(KID), KHASH, connection_retries=2, request_retries=2)
    await cli.connect()
    return cli

async def get_msgs(cli, ids):
    out = {}
    try:
        ch = int(CHAT) if str(CHAT).lstrip("-").isdigit() else CHAT
        msgs = await cli.get_messages(ch, ids=list(ids))
        for m in msgs:
            if m is not None:
                out[m.id] = m
    except Exception as ex:
        log("get_msgs err:", str(ex)[:120])
    return out

async def delete_range():
    """Delete all messages from DEL_FROM to DEL_TO (hardcoded)."""
    bots = load_sessions()
    ids = list(range(DEL_FROM, DEL_TO + 1))
    log(f"deleting msgs {DEL_FROM}-{DEL_TO} ({len(ids)} msgs)")
    deleted = set()
    for bname in sorted(bots.keys()):
        if len(deleted) == len(ids):
            break
        try:
            cli = await connect(bots[bname][0])
            try:
                ch = int(CHAT) if str(CHAT).lstrip("-").isdigit() else CHAT
                remaining = [i for i in ids if i not in deleted]
                if remaining:
                    r = await cli.delete_messages(ch, remaining)
                    log(f"{bname}: delete {len(remaining)} -> {r}")
                found = await get_msgs(cli, [i for i in ids if i not in deleted])
                for i in ids:
                    if i not in found:
                        deleted.add(i)
                log(f"{bname}: total {len(deleted)}/{len(ids)}")
            finally:
                await cli.disconnect()
        except Exception as ex:
            log(f"{bname}: FAIL {str(ex)[:150]}")
    log(f"FINAL deleted: {len(deleted)}/{len(ids)}")
    return len(deleted)

async def post_poster():
    """Download Beyblade image + send photo with caption via bot1."""
    bots = load_sessions()
    bname = "bot1" if "bot1" in bots else sorted(bots.keys())[0]
    # download poster
    tmp = "/tmp/bey_poster.jpg"
    try:
        req = q.Request(POSTER_URL, headers={"User-Agent": "Mozilla/5.0"})
        with q.urlopen(req, timeout=60) as resp:
            with open(tmp, "wb") as f:
                f.write(resp.read())
        sz = os.path.getsize(tmp)
        log(f"poster downloaded: {sz} bytes")
        if sz < 5000:
            log("poster too small — abort"); return None
    except Exception as ex:
        log(f"poster download FAIL: {str(ex)[:120]}"); return None
    try:
        cli = await connect(bots[bname][0])
        try:
            ch = int(CHAT) if str(CHAT).lstrip("-").isdigit() else CHAT
            msg = await cli.send_file(ch, tmp, caption=POSTER_CAP, parse_mode="html")
            log(f"POSTER POSTED: mid={msg.id} via {bname}")
            return msg.id
        finally:
            await cli.disconnect()
    except Exception as ex:
        log(f"poster send FAIL: {str(ex)[:150]}")
        return None

async def main():
    # 1) delete messages
    await delete_range()
    # 2) cleanup supabase
    for eid in EIDS:
        try:
            st = sb_delete(f"/rest/v1/episodes?id=eq.{eid}")
            log(f"sb del {eid[-6:]} -> {st}")
        except Exception as ex:
            log(f"sb del err {eid[-6:]}: {str(ex)[:80]}")
    # 3) mongo cleanup
    if MURI:
        try:
            import pymongo
        except Exception:
            import subprocess
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "pymongo[srv]"])
            import pymongo
        mc = pymongo.MongoClient(MURI, serverSelectionTimeoutMS=10000)
        db = mc.get_database("kts")
        r1 = db.episodes.delete_many({"id": {"$in": EIDS}})
        r2 = db.claims.delete_many({})
        log(f"mongo del={r1.deleted_count} claims={r2.deleted_count}")
        db.postctl.update_one({"_id": "post"}, {"$set": {"next_seq": SEQ, "lock": "", "lock_at": 0}}, upsert=True)
        log(f"postctl -> {SEQ}")
        mc.close()
    # 4) POST POSTER
    mid = await post_poster()
    if mid:
        log(f"POSTER MID={mid}")
    log("DONE")

if __name__ == "__main__":
    asyncio.run(main())
    sys.exit(0)
