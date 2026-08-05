# KTS sync_missing.py — MongoDB episodes ko Supabase mein sync karta hai (missing rows backfill)
# original "at" timestamps preserve karta hai taaki dashboard timeline sahi lage
import os, json, urllib.request as u

K7 = os.environ.get("KEY_7", "").strip()
SBURL = os.environ.get("KEY_20", "").strip().rstrip("/")
SBKEY = os.environ.get("KEY_21", "").strip()

def sb_get_ids():
    req = u.Request(f"{SBURL}/rest/v1/episodes?select=id",
                    headers={"apikey": SBKEY, "Authorization": f"Bearer {SBKEY}"})
    with u.urlopen(req, timeout=30) as r:
        rows = json.loads(r.read().decode())
    return set(r.get("id") for r in rows)

def sb_upsert(row):
    req = u.Request(f"{SBURL}/rest/v1/episodes", data=json.dumps(row).encode(), method="POST",
                    headers={"apikey": SBKEY, "Authorization": f"Bearer {SBKEY}",
                             "Content-Type": "application/json",
                             "Prefer": "resolution=merge-duplicates"})
    with u.urlopen(req, timeout=30) as r:
        return r.status

def main():
    import pymongo
    mc = pymongo.MongoClient(K7, serverSelectionTimeoutMS=8000)
    db = mc.get_database("kts")
    docs = list(db.episodes.find({}))
    print(f"[*] mongo episodes: {len(docs)}")
    existing = sb_get_ids()
    print(f"[*] supabase ids: {len(existing)}")
    missing = [d for d in docs if d.get("id") not in existing]
    print(f"[*] missing: {len(missing)}")
    for d in missing:
        row = {
            "id": d.get("id", ""),
            "show": d.get("show", ""),
            "franchise": d.get("franchise", ""),
            "season": d.get("season"),
            "episode": d.get("episode"),
            "title": d.get("title", ""),
            "quality": d.get("quality", ""),
            "qualities": d.get("qualities") or [],
            "lang": d.get("lang", ""),
            "category": d.get("category", ""),
            "type": d.get("type", ""),
            "thumb": d.get("thumb", ""),
            "fid": d.get("fid", ""),
            "bot_fid": d.get("bot_fid", ""),
            "mid": d.get("mid"),
            "turl": d.get("turl", ""),
            "perm": d.get("perm", ""),
            "web": d.get("web", ""),
            "size": d.get("size", 0),
            "status": d.get("status", "done"),
            "at": d.get("at") or int(__import__("time").time()),
        }
        try:
            st = sb_upsert(row)
            print(f"[ok] {row['id']} | {row.get('show')} S{row.get('season')}E{row.get('episode')} | {row.get('title')} | HTTP {st}")
        except Exception as e:
            print(f"[!] {row['id']} fail: {str(e)[:80]}")
    print("[done]")

if __name__ == "__main__":
    main()
