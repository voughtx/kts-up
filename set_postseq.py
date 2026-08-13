#!/usr/bin/env python3
"""set_postseq.py — postctl.next_seq ko pehla undone ordered position pe set karo.
Ordered list (Supabase cands doc) vs done episodes compare karke correct next_seq nikalta hai.
Sirf next_seq update — lock/claims touch nahi hota."""
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

    # 1) current postctl
    pc = db.postctl.find_one({"_id": "post"})
    if not pc:
        print("postctl NONE — naya run init karega, koi action nahi", flush=True)
        cli.close()
        return
    print("before: next_seq:", pc.get("next_seq"), "| lock:", repr(pc.get("lock")), flush=True)

    # 2) ordered cands (Supabase) + done ids (Supabase episodes — source of truth)
    SB = os.environ.get("KEY_21", "").strip()
    cands = []
    try:
        c = sbget(f"{os.environ.get('KEY_20','').rstrip('/')}/rest/v1/progress?select=state&id=eq.cands&limit=1")
        if c:
            cands = (c[0].get("state") or {}).get("eids") or []
    except Exception as e:
        print("cands fetch fail:", str(e)[:80], flush=True)
    print("cands len:", len(cands), flush=True)

    done = set()
    try:
        off = 0
        while True:
            chunk = sbget(f"{os.environ.get('KEY_20','').rstrip('/')}/rest/v1/episodes?select=id&limit=1000&offset={off}")
            if not chunk:
                break
            for r in chunk:
                if r.get("id"):
                    done.add(r["id"])
            off += 1000
            if len(chunk) < 1000:
                break
    except Exception as e:
        print("episodes fetch fail:", str(e)[:80], flush=True)
    print("done eids:", len(done), flush=True)

    deny = set()
    try:
        d = sbget(f"{os.environ.get('KEY_20','').rstrip('/')}/rest/v1/progress?select=state&id=eq.deny&limit=1")
        if d:
            deny = set((d[0].get("state") or {}).get("eids") or [])
    except Exception:
        pass
    print("denied:", len(deny), flush=True)

    # 3) first pending seq
    target = None
    for i, eid in enumerate(cands, 1):
        if eid in done:
            continue
        if eid in deny:
            continue
        target = i
        break
    if target is None:
        print("sab done/denied — kuch pending nahi", flush=True)
        cli.close()
        return
    print("correct next_seq:", target, flush=True)

    # 4) update
    r = db.postctl.update_one({"_id": "post"}, {"$set": {"next_seq": target}})
    print("updated:", r.modified_count, flush=True)
    pc2 = db.postctl.find_one({"_id": "post"})
    print("after: next_seq:", pc2.get("next_seq"), flush=True)
    cli.close()
    print("[done]", flush=True)

main()
