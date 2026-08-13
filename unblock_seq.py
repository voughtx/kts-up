#!/usr/bin/env python3
"""unblock_seq.py — denied episode ka claim clear + postctl next_seq advance.
Chain denied eid pe atki ho to use skip karke aage badhao."""
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

    deny = set()
    try:
        d = sbget(f"{SBU}/rest/v1/progress?select=state&id=eq.deny&limit=1")
        if d:
            deny = set((d[0].get("state") or {}).get("eids") or [])
    except Exception:
        pass

    # 1) denied eids ka claim clear
    denied_claims = [e for e in deny if e in cands]
    if denied_claims:
        r = db.claims.delete_many({"_id": {"$in": denied_claims}})
        print(f"denied claims deleted: {r.deleted_count}", flush=True)

    # 2) postctl next_seq = pehla non-done non-denied seq
    done = set()
    try:
        for d2 in db.episodes.find({}, {"id": 1}):
            if d2.get("id"):
                done.add(d2["id"])
    except Exception as e:
        print("done fail:", str(e)[:60], flush=True)

    target = None
    for i, eid in enumerate(cands, 1):
        if eid in done:
            continue
        if eid in deny:
            continue
        target = i
        break
    if target:
        r2 = db.postctl.update_one({"_id": "post"}, {"$set": {"next_seq": target, "lock": "", "lock_at": 0}})
        print(f"postctl next_seq -> {target} (lock released), updated: {r2.modified_count}", flush=True)
    else:
        print("sab done/denied", flush=True)
    cli.close()
    print("[done]", flush=True)

main()
