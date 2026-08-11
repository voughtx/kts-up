#!/usr/bin/env python3
"""fix_deadlock.py — Mushoku S1E20-23 (74f8fea8-ab) + S2E1-5 (9947483c-40) claims clear
+ postctl lock clear. System S2 pick kar raha hai lekin S1E20-23 posted nahi — deadlock."""
import os, json, time
from pymongo import MongoClient

uri = os.environ.get("KEY_7", "").strip()
client = MongoClient(uri, serverSelectionTimeoutMS=15000)
db = client["kts"]

# Mushoku S1E20-23 + S2E1-5 eids (cands positions 2933-2941)
targets = [
    "684672cb333e6d02d74c2450",  # S1E20
    "684672cb333e6d02d74c2451",  # S1E21
    "684672cb333e6d02d74c2452",  # S1E22
    "684672cb333e6d02d74c2453",  # S1E23
    "684672cb333e6d02d74c2454",  # S2E1
    "684672cb333e6d02d74c2455",  # S2E2
    "684672cb333e6d02d74c2456",  # S2E3
    "684672cb333e6d02d74c2457",  # S2E4
    "684672cb333e6d02d74c2458",  # S2E5
]
res = db.claims.delete_many({"_id": {"$in": targets}})
print("claims deleted:", res.deleted_count, flush=True)

# postctl reset — next_seq = S1E20 position (2933)
pc = db.postctl.find_one({"_id": "post"})
if pc:
    print("postctl before: next_seq:", pc.get("next_seq"), "| lock:", str(pc.get("lock",""))[:30], flush=True)
    db.postctl.update_one({"_id": "post"}, {"$set": {"next_seq": 2933, "lock": "", "lock_at": 0}})
    print("postctl reset -> next_seq 2933, lock cleared", flush=True)

left = list(db.claims.find({"_id": {"$in": targets}}))
print("remaining claims:", len(left), flush=True)
client.close()
print("[done]", flush=True)
