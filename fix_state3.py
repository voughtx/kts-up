#!/usr/bin/env python3
# fix_state3.py — reset postctl to Oggy start (1256) + clear claims/pick
import os, sys, json, time, urllib.request as q

def log(*a): print("[fx3]", *a, flush=True)

MURI = os.environ.get("KEY_7", "")
SBURL = os.environ.get("KEY_20", "").rstrip("/")
SBKEY = os.environ.get("KEY_21", "")

SEQ = 1256  # first Oggy episode position in ordered list

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
    r = db.claims.delete_many({})
    log(f"claims cleared: {r.deleted_count}")
    r2 = db.postctl.update_one({"_id": "post"}, {"$set": {"next_seq": SEQ, "lock": "", "lock_at": 0}}, upsert=True)
    pc = db.postctl.find_one({"_id": "post"}) or {}
    log(f"postctl -> next_seq={pc.get('next_seq')}")
    log("episodes total:", db.episodes.count_documents({}))
    # show_posters collection check (beyblade locked?)
    try:
        sp = list(db.show_posters.find({}, {"_id": 1}))
        log("show_posters:", sp)
    except Exception as ex:
        log("show_posters err:", str(ex)[:60])
    mc.close()
    # supabase pick clear
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
            log("pick err:", str(ex)[:80])
    log("DONE")
    return 0

if __name__ == "__main__":
    sys.exit(main())
