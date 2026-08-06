# channel_cleanup2.py — 557-573 delete (S1E11-19 no-thumb) + DB records
# User: "thumbnail wale jo nhi ho paye unhe yaha tak delete karo, re-upload karenge"
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
MIDS = list(range(557, 574))  # 557..573 (9 no-thumb episodes)

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
    print(f"[*] deleting channel msgs {MIDS[0]}..{MIDS[-1]} + DB records", flush=True)
    c = TelegramClient(StringSession(SS), AID, AHASH)
    await c.connect()
    ch = await c.get_entity(int(CHAT))
    msgs = await c.get_messages(ch, ids=MIDS)
    n = 0
    for m in msgs:
        if m is None:
            continue
        n += 1
        fn = ""
        if m.document and m.document.attributes:
            fn = m.document.attributes[0].file_name
        print(f"  {m.id}: {fn[:50]} | {(m.message or '')[:35]}", flush=True)
    res = await c.delete_messages(ch, MIDS)
    print(f"[ok] channel deleted: {n} -> {res}", flush=True)
    await c.disconnect()

    rows = sb_fetch()
    targets = [r for r in rows if r.get("mid") in MIDS]
    print(f"[*] db records found: {len(targets)}", flush=True)
    ids = [r["id"] for r in targets]
    for r in sorted(targets, key=lambda x: x.get("mid") or 0):
        print(f"  {r.get('mid')}: S{r.get('season')}E{r.get('episode')} {r.get('id','')[:14]}", flush=True)
    for eid in ids:
        st = sb_delete(eid)
        print(f"  supabase del {eid[:12]}: {st}", flush=True)
    mongo_delete(ids)
    print("[done]", flush=True)

asyncio.run(main())
