#!/usr/bin/env python3
"""snap_check.py — live system snapshot (POSITION ONLY, no titles/captions).
Prints: postctl, claims (ids+ages), show_posters for the 3 re-upload shows,
episode counts, health/pick rows. NEVER prints show/episode titles."""
import os, json, time
from pymongo import MongoClient

uri = os.environ.get("KEY_7", "").strip()
client = MongoClient(uri, serverSelectionTimeoutMS=20000)
db = client["kts"]

pc = db.postctl.find_one({"_id": "post"})
if pc:
    print("postctl: next_seq=%s lock=%s lock_at=%s (age %ss)" % (
        pc.get("next_seq"), str(pc.get("lock") or "")[:10], pc.get("lock_at"),
        int(time.time() - (pc.get("lock_at") or 0))))
else:
    print("postctl: NONE")

claims = list(db.claims.find())
print("claims count:", len(claims))
for c in sorted(claims, key=lambda x: -x.get("at", 0))[:8]:
    print("  claim", str(c["_id"])[-8:], "age", int(time.time() - c.get("at", 0)), "s")

REUPLOAD_SHOWS = [
    "68354cfb2d3fded2dcca04e1",
    "683554362454037aca2590f1",
    "683d47473fb4a3d6f197c6f8",
]
print("\nshow_posters rows (re-upload shows):")
for sid in REUPLOAD_SHOWS:
    row = db.show_posters.find_one({"_id": sid})
    print("  show", sid[-8:], "->", ("EXISTS at=%s" % row.get("at")) if row else "absent")

print("\nepisodes total:", db.episodes.count_documents({}))
print("episodes done:", db.episodes.count_documents({"status": "done"}))

# progress rows of interest (position only)
for pid in ["health", "pick"]:
    row = db.progress.find_one({"_id": pid})
    print("progress", pid, "->", json.dumps(row, default=str)[:200] if row else "NONE")

client.close()
