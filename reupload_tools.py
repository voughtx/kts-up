#!/usr/bin/env python3
# reupload_tools.py — RE-UPLOAD PREP TOOL (kts)
# Modes (env TARGET):
#   verify  -> read-only: channel msgs 838-860 list + bot access test
#   delete  -> delete channel msgs 846-856 + done/claims cleanup + postctl/queue reset
#
# Runs on GitHub Actions runner via:  python reupload_tools.py  (script input)
import os, sys, json, time, urllib.request as q, urllib.parse as u

def log(*a):
    print("[tool]", *a, flush=True)

KID = os.environ.get("KEY_16", "")
KHASH = os.environ.get("KEY_17", "")
SBURL = os.environ.get("KEY_20", "").rstrip("/")
SBKEY = os.environ.get("KEY_21", "")
MURI = os.environ.get("KEY_7", "")
CHAT = os.environ.get("KEY_2", "")
TARGET = (os.environ.get("TARGET") or "verify").strip().lower()

# S5 re-upload range: E34-E48 (E34 died-doc, E35+E39-E48 posted, E36-38 claims)
EIDS = [
    "687a500af27e6f8b5f5c1bfd",  # E34 (died doc)
    "687a500af27e6f8b5f5c1bfe",  # E35
    "687a500af27e6f8b5f5c1bff",  # E36
    "687a500af27e6f8b5f5c1c00",  # E37
    "687a500af27e6f8b5f5c1c01",  # E38
    "687a500af27e6f8b5f5c1c02",  # E39
    "687a500af27e6f8b5f5c1c03",  # E40
    "687a500af27e6f8b5f5c1c04",  # E41
    "687a500af27e6f8b5f5c1c05",  # E42
    "687a500af27e6f8b5f5c1c06",  # E43
    "687a500af27e6f8b5f5c1c07",  # E44
    "687a500af27e6f8b5f5c1c08",  # E45
    "687a500af27e6f8b5f5c1c09",  # E46
    "687a500af27e6f8b5f5c1c0a",  # E47
    "687a500af27e6f8b5f5c1c0b",  # E48
]
DEL_FROM, DEL_TO = 846, 856      # channel message ids to delete (E35, E39-E48)
SEQ_RESET = 318                  # postctl next_seq = E34's position in ordered list

def sb_get(path):
    req = q.Request(SBURL + path, headers={"apikey": SBKEY, "Authorization": "Bearer " + SBKEY})
    with q.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())

def sb_post(path, payload, method="POST"):
    req = q.Request(SBURL + path, data=json.dumps(payload).encode(),
                    headers={"apikey": SBKEY, "Authorization": "Bearer " + SBKEY,
                             "Content-Type": "application/json", "Prefer": "resolution=merge-duplicates"},
                    method=method)
    with q.urlopen(req, timeout=30) as r:
        return r.status

def sb_delete(path):
    req = q.Request(SBURL + path, headers={"apikey": SBKEY, "Authorization": "Bearer " + SBKEY}, method="DELETE")
    with q.urlopen(req, timeout=30) as r:
        return r.status

def load_sessions():
    st = (sb_get("/rest/v1/progress?select=state&id=eq.bot_sessions&limit=1") or [{}])[0].get("state") or {}
    return {k: v for k, v in st.items() if isinstance(v, list) and len(v) >= 1}

def connect(api_id, api_hash, sess):
    from telethon import TelegramClient
    from telethon.sessions import StringSession
    cli = TelegramClient(StringSession(sess), int(api_id), api_hash, connection_retries=2, request_retries=2)
    cli.connect()
    return cli

def get_msgs(cli, ids):
    """Fetch messages; returns {id: msg} for existing."""
    out = {}
    try:
        ch = int(CHAT) if str(CHAT).lstrip("-").isdigit() else CHAT
        msgs = cli.get_messages(ch, ids=list(ids))
        for m in msgs:
            if m is not None:
                out[m.id] = m
    except Exception as ex:
        log("get_msgs err:", str(ex)[:120])
    return out

