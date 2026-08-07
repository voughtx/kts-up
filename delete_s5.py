# delete_s5.py — S5 ke SAARE episodes channel + DB se delete (re-upload ke liye)
# Dynamic: Supabase se saare S5 records fetch, mids nikaal, channel se delete
import os, sys, asyncio, json, urllib.request

try:
    import cryptg  # noqa
except Exception:
    os.system(f"{sys.executable} -m pip install -q cryptg")

from telethon import TelegramClient
from telethon.sessions import StringSession

CHAT = os.environ.get("KEY_2", "").strip()
AID = int(os.environ.get("KEY_16", "0").strip())
AHASH = os.environ.get("KEY_17", "").strip()
SS = os.environ.get("KEY_18", "").strip()
SBURL = os.environ.get("KEY_20", "").strip().rstrip("/")
SBKEY = os.environ.get("KEY_21", "").strip()

def sb_fetch():
    url = f"{SBURL}/rest/v1/episodes?select=id,mid,season,episode,title&limit=2000"
    req = urllib.request.Request(url, headers={"apikey": SBKEY, "Authorization": f"Bearer {SBKEY}"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())

def sb_delete(eid):
    try:
        req = urllib.request.Request(f"{SBURL}/rest/v1/episodes?id=eq.{eid}",
                                     headers={"apikey": SBKEY, "Authorization": f"Bearer {SBKEY}"},
                                     method="DELETE")
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code

def mongo_delete(eids):
    try:
        from pymongo import MongoClient
        uri = os.environ.get("KEY_7", "").strip()
        cli = MongoClient(uri, serverSelectionTimeoutMS=15000)
        db = cli.get_database("kts")
        res = db.episodes.delete_many({"id": {"$in": eids}})
        print(f"[ok] mongo deleted: {res.deleted_count}", flush=True)
        cli.close()
    except Exception as e:
        print(f"[!] mongo fail: {str(e)[:80]}", flush=True)

async def main():
    rows = sb_fetch()
    s5 = [r for r in rows if (r.get("season") or 0) == 5]
    s5.sort(key=lambda x: x.get("episode") or 0)
    print(f"[*] S5 records: {len(s5)}", flush=True)
    mids = [r["mid"] for r in s5 if r.get("mid")]
    ids = [r["id"] for r in s5]
    print(f"[*] mids: {mids}", flush=True)
    for r in s5:
        print(f"  S5E{r.get('episode')} mid={r.get('mid')} {str(r.get('title'))[:30]}", flush=True)

    if mids:
        c = TelegramClient(StringSession(SS), AID, AHASH)
        await c.connect()
        ch = await c.get_entity(int(CHAT))
        msgs = await c.get_messages(ch, ids=mids)
        n = sum(1 for m in msgs if m is not None)
        res = await c.delete_messages(ch, mids)
        print(f"[ok] channel deleted: {n}", flush=True)
        await c.disconnect()

    for eid in ids:
        st = sb_delete(eid)
        print(f"  supabase {eid[:12]}: {st}", flush=True)
    mongo_delete(ids)

    # claims + postctl clear (fresh start)
    try:
        from pymongo import MongoClient
        uri = os.environ.get("KEY_7", "").strip()
        cli = MongoClient(uri, serverSelectionTimeoutMS=15000)
        db = cli.get_database("kts")
        r = db.claims.delete_many({})
        r2 = db.postctl.delete_many({})
        print(f"[ok] claims={r.deleted_count} postctl={r2.deleted_count} cleared", flush=True)
        cli.close()
    except Exception as e:
        print(f"[!] mongo claims/postctl: {str(e)[:80]}", flush=True)
    print("[done]", flush=True)

asyncio.run(main())
