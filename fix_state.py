#!/usr/bin/env python3
# fix_state.py — postctl reset + claims cleanup (kts)
import os, sys, json, urllib.request as q

def log(*a): print("[fix]", *a, flush=True)

MURI = os.environ.get("KEY_7", "")
SBURL = os.environ.get("KEY_20", "").rstrip("/")
SBKEY = os.environ.get("KEY_21", "")

SEQ_RESET = 927  # S18E34 (gap episode) — first undone in ordered list

def main():
    if not MURI:
        log("KEY_7 missing"); return 1
    try:
        import pymongo
    except Exception:
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "pymongo[srv]"])
        import pymongo
    mc = pymongo.MongoClient(MURI, serverSelectionTimeoutMS=10000)
    db = mc.get_database("kts")
    # 1) postctl reset
    r = db.postctl.update_one({"_id": "post"}, {"$set": {"next_seq": SEQ_RESET, "lock": "", "lock_at": 0}}, upsert=True)
    pc = db.postctl.find_one({"_id": "post"}) or {}
    log(f"postctl -> next_seq={pc.get('next_seq')} (lock={pc.get('lock')!r})")
    # 2) claims clear (sab runs cancelled hain — koi active nahi)
    r2 = db.claims.delete_many({})
    log(f"claims cleared: {r2.deleted_count}")
    # 3) episodes docs check — koi [died] type doc?
    died = list(db.episodes.find({"mid": 0}, {"id": 1}))
    log(f"episode docs with mid=0: {len(died)}")
    for d in died:
        log("  died-doc:", d.get("id"))
    # 4) done count
    total = db.episodes.count_documents({})
    log(f"episodes total: {total}")
    mc.close()
    # 5) supabase deny doc init (empty)
    if SBURL and SBKEY:
        try:
            row = {"id": "deny", "state": {"eids": [], "at": int(__import__("time").time())}}
            req = q.Request(SBURL + "/rest/v1/progress", data=json.dumps(row).encode(),
                            headers={"apikey": SBKEY, "Authorization": "Bearer " + SBKEY,
                                     "Content-Type": "application/json",
                                     "Prefer": "resolution=merge-duplicates"}, method="POST")
            with q.urlopen(req, timeout=20) as resp:
                log(f"deny doc init: {resp.status}")
        except Exception as ex:
            log("deny init err:", str(ex)[:100])
    log("DONE")
    return 0

if __name__ == "__main__":
    sys.exit(main())
