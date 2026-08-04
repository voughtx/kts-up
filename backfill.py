# KTS backfill tool — ek doc Mongo + Supabase me save karta hai
# Use: workflow_dispatch (backfill.yml) ke through, DOC_JSON_B64 env me
# doc mein "_progress": true ho to Supabase progress table (id, state) mein save hota hai
import os, json, base64, urllib.request as u

K7 = os.environ.get("KEY_7", "")
SBURL = os.environ.get("KEY_20", "")
SBKEY = os.environ.get("KEY_21", "")

raw = os.environ.get("DOC_JSON_B64", "")
if not raw:
    print("[!] DOC_JSON_B64 missing")
    raise SystemExit(1)
doc = json.loads(base64.b64decode(raw).decode())
print("[*] backfill:", doc.get("id"), "|", doc.get("title") or doc.get("state", {}).get("result", ""))

if doc.get("_progress"):
    # Supabase progress row
    if SBURL and SBKEY:
        try:
            row = {"id": doc["id"], "state": doc.get("state", {})}
            req = u.Request(f"{SBURL}/rest/v1/progress", data=json.dumps(row).encode(), method="POST",
                headers={"apikey": SBKEY, "Authorization": f"Bearer {SBKEY}",
                         "Content-Type": "application/json", "Prefer": "resolution=merge-duplicates"})
            with u.urlopen(req, timeout=30) as r:
                print("[ok] supabase progress saved", r.status)
        except Exception as e:
            print("[!] supabase progress fail:", str(e)[:100])
    print("[done]")
    raise SystemExit(0)

if K7:
    try:
        import pymongo
        mc = pymongo.MongoClient(K7, serverSelectionTimeoutMS=8000)
        db = mc.get_database("kts")
        db.episodes.replace_one({"id": doc["id"]}, doc, upsert=True)
        print("[ok] mongo saved")
    except Exception as e:
        print("[!] mongo fail:", str(e)[:100])

if SBURL and SBKEY:
    try:
        row = {k: doc.get(k, "") for k in ["id","show","franchise","season","episode","title",
                "quality","lang","category","type","thumb","fid","bot_fid","mid","turl",
                "perm","web","size"]}
        row["qualities"] = doc.get("qualities") or []
        row["status"] = "done"
        row["at"] = doc.get("at", int(__import__("time").time()))
        req = u.Request(f"{SBURL}/rest/v1/episodes", data=json.dumps(row).encode(), method="POST",
            headers={"apikey": SBKEY, "Authorization": f"Bearer {SBKEY}",
                     "Content-Type": "application/json", "Prefer": "resolution=merge-duplicates"})
        with u.urlopen(req, timeout=30) as r:
            print("[ok] supabase saved", r.status)
    except Exception as e:
        print("[!] supabase fail:", str(e)[:100])
print("[done]")
