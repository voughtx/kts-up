#!/usr/bin/env python3
# reupload_tools.py — RE-UPLOAD PREP TOOL (kts)  [asyncio/telethon v2]
# Modes (env TARGET):
#   verify  -> read-only: channel msgs 838-860 list + bot access test
#   delete  -> delete channel msgs 846-856 + done/claims cleanup + postctl/queue reset
import os, sys, json, asyncio, urllib.request as q

def log(*a):
    print("[tool]", *a, flush=True)

KID = os.environ.get("KEY_16", "")
KHASH = os.environ.get("KEY_17", "")
SBURL = os.environ.get("KEY_20", "").rstrip("/")
SBKEY = os.environ.get("KEY_21", "")
MURI = os.environ.get("KEY_7", "")
CHAT = os.environ.get("KEY_2", "")
TARGET = (os.environ.get("TARGET") or "verify").strip().lower()

EIDS = [
    "687a500af27e6f8b5f5c1bfd", "687a500af27e6f8b5f5c1bfe",
    "687a500af27e6f8b5f5c1bff", "687a500af27e6f8b5f5c1c00",
    "687a500af27e6f8b5f5c1c01", "687a500af27e6f8b5f5c1c02",
    "687a500af27e6f8b5f5c1c03", "687a500af27e6f8b5f5c1c04",
    "687a500af27e6f8b5f5c1c05", "687a500af27e6f8b5f5c1c06",
    "687a500af27e6f8b5f5c1c07", "687a500af27e6f8b5f5c1c08",
    "687a500af27e6f8b5f5c1c09", "687a500af27e6f8b5f5c1c0a",
    "687a500af27e6f8b5f5c1c0b",
]
DEL_FROM, DEL_TO = 846, 856
SEQ_RESET = 318

def sb_get(path):
    req = q.Request(SBURL + path, headers={"apikey": SBKEY, "Authorization": "Bearer " + SBKEY})
    with q.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())

def sb_post(path, payload):
    req = q.Request(SBURL + path, data=json.dumps(payload).encode(),
                    headers={"apikey": SBKEY, "Authorization": "Bearer " + SBKEY,
                             "Content-Type": "application/json", "Prefer": "resolution=merge-duplicates"},
                    method="POST")
    with q.urlopen(req, timeout=30) as r:
        return r.status

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

async def mode_verify():
    log("== VERIFY MODE (read-only) ==")
    if not (KID and KHASH):
        log("FATAL: KEY_16/KEY_17 missing"); return 1
    bots = load_sessions()
    log("bots available:", list(bots.keys()))
    if not bots:
        log("FATAL: no bot sessions"); return 1
    bname = "bot1"
    try:
        cli = await connect(bots[bname][0])
        me = await cli.get_me()
        log("connected:", bname, "->", getattr(me, "username", None) or getattr(me, "id", None))
        ids = list(range(838, 861))
        found = await get_msgs(cli, ids)
        log(f"messages found: {len(found)}/{len(ids)}")
        for mid in sorted(found.keys()):
            m = found[mid]
            cap = ""
            try:
                cap = (m.message or "")[:60].replace("\n", " ")
            except Exception:
                pass
            log(f"  msg {mid} | date={m.date} | {cap}")
        await cli.disconnect()
    except Exception as ex:
        log("verify FAIL:", str(ex)[:200])
        return 1
    log("verify DONE")
    return 0

async def mode_delete():
    log("== DELETE MODE ==")
    if not (KID and KHASH):
        log("FATAL: KEY_16/KEY_17 missing"); return 1
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
                    log(f"{bname}: delete_messages({len(remaining)}) -> {r}")
                found = await get_msgs(cli, [i for i in ids if i not in deleted])
                for i in ids:
                    if i not in found:
                        deleted.add(i)
                log(f"{bname}: total deleted so far {len(deleted)}/{len(ids)}")
            finally:
                await cli.disconnect()
        except Exception as ex:
            log(f"{bname}: FAIL {str(ex)[:150]}")
    log(f"FINAL deleted: {len(deleted)}/{len(ids)} -> {sorted(deleted)}")
    if len(deleted) < len(ids):
        log("WARNING: kuch messages delete nahi hue — manually check karo!")
    log("== state cleanup ==")
    for eid in EIDS:
        try:
            st = sb_delete(f"/rest/v1/episodes?id=eq.{eid}")
            log(f"sb episodes delete {eid[-6:]} -> {st}")
        except Exception as ex:
            log(f"sb delete err {eid[-6:]}: {str(ex)[:100]}")
    try:
        sb_post("/rest/v1/progress", {"id": "pick", "state": {"eid": "", "stage": "", "at": 0}})
        log("pick cleared")
    except Exception as ex:
        log("pick clear err:", str(ex)[:100])
    try:
        sb_post("/rest/v1/progress", {"id": "queue", "state": {"entries": []}})
        log("queue cleared")
    except Exception as ex:
        log("queue clear err:", str(ex)[:100])
    if MURI:
        try:
            import pymongo
        except Exception:
            import subprocess
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "pymongo[srv]"])
            import pymongo
        try:
            mc = pymongo.MongoClient(MURI, serverSelectionTimeoutMS=10000)
            db = mc.get_database("kts")
            before_ep = db.episodes.count_documents({"id": {"$in": EIDS}})
            before_cl = db.claims.count_documents({"_id": {"$in": EIDS}})
            pc = db.postctl.find_one({"_id": "post"}) or {}
            log(f"MONGO before: episodes={before_ep} claims={before_cl} postctl={pc}")
            r1 = db.episodes.delete_many({"id": {"$in": EIDS}})
            r2 = db.claims.delete_many({"_id": {"$in": EIDS}})
            log(f"deleted episodes={r1.deleted_count} claims={r2.deleted_count}")
            r3 = db.postctl.update_one({"_id": "post"}, {"$set": {"next_seq": SEQ_RESET, "lock": "", "lock_at": 0}}, upsert=True)
            log(f"postctl reset -> next_seq={SEQ_RESET} (upserted={r3.upserted_id is not None})")
            log(f"MONGO after: postctl={db.postctl.find_one({'_id': 'post'}) or {}}")
            mc.close()
        except Exception as ex:
            log("MONGO err:", str(ex)[:200])
    else:
        log("WARNING: KEY_7 missing — mongo cleanup skip")
    log("DELETE MODE DONE")
    return 0

if __name__ == "__main__":
    log("TARGET =", TARGET)
    if TARGET == "delete":
        rc = asyncio.run(mode_delete())
    else:
        rc = asyncio.run(mode_verify())
    sys.exit(rc)
