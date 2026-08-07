# delete_s5.py — S5E1-16 (mids 778-793) channel + DB se delete (re-upload ke liye)
import os, sys, asyncio, json, urllib.request, time

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
MIDS = list(range(794, 802))  # 794..801 (S5E1-8 re-upload ke liye)

def sb_fetch():
    url = f"{SBURL}/rest/v1/episodes?select=id,mid,season,episode&limit=2000"
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
    print(f"[*] deleting channel msgs {MIDS[0]}..{MIDS[-1]}", flush=True)
    c = TelegramClient(StringSession(SS), AID, AHASH)
    await c.connect()
    ch = await c.get_entity(int(CHAT))
    msgs = await c.get_messages(ch, ids=MIDS)
    n = 0
    for m in msgs:
        if m is None:
            continue
        n += 1
        fn = m.document.attributes[0].file_name if m.document and m.document.attributes else ""
        print(f"  {m.id}: {fn[:50]}", flush=True)
    res = await c.delete_messages(ch, MIDS)
    print(f"[ok] channel deleted: {n}", flush=True)
    await c.disconnect()

    rows = sb_fetch()
    targets = [r for r in rows if r.get("mid") in MIDS]
    ids = [r["id"] for r in targets]
    print(f"[*] db records: {len(targets)}", flush=True)
    for eid in ids:
        st = sb_delete(eid)
        print(f"  supabase {eid[:12]}: {st}", flush=True)
    mongo_delete(ids)
    # claims bhi clear (S5 wale — re-claim ho sakein)
    try:
        from pymongo import MongoClient
        uri = os.environ.get("KEY_7", "").strip()
        cli = MongoClient(uri, serverSelectionTimeoutMS=15000)
        db = cli.get_database("kts")
        r = db.claims.delete_many({})
        print(f"[ok] claims cleared: {r.deleted_count}", flush=True)
        r2 = db.postctl.delete_many({})
        print(f"[ok] postctl cleared: {r2.deleted_count}", flush=True)
        cli.close()
    except Exception as e:
        print(f"[!] mongo claims/postctl: {str(e)[:80]}", flush=True)
    print("[done]", flush=True)

asyncio.run(main())
