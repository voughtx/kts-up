#!/usr/bin/env python3
# fix_order.py — generic channel re-order tool (kts)
# Env: DEL_MIDS="1466-1473"  EIDS="a,b,c"  SEQ=927
import os, sys, json, asyncio, urllib.request as q

def log(*a): print("[fixord]", *a, flush=True)

KID = os.environ.get("KEY_16", "")
KHASH = os.environ.get("KEY_17", "")
SBURL = os.environ.get("KEY_20", "").rstrip("/")
SBKEY = os.environ.get("KEY_21", "")
MURI = os.environ.get("KEY_7", "")
CHAT = os.environ.get("KEY_2", "")

DEL_MIDS = os.environ.get("DEL_MIDS", "1466-1473")
EIDS = [x.strip() for x in os.environ.get("EIDS", "").split(",") if x.strip()]
SEQ = int(os.environ.get("SEQ", "927"))

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

async def main():
    log("DEL_MIDS:", DEL_MIDS, "| EIDS:", len(EIDS), "| SEQ:", SEQ)
    lo, hi = (int(x) for x in DEL_MIDS.split("-"))
    ids = list(range(lo, hi + 1))
    # 1) delete messages
    bots = load_sessions()
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
                log(f"{bname}: deleted {len(deleted)}/{len(ids)}")
            finally:
                await cli.disconnect()
        except Exception as ex:
            log(f"{bname}: FAIL {str(ex)[:150]}")
    log(f"FINAL deleted: {len(deleted)}/{len(ids)} -> {sorted(deleted)}")
    # 2) supabase rows delete
    for eid in EIDS:
        try:
            st = sb_delete(f"/rest/v1/episodes?id=eq.{eid}")
            log(f"sb del {eid[-6:]} -> {st}")
        except Exception as ex:
            log(f"sb del err {eid[-6:]}: {str(ex)[:80]}")
    # 3) mongo cleanup + postctl
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
        log(f"mongo episodes del={r1.deleted_count} claims cleared={r2.deleted_count}")
        r3 = db.postctl.update_one({"_id": "post"}, {"$set": {"next_seq": SEQ, "lock": "", "lock_at": 0}}, upsert=True)
        pc = db.postctl.find_one({"_id": "post"}) or {}
        log(f"postctl -> next_seq={pc.get('next_seq')}")
        mc.close()
    log("DONE")

if __name__ == "__main__":
    asyncio.run(main())
    sys.exit(0)
