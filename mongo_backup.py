#!/usr/bin/env python3
"""mongo_backup.py — FULL mongo export for backup (episodes, show_posters, claims,
postctl, progress). Output: gzip+base64 chunks in log (KTSB64 markers) —
sandbox reconstruct karke backup zip banayega."""
import os, json, base64, gzip
from pymongo import MongoClient

uri = os.environ.get("KEY_7", "").strip()
cli = MongoClient(uri, serverSelectionTimeoutMS=25000)
db = cli["kts"]
out = {}
for coll in ["episodes", "show_posters", "claims", "postctl", "progress"]:
    try:
        rows = list(db[coll].find({}))
        out[coll] = json.loads(json.dumps(rows, default=str))
        print(f"[backup] {coll}: {len(rows)} rows", flush=True)
    except Exception as e:
        print(f"[backup] {coll} ERR {str(e)[:80]}", flush=True)
cli.close()

raw = json.dumps(out).encode()
gz = gzip.compress(raw, 9)
b64 = base64.b64encode(gz).decode()
print(f"[backup] raw={len(raw)} gz={len(gz)} b64={len(b64)}", flush=True)
print("KTSB64:START", flush=True)
n = 50000
for i in range(0, len(b64), n):
    print(f"KTSB64:{i//n}:{b64[i:i+n]}", flush=True)
print("KTSB64:END", flush=True)
print("[done]", flush=True)
