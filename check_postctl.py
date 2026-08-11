#!/usr/bin/env python3
"""check_postctl.py — postctl + claims state check (Mongo)."""
import os, json
from pymongo import MongoClient

uri = os.environ.get("KEY_7", "").strip()
client = MongoClient(uri, serverSelectionTimeoutMS=15000)
db = client["kts"]

pc = db.postctl.find_one({"_id": "post"})
print("postctl:", json.dumps(pc, default=str)[:400] if pc else "NONE")

# recent claims
claims = list(db.claims.find().sort("at", -1).limit(10))
print("\nrecent claims:", len(claims))
for c in claims:
    print(f"  {c['_id'][-8:]} at={c.get('at')} age={int(__import__('time').time()-c.get('at',0))}s")

# episodes done count
print("\ndone eps:", db.episodes.count_documents({"status": "done"}))
client.close()
