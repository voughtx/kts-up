#!/usr/bin/env python3
"""check_state3.py — 3 re-upload shows ka mongo state verify:
1) episodes collection me in shows ke kitne records bache (0 hona chahiye — E1 se shuru hoga)
2) show_posters me in shows hain kya (0 = poster dobara aayega)
3) claims + postctl (deleted = naya init)
Sirf counts — titles nahi."""
import os, json, time
from pymongo import MongoClient

uri = os.environ.get("KEY_7", "").strip()
client = MongoClient(uri, serverSelectionTimeoutMS=15000)
db = client["kts"]

SHOW_IDS = ["68354cfb2d3fded2dcca04e1", "683554362454037aca2590f1", "683d47473fb4a3d6f197c6f8"]

# episodes collection — id field prefix se count
ep_count = db.episodes.count_documents({"id": {"$regex": "^(" + "|".join(SHOW_IDS) + ")"}})
print(f"episodes records for 3 shows: {ep_count}", flush=True)

# show_posters
posters = db.show_posters.count_documents({"_id": {"$in": SHOW_IDS}})
print(f"show_posters for 3 shows: {posters}", flush=True)

# claims (in these show ids)
claims = db.claims.count_documents({"_id": {"$regex": "^(" + "|".join(SHOW_IDS) + ")"}})
print(f"claims for 3 shows: {claims}", flush=True)

# postctl
pc = db.postctl.find_one({"_id": "post"})
print(f"postctl: {'EXISTS next_seq=' + str(pc.get('next_seq')) if pc else 'DELETED (naya init)'}", flush=True)

client.close()
print("[done]", flush=True)
