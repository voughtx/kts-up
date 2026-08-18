#!/usr/bin/env python3
"""fix_order_8184.py v2 — USER APPROVED: E28 phir skip. Root cause: mongo me
E28/E30 done-rows 8-char id se delete nahi hue the (full id chahiye).
Ab FULL ids se mongo + supabase clean, 8184(E29) delete, postctl reset -> E28 first.
Kabhi title/caption print nahi."""
import os, sys, json, time, urllib.request, asyncio

# FULL 24-hex ids (prefix 68832d7fb66aa780)
E28 = "68832d7fb66aa780ec8d6497"
E29 = "68832d7fb66aa780ec8d6498"
E30 = "68832d7fb66aa780ec8d6499"
DEL_MIDS = [8184]   # E29 out-of-order channel msg
SB = os.environ.get("KEY_20", "").strip().rstrip("/")
SBKEY = os.environ.get("KEY_21", "").strip()
CH = int(os.environ.get("KEY_2", "0").strip())

def sb_json(url, method="GET", body=None):
    hdrs = {"apikey": SBKEY, "Authorization": f"Bearer {SBKEY}", "Content-Type": "application/json",
            "Prefer": "resolution=merge-duplicates"}
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers=hdrs)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode() or "null")

async def main():
    from pymongo import MongoClient
    uri = os.environ.get("KEY_7", "").strip()
    cli = MongoClient(uri, serverSelectionTimeoutMS=20000)
    db = cli["kts"]

    print("== [1/4] mongo check (full ids) ==", flush=True)
    for lbl, eid in [("E28", E28), ("E29", E29), ("E30", E30)]:
        r = db.episodes.find_one({"id": eid}, {"id": 1, "mid": 1, "status": 1})
        print(f"  {lbl}: {r if r else 'NOT in mongo'}", flush=True)

    print("== [2/4] mongo delete (full ids) ==", flush=True)
    r1 = db.episodes.delete_many({"id": {"$in": [E28, E29, E30]}})
    print(f"  mongo episodes deleted: {r1.deleted_count}", flush=True)
    r2 = db.claims.delete_many({"_id": {"$in": [E28, E29, E30]}})
    print(f"  mongo claims deleted: {r2.deleted_count}", flush=True)

    print("== [3/4] telegram delete 8184 ==", flush=True)
    from telethon import TelegramClient
    from telethon.sessions import StringSession
    client = TelegramClient(StringSession(os.environ.get("KEY_18", "").strip()),
                            int(os.environ.get("KEY_16", "0").strip()),
                            os.environ.get("KEY_17", "").strip(),
                            connection_retries=2)
    await client.connect()
    await client.get_me()
    ent = await client.get_entity(CH)
    try:
        m = await client.get_messages(ent, ids=8184)
        if m is None:
            print("  8184 skip-none", flush=True)
        else:
            await client.delete_messages(ent, [8184])
            print("  8184 deleted", flush=True)
    except Exception as e:
        print(f"  8184 ERR {str(e)[:60]}", flush=True)
    await client.disconnect()

    print("== [4/4] supabase + postctl ==", flush=True)
    id_in = ",".join([E28, E29, E30])
    try:
        hdrs = {"apikey": SBKEY, "Authorization": f"Bearer {SBKEY}", "Prefer": "return=minimal"}
        req = urllib.request.Request(SB + f"/rest/v1/episodes?id=in.({id_in})", method="DELETE", headers=hdrs)
        with urllib.request.urlopen(req, timeout=30) as r:
            print(f"  supabase delete status: {r.status}", flush=True)
    except Exception as e:
        print(f"  supabase delete ERR: {str(e)[:80]}", flush=True)
    pc = db.postctl.find_one({"_id": "post"})
    print(f"  postctl before: {pc.get('next_seq') if pc else 'NONE'}", flush=True)
    db.postctl.delete_one({"_id": "post"})
    print("  postctl deleted (E28 se init)", flush=True)
    left = db.episodes.count_documents({"id": {"$in": [E28, E29, E30]}})
    print(f"  leftover in mongo: {left}", flush=True)
    cli.close()
    print("[done]", flush=True)

if __name__ == "__main__":
    asyncio.run(main())
