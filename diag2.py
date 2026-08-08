#!/usr/bin/env python3
import os, sys, json, time
MURI = os.environ.get("KEY_7", "")
def log(*a): print("[d2]", *a, flush=True)
def main():
    import pymongo
    mc = pymongo.MongoClient(MURI, serverSelectionTimeoutMS=10000)
    db = mc.get_database("kts")
    pc = db.postctl.find_one({"_id":"post"}) or {}
    log("postctl:", json.dumps(pc))
    now = int(time.time())
    for c in db.claims.find({}).sort("at",1):
        age = now - (c.get("at") or 0)
        log(f"  claim {c['_id'][-8:]} age={age}s")
    log("claims total:", db.claims.count_documents({}))
    mc.close()
main()
sys.exit(0)
