#!/usr/bin/env python3
"""fix_order_v3.py — USER APPROVED: 8185(E31)+8186(E29-meta-fail) delete,
E28/E29/E30/E31 free, postctl reset -> E28 se start. Full 24-hex ids.
Kabhi title/caption print nahi."""
import os, sys, json, time, urllib.request, asyncio

E28 = "68832d7fb66aa780ec8d6497"   # free (8180 deleted)
E29 = "68832d7fb66aa780ec8d6498"   # 8186 (meta-fail post) -> delete
E30 = "68832d7fb66aa780ec8d6499"   # free (8181 deleted)
E31 = "68832d7fb66aa780ec8d649a"   # 8185 -> delete
DEL_MIDS = [8185, 8186]
FREE_IDS = [E28, E30]           # already gone from channel — just ensure free
DEL_IDS = [E29, E31]
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

    print("== [1/4] mongo check ==", flush=True)
    for lbl, eid in [("E28", E28), ("E29", E29), ("E30", E30), ("E31", E31)]:
        r = db.episodes.find_one({"id": eid}, {"id": 1, "mid": 1})
        print(f"  {lbl}: {r.get('mid') if r else 'NOT in mongo'}", flush=True)

    print("== [2/4] telegram delete 8185, 8186 ==", flush=True)
    from telethon import TelegramClient
    from telethon.sessions import StringSession
    client = TelegramClient(StringSession(os.environ.get("KEY_18", "").strip()),
                            int(os.environ.get("KEY_16", "0").strip()),
                            os.environ.get("KEY_17", "").strip(),
                            connection_retries=2)
    await client.connect()
    await client.get_me()
    ent = await client.get_entity(CH)
    for mid in DEL_MIDS:
        try:
            m = await client.get_messages(ent, ids=mid)
            if m is None:
                print(f"  {mid} skip-none", flush=True)
                continue
            await client.delete_messages(ent, [mid])
            print(f"  {mid} deleted", flush=True)
        except Exception as e:
            print(f"  {mid} ERR {str(e)[:60]}", flush=True)
        await asyncio.sleep(0.5)
    await client.disconnect()

    print("== [3/4] supabase + mongo delete ==", flush=True)
    all_ids = DEL_IDS + FREE_IDS
    id_in = ",".join(all_ids)
    try:
        hdrs = {"apikey": SBKEY, "Authorization": f"Bearer {SBKEY}", "Prefer": "return=minimal"}
        req = urllib.request.Request(SB + f"/rest/v1/episodes?id=in.({id_in})", method="DELETE", headers=hdrs)
        with urllib.request.urlopen(req, timeout=30) as r:
            print(f"  supabase delete status: {r.status}", flush=True)
    except Exception as e:
        print(f"  supabase delete ERR: {str(e)[:80]}", flush=True)
    r1 = db.episodes.delete_many({"id": {"$in": all_ids}})
    print(f"  mongo episodes deleted: {r1.deleted_count}", flush=True)
    r2 = db.claims.delete_many({"_id": {"$in": all_ids}})
    print(f"  mongo claims deleted: {r2.deleted_count}", flush=True)

    print("== [4/4] postctl reset ==", flush=True)
    pc = db.postctl.find_one({"_id": "post"})
    print(f"  postctl before: {pc.get('next_seq') if pc else 'NONE'}", flush=True)
    db.postctl.delete_one({"_id": "post"})
    print("  postctl deleted (E28 se init)", flush=True)
    left = db.episodes.count_documents({"id": {"$in": all_ids}})
    print(f"  leftover mongo: {left}", flush=True)
    cli.close()
    print("[done]", flush=True)

if __name__ == "__main__":
    asyncio.run(main())
