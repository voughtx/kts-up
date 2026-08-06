# channel_cleanup3.py — 574 (S1E20) delete, taaki E11-E20 sab fresh order mein upload ho
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
MID = 574

def sb_fetch():
    url = f"{SBURL}/rest/v1/episodes?select=id,mid,title,season,episode&limit=1000"
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
        print(f"[!] mongo fail: {str(e)[:100]}", flush=True)

async def main():
    print(f"[*] deleting msg {MID} + DB record", flush=True)
    c = TelegramClient(StringSession(SS), AID, AHASH)
    await c.connect()
    ch = await c.get_entity(int(CHAT))
    msgs = await c.get_messages(ch, ids=[MID])
    for m in msgs:
        if m is None:
            continue
        fn = m.document.attributes[0].file_name if m.document and m.document.attributes else ""
        print(f"  {m.id}: {fn[:50]}", flush=True)
    res = await c.delete_messages(ch, [MID])
    print(f"[ok] channel deleted: {res}", flush=True)
    await c.disconnect()

    rows = sb_fetch()
    targets = [r for r in rows if r.get("mid") == MID]
    ids = [r["id"] for r in targets]
    for r in targets:
        print(f"  db: S{r.get('season')}E{r.get('episode')} {r.get('id','')[:14]}", flush=True)
    for eid in ids:
        print(f"  supabase del {eid[:12]}: {sb_delete(eid)}", flush=True)
    mongo_delete(ids)
    print("[done]", flush=True)

asyncio.run(main())
