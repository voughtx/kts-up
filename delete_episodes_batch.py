# delete_episodes_batch.py — multiple episodes ko Supabase + Mongo se delete (batch)
import os, json, urllib.request as u

SBURL = os.environ.get("KEY_20", "").strip().rstrip("/")
SBKEY = os.environ.get("KEY_21", "").strip()
K7 = os.environ.get("KEY_7", "").strip()
EP_IDS = [x.strip() for x in os.environ.get("EP_IDS", "").split(",") if x.strip()]

print(f"[*] episodes to delete: {len(EP_IDS)}")

for eid in EP_IDS:
    ok_sb = False
    if SBURL and SBKEY:
        try:
            req = u.Request(f"{SBURL}/rest/v1/episodes?id=eq.{u.quote(eid)}", method="DELETE",
                            headers={"apikey": SBKEY, "Authorization": f"Bearer {SBKEY}"})
            with u.urlopen(req, timeout=30) as r:
                ok_sb = True
                print(f"[ok] supabase deleted {eid} ({r.status})")
        except Exception as e:
            print(f"[!] supabase delete fail {eid}: {str(e)[:60]}")
    ok_m = False
    if K7:
        try:
            import pymongo
            mc = pymongo.MongoClient(K7, serverSelectionTimeoutMS=8000)
            db = mc.get_database("kts")
            res = db.episodes.delete_one({"id": eid})
            ok_m = res.deleted_count > 0
            print(f"[ok] mongo deleted {eid} (deleted: {res.deleted_count})")
        except Exception as e:
            print(f"[!] mongo delete fail {eid}: {str(e)[:60]}")

print("[done]")
