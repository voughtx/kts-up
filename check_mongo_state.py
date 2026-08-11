#!/usr/bin/env python3
"""check_mongo_state.py — S1E20-23 ke Mongo records + claims + postctl + done_ids check."""
import os, json, time
from pymongo import MongoClient

uri = os.environ.get("KEY_7", "").strip()
client = MongoClient(uri, serverSelectionTimeoutMS=15000)
db = client["kts"]

targets = [
    "684672cb333e6d02d74c2450",  # S1E20
    "684672cb333e6d02d74c2451",  # S1E21
    "684672cb333e6d02d74c2452",  # S1E22
    "684672cb333e6d02d74c2453",  # S1E23
]
print("=== Mongo episodes records (S1E20-23) ===", flush=True)
for eid in targets:
    rec = db.episodes.find_one({"_id": eid})
    if rec:
        print(f"  {eid[-8:]}: {json.dumps({k: rec.get(k) for k in ['show','season','episode','status','fid','mid','at']}, default=str)[:200]}", flush=True)
    else:
        print(f"  {eid[-8:]}: NO RECORD", flush=True)

print("\n=== claims ===", flush=True)
for eid in targets:
    c = db.claims.find_one({"_id": eid})
    print(f"  {eid[-8:]}: {'claimed at '+str(c.get('at'))+' age '+str(int(time.time()-c.get('at',0)))+'s' if c else 'free'}", flush=True)

print("\n=== postctl ===", flush=True)
pc = db.postctl.find_one({"_id": "post"})
print(" ", json.dumps(pc, default=str)[:300] if pc else "NONE", flush=True)

print("\n=== done_ids count ===", flush=True)
print(" ", db.episodes.count_documents({}), flush=True)

# S1E24-27 (agar exist karein) aur S2E1-5
print("\n=== S2E1-5 in mongo? ===", flush=True)
for eid in ["684672cb333e6d02d74c2454","684672cb333e6d02d74c2455","684672cb333e6d02d74c2456","684672cb333e6d02d74c2457","684672cb333e6d02d74c2458"]:
    rec = db.episodes.find_one({"_id": eid})
    print(f"  {eid[-8:]}: {'DONE' if rec else 'no'}", flush=True)

# kya S1E20-23 ka mid record hai?
print("\n=== mids 3580-3590 check ===", flush=True)
for m in range(3580, 3591):
    rec = db.episodes.find_one({"mid": m})
    if rec:
        print(f"  mid={m}: {rec.get('show','?')[:25]} S{rec.get('season')}E{rec.get('episode')}", flush=True)

client.close()
print("\n[done]", flush=True)
