#!/usr/bin/env python3
"""clear_stuck2.py — S1E20-22 (74f8fea8/9/aa) + postctl lock clear + next_seq verify."""
import os, json, time
from pymongo import MongoClient

uri = os.environ.get("KEY_7", "").strip()
client = MongoClient(uri, serverSelectionTimeoutMS=15000)
db = client["kts"]

targets = [
    "684672cb333e6d02d74c2450",  # S1E20
    "684672cb333e6d02d74c2451",  # S1E21
    "684672cb333e6d02d74c2452",  # S1E22
]
res = db.claims.delete_many({"_id": {"$in": targets}})
print("claims deleted:", res.deleted_count, flush=True)

pc = db.postctl.find_one({"_id": "post"})
if pc:
    print("postctl next_seq:", pc.get("next_seq"), "| lock:", str(pc.get("lock",""))[:30], flush=True)
    db.postctl.update_one({"_id": "post"}, {"$set": {"lock": "", "lock_at": 0}})
    print("lock cleared", flush=True)

left = list(db.claims.find({"_id": {"$in": targets}}))
print("remaining:", len(left), flush=True)
client.close()
print("[done]", flush=True)
