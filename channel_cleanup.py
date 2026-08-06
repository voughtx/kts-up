# channel_cleanup.py — channel saaf karo:
# 1) delete: 536-540 (DC tests), 551-556 (S10E1-3 + status), 558,560,562,564,566,568,570,572 (status)
# 2) Supabase + Mongo se S10E1-3 records delete (fresh rehne ke liye)
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
SBURL = os.environ.get("KEY_20", "").strip()
SBKEY = os.environ.get("KEY_21", "").strip()

DELETE_IDS = list(range(536, 541)) + list(range(551, 557)) + \
             [558, 560, 562, 564, 566, 568, 570, 572]
S10_IDS = ["686e711252b2d65b4faaf813", "686e711252b2d65b4faaf814", "686e711252b2d65b4faaf815"]  # S10E1-3

def sb_delete(eid):
    try:
        req = urllib.request.Request(
            f"{SBURL}/rest/v1/episodes?id=eq.{eid}",
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
        if not uri:
            print("[!] KEY_7 missing — mongo skip", flush=True)
            return
        cli = MongoClient(uri, serverSelectionTimeoutMS=15000)
        db = cli.get_default_database()
        coll = db.episodes if "episodes" in db.list_collection_names() else db["episodes"]
        res = coll.delete_many({"id": {"$in": eids}})
        print(f"[ok] mongo deleted: {res.deleted_count}", flush=True)
        cli.close()
    except Exception as e:
        print(f"[!] mongo fail: {str(e)[:100]}", flush=True)

async def main():
    print(f"[*] deleting messages: {DELETE_IDS}", flush=True)
    c = TelegramClient(StringSession(SS), AID, AHASH)
    await c.connect()
    ch = await c.get_entity(int(CHAT))
    # pehle verify karo ki jo delete karna hai wo sahi hain
    msgs = await c.get_messages(ch, ids=DELETE_IDS)
    for m in msgs:
        if m is None:
            continue
        fn = ""
        if m.document and m.document.attributes:
            fn = m.document.attributes[0].file_name
        print(f"  {m.id}: {fn[:45]} | {(m.message or '')[:40]}", flush=True)
    # DELETE
    res = await c.delete_messages(ch, DELETE_IDS)
    print(f"[ok] deleted: {len(DELETE_IDS)} (telethon returned {res.ids})", flush=True)
    await c.disconnect()

    # DB cleanup — S10E1-3
    print(f"[*] deleting S10E1-3 records from supabase+mongo", flush=True)
    for eid in S10_IDS:
        st = sb_delete(eid)
        print(f"  supabase {eid[:12]}: {st}", flush=True)
    mongo_delete(S10_IDS)
    print("[done]", flush=True)

asyncio.run(main())
