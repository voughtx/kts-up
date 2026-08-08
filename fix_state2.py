#!/usr/bin/env python3
# fix_state2.py — claims + postctl lock clear (next_seq preserve) + pick clear
import os, sys, json, time, urllib.request as q

def log(*a): print("[fx2]", *a, flush=True)

MURI = os.environ.get("KEY_7", "")
SBURL = os.environ.get("KEY_20", "").rstrip("/")
SBKEY = os.environ.get("KEY_21", "")

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
    # 1) claims clear (sab runs cancelled hain)
    r = db.claims.delete_many({})
    log(f"claims cleared: {r.deleted_count}")
    # 2) postctl: lock clear, next_seq PRESERVE
    pc = db.postctl.find_one({"_id": "post"}) or {}
    ns = pc.get("next_seq") or 1
    r2 = db.postctl.update_one({"_id": "post"}, {"$set": {"lock": "", "lock_at": 0}})
    log(f"postctl lock cleared | next_seq={ns} (preserved)")
    # 3) done count
    log("episodes total:", db.episodes.count_documents({}))
    mc.close()
    # 4) supabase pick clear
    if SBURL and SBKEY:
        try:
            row = {"id": "pick", "state": {"eid": "", "stage": "", "at": 0}}
            req = q.Request(SBURL + "/rest/v1/progress", data=json.dumps(row).encode(),
                            headers={"apikey": SBKEY, "Authorization": "Bearer " + SBKEY,
                                     "Content-Type": "application/json",
                                     "Prefer": "resolution=merge-duplicates"}, method="POST")
            with q.urlopen(req, timeout=20) as resp:
                log(f"pick cleared: {resp.status}")
        except Exception as ex:
            log("pick clear err:", str(ex)[:80])
    log("DONE")
    return 0

if __name__ == "__main__":
    sys.exit(main())
