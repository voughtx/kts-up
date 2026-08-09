#!/usr/bin/env python3
import os, sys, json
MURI = os.environ.get("KEY_7", "")
def log(*a): print("[d3]", *a, flush=True)
def main():
    import pymongo
    mc = pymongo.MongoClient(MURI, serverSelectionTimeoutMS=10000)
    db = mc.get_database("kts")
    try:
        sp = list(db.show_posters.find({}, {"_id": 1}))
        log("show_posters:", sp)
    except Exception as ex:
        log("sp err:", str(ex)[:60])
    pc = db.postctl.find_one({"_id":"post"}) or {}
    log("postctl:", json.dumps(pc))
    log("claims:", db.claims.count_documents({}))
    mc.close()
main()
sys.exit(0)
