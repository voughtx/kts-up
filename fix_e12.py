#!/usr/bin/env python3
# fix_e12.py — deny BLUE LOCK S2E12 (broken CDN data) + clear claims + postctl to E13
import os, sys, json, time, urllib.request as q

def log(*a): print("[fx12]", *a, flush=True)

MURI = os.environ.get("KEY_7", "")
SBURL = os.environ.get("KEY_20", "").rstrip("/")
SBKEY = os.environ.get("KEY_21", "")

E12 = "681d0ca15edd6fa782ea65c9"  # BLUE LOCK S2E12 Flowers (broken segments on CDN)
SEQ = 1423  # S2E13 position in ordered list

def main():
    # 1) deny list add
    try:
        req = q.Request(SBURL+"/rest/v1/progress?select=state&id=eq.deny&limit=1",
                        headers={"apikey": SBKEY, "Authorization": "Bearer " + SBKEY})
        with q.urlopen(req, timeout=20) as r:
            arr = json.loads(r.read().decode())
        st = (arr[0].get("state") or {}) if arr else {}
        eids = set(st.get("eids") or [])
        if E12 not in eids:
            eids.add(E12)
            row = {"id": "deny", "state": {"eids": sorted(eids), "at": int(time.time())}}
            req2 = q.Request(SBURL+"/rest/v1/progress", data=json.dumps(row).encode(),
                headers={"apikey": SBKEY, "Authorization": "Bearer " + SBKEY,
                         "Content-Type": "application/json",
                         "Prefer": "resolution=merge-duplicates"}, method="POST")
            with q.urlopen(req2, timeout=20) as r2:
                log(f"deny add E12: {r2.status}")
        else:
            log("E12 already in deny")
    except Exception as ex:
        log("deny err:", str(ex)[:80])
    # 2) mongo: claims clear + postctl
    if MURI:
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
        db.postctl.update_one({"_id": "post"}, {"$set": {"next_seq": SEQ, "lock": "", "lock_at": 0}}, upsert=True)
        pc = db.postctl.find_one({"_id": "post"}) or {}
        log(f"postctl -> next_seq={pc.get('next_seq')}")
        # also delete any done-doc for E12 if exists
        r3 = db.episodes.delete_many({"id": E12})
        if r3.deleted_count:
            log(f"removed E12 done-doc: {r3.deleted_count}")
        mc.close()
    log("DONE")

main()
sys.exit(0)
