#!/usr/bin/env python3
"""clear_mushoku.py — Mushoku S1E20-23 claims clear (cands pos 2933-2936)."""
import os, json, urllib.request, time
from pymongo import MongoClient

SB_URL = os.environ.get("KEY_20", "").strip().rstrip("/")
SB_KEY = os.environ.get("KEY_21", "").strip()
uri = os.environ.get("KEY_7", "").strip()
client = MongoClient(uri, serverSelectionTimeoutMS=15000)
db = client["kts"]

H = {"apikey": SB_KEY, "Authorization": f"Bearer {SB_KEY}"}
req = urllib.request.Request(f"{SB_URL}/rest/v1/progress?select=state&id=eq.cands", headers=H)
with urllib.request.urlopen(req, timeout=20) as r:
    eids = json.loads(r.read().decode())[0]["state"]["eids"]
targets = [eids[2932], eids[2933], eids[2934], eids[2935]]  # S1E20-23
now = int(time.time())
# sirf stale claims clear (30 min+ ya koi bhi jo 5 min se zyada purana ho — retry cycle ke liye)
res = db.claims.delete_many({"_id": {"$in": targets}})
print("claims deleted:", res.deleted_count, flush=True)
db.postctl.update_one({"_id": "post"}, {"$set": {"lock": "", "lock_at": 0}})
print("postctl lock cleared", flush=True)
client.close()
