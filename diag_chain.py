#!/usr/bin/env python3
"""diag_chain.py — chain deadlock diagnostic:
cands se seq 80-100 ke eids nikal ke check: mongo episodes(done)? claims? deny?
Sirf position/eid data — titles nahi."""
import os, json, time, urllib.request

def sbget(url):
    req = urllib.request.Request(url, headers={
        "apikey": os.environ.get("KEY_21", ""),
        "Authorization": f"Bearer {os.environ.get('KEY_21', '')}"})
    with urllib.request.urlopen(req, timeout=25) as r:
        return json.loads(r.read().decode())

def main():
    from pymongo import MongoClient
    uri = os.environ.get("KEY_7", "").strip()
    cli = MongoClient(uri, serverSelectionTimeoutMS=15000)
    db = cli.get_database("kts")

    SBU = os.environ.get("KEY_20", "").rstrip("/")
    cands = []
    try:
        c = sbget(f"{SBU}/rest/v1/progress?select=state&id=eq.cands&limit=1")
        if c:
            cands = (c[0].get("state") or {}).get("eids") or []
    except Exception as e:
        print("cands fail:", str(e)[:80], flush=True)
    print("cands len:", len(cands), flush=True)

    done = set()
    try:
        for d in db.episodes.find({}, {"id": 1}):
            if d.get("id"):
                done.add(d["id"])
    except Exception as e:
        print("mongo episodes fail:", str(e)[:80], flush=True)

    claims = set()
    try:
        for d in db.claims.find({}, {"_id": 1}):
            claims.add(d["_id"])
    except Exception as e:
        print("claims fail:", str(e)[:80], flush=True)

    deny = set()
    try:
        d = sbget(f"{SBU}/rest/v1/progress?select=state&id=eq.deny&limit=1")
        if d:
            deny = set((d[0].get("state") or {}).get("eids") or [])
    except Exception:
        pass

    # postctl
    pc = db.postctl.find_one({"_id": "post"})
    print("postctl next_seq:", (pc or {}).get("next_seq"), "| lock:", str((pc or {}).get("lock"))[:20], flush=True)

    print("\nseq | done | claim | deny | eid", flush=True)
    for i in range(80, min(101, len(cands)+1)):
        eid = cands[i-1]
        print(f"{i:3} | {'Y' if eid in done else '.'} | {'Y' if eid in claims else '.'} | {'Y' if eid in deny else '.'} | {eid[:16]}", flush=True)

    cli.close()
    print("[done]", flush=True)

main()
