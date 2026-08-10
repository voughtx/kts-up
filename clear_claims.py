#!/usr/bin/env python3
"""clear_claims.py — Miraculous S5E16-24 ke atke hue claims Mongo se clear.
Sirf specific eids (ba655f35..ba655f3d) — koi aur data touch nahi."""
import os
from pymongo import MongoClient

uri = os.environ.get("KEY_7", "").strip()
if not uri:
    print("[!] KEY_7 missing")
    raise SystemExit(1)

client = MongoClient(uri, serverSelectionTimeoutMS=15000)
db = client["kts"]

# S5E16-24: 6849900e6ed2282cba655f35 .. 3d
eids = [f"6849900e6ed2282cba655f{i:02x}" for i in range(0x35, 0x3e)]
print("target eids:", len(eids))

res = db.claims.delete_many({"_id": {"$in": eids}})
print("claims deleted:", res.deleted_count)

# verify remaining
left = list(db.claims.find({"_id": {"$in": eids}}, {"_id": 1}))
print("remaining:", len(left))

# postctl check (read-only)
pc = db.postctl.find_one({"_id": "post"})
if pc:
    print("postctl next_seq:", pc.get("next_seq"), "| lock:", pc.get("lock", "")[:20])
else:
    print("postctl: none")

client.close()
print("[done]")
