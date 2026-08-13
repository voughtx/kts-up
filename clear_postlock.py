#!/usr/bin/env python3
"""clear_postlock.py — postctl ka atka lock clear (canceled runs se).
Agar lock atka hai (run done/cancelled) to release karo."""
import os
from pymongo import MongoClient

uri = os.environ.get("KEY_7", "").strip()
if not uri:
    print("[!] KEY_7 missing")
    raise SystemExit(1)

client = MongoClient(uri, serverSelectionTimeoutMS=15000)
db = client["kts"]

pc = db.postctl.find_one({"_id": "post"})
if not pc:
    print("postctl none — ok")
    client.close()
    raise SystemExit(0)

lock = pc.get("lock", "")
lock_at = pc.get("lock_at", 0)
next_seq = pc.get("next_seq")
print("before: next_seq:", next_seq, "| lock:", lock[:30], "| lock_at:", lock_at)

# lock hamesha clear karo — koi bhi live run abhi nahi hai (sab cancel)
if lock:
    res = db.postctl.update_one({"_id": "post"}, {"$set": {"lock": "", "lock_at": 0}})
    print("lock cleared:", res.modified_count)
else:
    print("no lock")

pc2 = db.postctl.find_one({"_id": "post"})
print("after: next_seq:", pc2.get("next_seq"), "| lock:", repr(pc2.get("lock")))
client.close()
print("[done]")
