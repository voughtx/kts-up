#!/usr/bin/env python3
"""sim_claim.py — _claim_next ka exact behavior simulate karo seq 86 ke liye.
Batao: mongo done me hai? deny me? claim insert try -> success/fail?"""
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

    # done ids — EXACT same as _Store.done_ids
    done = set()
    try:
        for d in db.episodes.find({}, {"id": 1}):
            if d.get("id"):
                done.add(d["id"])
    except Exception as e:
        print("done_ids fail:", str(e)[:80], flush=True)
    print("done_ids count:", len(done), flush=True)

    # deny ids
    deny = set()
    try:
        d = sbget(f"{SBU}/rest/v1/progress?select=state&id=eq.deny&limit=1")
        if d:
            deny = set((d[0].get("state") or {}).get("eids") or [])
    except Exception:
        pass

    # iterate EXACTLY like _claim_next
    now = int(time.time())
    print("\n--- simulate _claim_next (first 120 cands) ---", flush=True)
    claimed = 0
    for i, cid in enumerate(cands[:120], 1):
        if cid in done:
            continue
        if cid in deny:
            continue
        # check if claim exists
        exists = db.claims.find_one({"_id": cid}) is not None
        if exists:
            continue
        if claimed < 15:
            print(f"  first-unclaimed: seq={i} eid={cid[:24]}", flush=True)
        claimed += 1
    print("total unclaimed in first 120:", claimed, flush=True)

    # specifically seq 86
    eid86 = cands[85]
    print(f"\nseq86 eid: {eid86}", flush=True)
    print("  in done:", eid86 in done, flush=True)
    print("  in deny:", eid86 in deny, flush=True)
    print("  in claims:", db.claims.find_one({"_id": eid86}) is not None, flush=True)
    print("  cands.index:", cands.index(eid86) + 1, flush=True)
    cli.close()
    print("[done]", flush=True)

main()
