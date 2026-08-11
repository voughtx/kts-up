#!/usr/bin/env python3
import os
from pymongo import MongoClient
uri = os.environ.get("KEY_7", "").strip()
client = MongoClient(uri, serverSelectionTimeoutMS=15000)
db = client["kts"]
targets = ["684672cb333e6d02d74c2450","684672cb333e6d02d74c2451","684672cb333e6d02d74c2452","684672cb333e6d02d74c2453","684672cb333e6d02d74c2454"]
res = db.claims.delete_many({"_id": {"$in": targets}})
print("claims deleted:", res.deleted_count, flush=True)
db.postctl.update_one({"_id": "post"}, {"$set": {"lock": "", "lock_at": 0}})
print("postctl lock cleared", flush=True)
client.close()
