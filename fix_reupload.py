#!/usr/bin/env python3
"""fix_reupload.py — 3 shows (Little Baldy, Courage, Jujutsu) ka mongo state reset:
1) episodes collection se in shows ke saare episode ids delete (done_ids source)
   -> system E1 se re-upload karega (E4 skip bug fix)
2) show_posters se in shows delete -> poster dobara post hoga
3) claims cleanup
Titles nahi print hote — sirf counts."""
import os, sys, json, time, urllib.request

try:
    import cryptg  # noqa
except Exception:
    os.system(f"{sys.executable} -m pip install -q cryptg")

from pymongo import MongoClient

AID = int(os.environ.get("KEY_16", "0").strip())
AHASH = os.environ.get("KEY_17", "").strip()
SBURL = os.environ.get("KEY_20", "").strip().rstrip("/")
SBKEY = os.environ.get("KEY_21", "").strip()
SHOW_IDS = ["68354cfb2d3fded2dcca04e1", "683554362454037aca2590f1", "683d47473fb4a3d6f197c6f8"]

def sbget(qs):
    req = urllib.request.Request(f"{SBURL}/rest/v1/progress?{qs}",
        headers={"apikey": SBKEY, "Authorization": f"Bearer {SBKEY}"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())

def api_get(path):
    t = sbget("select=state&id=eq.token&limit=1")
    tok = (t[0].get("state") or {}).get("token", "")
    req = urllib.request.Request(f"https://api.kartoons.me/api{path}",
        headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json",
                 "Origin": "https://kartoons.me/", "Referer": "https://kartoons.me/",
                 "Authorization": f"Bearer {tok}"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())

def main():
    uri = os.environ.get("KEY_7", "").strip()
    cli = MongoClient(uri, serverSelectionTimeoutMS=15000)
    db = cli.get_database("kts")

    # 1) saare episode ids fetch (3 shows)
    allids = []
    for sid in SHOW_IDS:
        d = api_get(f"/shows/{sid}")
        seas = d.get("data", {}).get("seasons") or []
        for s in seas:
            eps = api_get(f"/shows/{sid}/season/{s['_id']}/all-episodes").get("data") or []
            for e in eps:
                if e.get("_id"):
                    allids.append(e["_id"])
            time.sleep(0.2)
    print(f"total episode ids fetched: {len(allids)}", flush=True)

    # 2) episodes collection se delete (done_ids source)
    if allids:
        r = db.episodes.delete_many({"_id": {"$in": allids}})
        print(f"mongo episodes deleted: {r.deleted_count}", flush=True)

    # 3) show_posters delete
    r2 = db.show_posters.delete_many({"_id": {"$in": SHOW_IDS}})
    print(f"show_posters deleted: {r2.deleted_count}", flush=True)

    # 4) claims delete
    r3 = db.claims.delete_many({"_id": {"$in": allids}})
    print(f"claims deleted: {r3.deleted_count}", flush=True)

    # 5) postctl next_seq reset (naya run init karega)
    db.postctl.delete_many({})
    print("postctl deleted (naya run init karega)", flush=True)

    cli.close()
    print("[done]", flush=True)

main()
