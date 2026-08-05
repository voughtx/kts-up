# delete_episode.py — movie test row ko Supabase + Mongo se delete (taaki movies fresh reh)
import os, json, urllib.request as u

SBURL = os.environ.get("KEY_20", "").strip().rstrip("/")
SBKEY = os.environ.get("KEY_21", "").strip()
K7 = os.environ.get("KEY_7", "").strip()
EP_ID = os.environ.get("EP_ID", "").strip()

if SBURL and SBKEY and EP_ID:
    try:
        req = u.Request(f"{SBURL}/rest/v1/episodes?id=eq.{u.quote(EP_ID)}", method="DELETE",
                        headers={"apikey": SBKEY, "Authorization": f"Bearer {SBKEY}"})
        with u.urlopen(req, timeout=30) as r:
            print(f"[ok] supabase deleted {EP_ID} ({r.status})")
    except Exception as e:
        print(f"[!] supabase delete fail: {str(e)[:80]}")
else:
    print("[!] SB/EP_ID missing")

if K7 and EP_ID:
    try:
        import pymongo
        mc = pymongo.MongoClient(K7, serverSelectionTimeoutMS=8000)
        db = mc.get_database("kts")
        res = db.episodes.delete_one({"id": EP_ID})
        print(f"[ok] mongo deleted {EP_ID} (deleted: {res.deleted_count})")
    except Exception as e:
        print(f"[!] mongo delete fail: {str(e)[:80]}")
print("[done]")
