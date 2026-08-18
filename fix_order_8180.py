#!/usr/bin/env python3
"""fix_order_8180.py — USER APPROVED: 8180(S4E28)+8181(S4E30) delete (out-of-order),
E26/E27/E29 re-upload ke liye free. Channel msgs + supabase + mongo clean.
E26=ec8d6495 E27=ec8d6496 E28=ec8d6497 E29=ec8d6498 E30=ec8d6499 (sequence).
Position-only output. Kabhi title/caption print nahi."""
import os, sys, json, time, urllib.request, asyncio

DEL_POST_IDS = ["ec8d6497", "ec8d6499"]   # E28, E30 -> posted (8180, 8181) delete
DEL_MIDS = [8180, 8181]
VERIFY_IDS = ["ec8d6495", "ec8d6496", "ec8d6498"]  # E26, E27, E29 — free rahne chahiye
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

    print("== [1/4] telegram delete ==", flush=True)
    from telethon import TelegramClient
    from telethon.sessions import StringSession
    client = TelegramClient(StringSession(os.environ.get("KEY_18", "").strip()),
                            int(os.environ.get("KEY_16", "0").strip()),
                            os.environ.get("KEY_17", "").strip(),
                            connection_retries=2)
    await client.connect()
    await client.get_me()
    ent = await client.get_entity(CH)
    okd = 0
    for mid in DEL_MIDS:
        try:
            m = await client.get_messages(ent, ids=mid)
            if m is None:
                print(f"  {mid} skip-none", flush=True)
                continue
            await client.delete_messages(ent, [mid])
            okd += 1
            print(f"  {mid} deleted", flush=True)
        except Exception as e:
            print(f"  {mid} ERR {str(e)[:60]}", flush=True)
        await asyncio.sleep(0.5)
    print(f"  tg deleted {okd}/{len(DEL_MIDS)}", flush=True)
    await client.disconnect()

    print("== [2/4] supabase delete ==", flush=True)
    id_in = ",".join(DEL_POST_IDS)
    try:
        hdrs = {"apikey": SBKEY, "Authorization": f"Bearer {SBKEY}", "Prefer": "return=minimal"}
        req = urllib.request.Request(SB + f"/rest/v1/episodes?id=in.({id_in})", method="DELETE", headers=hdrs)
        with urllib.request.urlopen(req, timeout=30) as r:
            print(f"  supabase delete status: {r.status}", flush=True)
    except Exception as e:
        print(f"  supabase delete ERR: {str(e)[:80]}", flush=True)

    print("== [3/4] mongo clean ==", flush=True)
    r1 = db.episodes.delete_many({"id": {"$in": DEL_POST_IDS}})
    print(f"  mongo episodes deleted (E28,E30): {r1.deleted_count}", flush=True)
    r2 = db.claims.delete_many({"_id": {"$in": DEL_POST_IDS}})
    print(f"  mongo claims deleted: {r2.deleted_count}", flush=True)
    # E26/E27/E29 — galat done-row ho to free karo (channel pe kabhi posted nahi)
    vrows = list(db.episodes.find({"id": {"$in": VERIFY_IDS}}, {"id": 1, "mid": 1}))
    print(f"  E26/E27/E29 in mongo: {len(vrows)} rows", flush=True)
    for v in vrows:
        print(f"    {v['id'][-8:]} mid={v.get('mid')}", flush=True)
    r3 = db.episodes.delete_many({"id": {"$in": VERIFY_IDS}, "mid": {"$in": [0, None]}})
    print(f"  E26/E27/E29 mid=0 rows cleaned: {r3.deleted_count}", flush=True)
    r4 = db.claims.delete_many({"_id": {"$in": VERIFY_IDS}})
    print(f"  E26/E27/E29 claims cleaned: {r4.deleted_count}", flush=True)

    print("== [4/4] postctl reset (E26 se start) ==", flush=True)
    pc = db.postctl.find_one({"_id": "post"})
    print(f"  postctl before: next_seq={pc.get('next_seq') if pc else 'NONE'}", flush=True)
    db.postctl.delete_one({"_id": "post"})  # re-init -> first undone = E26
    print("  postctl deleted (agli run E26 se init karega)", flush=True)

    # final verify
    left = db.episodes.count_documents({"id": {"$in": DEL_POST_IDS}})
    print(f"  leftover DEL ids in mongo: {left}", flush=True)
    cli.close()
    print("[done]", flush=True)

if __name__ == "__main__":
    asyncio.run(main())