def mode_verify():
    log("== VERIFY MODE (read-only) ==")
    if not (KID and KHASH):
        log("FATAL: KEY_16/KEY_17 missing"); return 1
    bots = load_sessions()
    log("bots available:", list(bots.keys()))
    if not bots:
        log("FATAL: no bot sessions"); return 1
    bname = "bot1"
    try:
        cli = connect(KID, KHASH, bots[bname][0])
        me = cli.get_me()
        log("connected:", bname, "->", me.username or me.id)
        ids = list(range(838, 861))
        found = get_msgs(cli, ids)
        log(f"messages found: {len(found)}/{len(ids)}")
        for mid in sorted(found.keys()):
            m = found[mid]
            cap = ""
            try:
                cap = (m.message or "")[:60].replace("\n", " ")
            except Exception:
                pass
            log(f"  msg {mid} | date={m.date} | {cap}")
        cli.disconnect()
    except Exception as ex:
        log("verify FAIL:", str(ex)[:200])
        return 1
    log("verify DONE")
    return 0

def mode_delete():
    log("== DELETE MODE ==")
    if not (KID and KHASH):
        log("FATAL: KEY_16/KEY_17 missing"); return 1
    # ---- 1) DELETE CHANNEL MESSAGES ----
    bots = load_sessions()
    ids = list(range(DEL_FROM, DEL_TO + 1))
    log(f"deleting msgs {DEL_FROM}-{DEL_TO} ({len(ids)} msgs)")
    deleted = set()
    for bname in sorted(bots.keys()):
        if len(deleted) == len(ids):
            break
        try:
            cli = connect(KID, KHASH, bots[bname][0])
            try:
                ch = int(CHAT) if str(CHAT).lstrip("-").isdigit() else CHAT
                remaining = [i for i in ids if i not in deleted]
                if remaining:
                    r = cli.delete_messages(ch, remaining)
                    log(f"{bname}: delete_messages({len(remaining)}) -> {r}")
                # verify which are gone
                found = get_msgs(cli, [i for i in ids if i not in deleted])
                for i in ids:
                    if i not in found:
                        deleted.add(i)
                log(f"{bname}: total deleted so far {len(deleted)}/{len(ids)}")
            finally:
                cli.disconnect()
        except Exception as ex:
            log(f"{bname}: FAIL {str(ex)[:150]}")
    log(f"FINAL deleted: {len(deleted)}/{len(ids)} -> {sorted(deleted)}")
    if len(deleted) < len(ids):
        log("WARNING: kuch messages delete nahi hue — manually check karo!")
    # ---- 2) STATE CLEANUP ----
    log("== state cleanup ==")
    # supabase episodes rows remove
    for eid in EIDS:
        try:
            st = sb_delete(f"/rest/v1/episodes?id=eq.{eid}")
            log(f"sb episodes delete {eid[-6:]} -> {st}")
        except Exception as ex:
            log(f"sb delete err {eid[-6:]}: {str(ex)[:100]}")
    # supabase pick clear
    try:
        sb_post("/rest/v1/progress", {"id": "pick", "state": {"eid": "", "stage": "", "at": 0}})
        log("pick cleared")
    except Exception as ex:
        log("pick clear err:", str(ex)[:100])
    # supabase queue clear
    try:
        sb_post("/rest/v1/progress", {"id": "queue", "state": {"entries": []}})
        log("queue cleared")
    except Exception as ex:
        log("queue clear err:", str(ex)[:100])
    # ---- 3) MONGO cleanup + postctl reset ----
    if MURI:
        try:
            import pymongo
        except Exception:
            import subprocess, sys as _s
            _s.check_call([sys.executable, "-m", "pip", "install", "-q", "pymongo[srv]"])
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
            pc2 = db.postctl.find_one({"_id": "post"}) or {}
            log(f"MONGO after: postctl={pc2}")
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
        rc = mode_delete()
    else:
        rc = mode_verify()
    sys.exit(rc)
