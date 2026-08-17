#!/usr/bin/env python3
"""reupload_show1.py — USER APPROVED: 7881..7891 (E1-E11) delete + re-upload prep.
Step 1: Telegram channel messages delete (user session).
Step 2: Supabase episodes rows delete (mid>7880).
Step 3: Mongo cleanup: episodes rows, claims, poster lock (dcca04e1), postctl reset.
Position-only output. Kabhi titles/captions print nahi.
"""
import os, sys, asyncio, json, time, urllib.request

# ---------- env ----------
SB = os.environ.get("KEY_21", "").strip()
CH = int(os.environ.get("KEY_2", "0").strip())
AID = int(os.environ.get("KEY_16", "0").strip())
AHASH = os.environ.get("KEY_17", "").strip()
SS = os.environ.get("KEY_18", "").strip()
MONGO_URI = os.environ.get("KEY_7", "").strip()
SHOW1 = "68354cfb2d3fded2dcca04e1"  # poster lock to clear (user-approved re-upload show)


def sb_json(url, method="GET", body=None):
    hdrs = {"apikey": SB, "Authorization": f"Bearer {SB}", "Content-Type": "application/json"}
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers=hdrs)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode() or "null")


def main():
    print("== [1/4] fetch posted eps (mid>7880) ==", flush=True)
    eps = sb_json(f"{SB}/rest/v1/episodes?select=mid,id&mid=gt.7880&order=mid.desc&limit=100")
    mids = sorted(e["mid"] for e in eps)
    eids = [e["id"] for e in eps]
    print("  found:", len(eps), "| mids:", mids[0], "..", mids[-1], flush=True)
    if not eids:
        print("  NOTHING to delete — abort", flush=True)
        return
    mid_in = ",".join(str(m) for m in mids)
    id_in = ",".join(eids)

    # ---------- Telegram delete ----------
    print("== [2/4] telegram delete ==", flush=True)
    if not SS:
        print("  no user session — SKIP tg delete (DB rows still cleaned)", flush=True)
    else:
        try:
            import cryptg  # noqa
        except Exception:
            os.system(f"{sys.executable} -m pip install -q cryptg")
        from telethon import TelegramClient
        from telethon.sessions import StringSession

        async def tg_del():
            c = TelegramClient(StringSession(SS), AID, AHASH, connection_retries=2)
            await c.connect()
            ent = await c.get_entity(CH)
            ok = 0
            fail = 0
            for mid in mids:
                try:
                    m = await c.get_messages(ent, ids=mid)
                    if m is None:
                        print(f"  {mid} skip-none", flush=True)
                        continue
                    await c.delete_messages(ent, [mid])
                    ok += 1
                    print(f"  {mid} deleted", flush=True)
                except Exception as e:
                    print(f"  {mid} ERR {str(e)[:60]}", flush=True)
                    fail += 1
                await asyncio.sleep(0.5)
            print(f"  tg deleted {ok} | fail {fail}", flush=True)
            await c.disconnect()

        asyncio.run(tg_del())

    # ---------- Supabase episodes delete ----------
    print("== [3/4] supabase episodes delete ==", flush=True)
    try:
        hdrs = {"apikey": SB, "Authorization": f"Bearer {SB}", "Prefer": "return=minimal"}
        req = urllib.request.Request(
            f"{SB}/rest/v1/episodes?id=in.({id_in})", method="DELETE", headers=hdrs)
        with urllib.request.urlopen(req, timeout=30) as r:
            print("  supabase delete status:", r.status, flush=True)
    except Exception as e:
        print("  supabase delete ERR:", str(e)[:120], flush=True)

    # ---------- Mongo cleanup ----------
    print("== [4/4] mongo cleanup ==", flush=True)
    from pymongo import MongoClient
    cli = MongoClient(MONGO_URI, serverSelectionTimeoutMS=20000)
    db = cli["kts"]
    r1 = db.episodes.delete_many({"id": {"$in": eids}})
    print("  mongo episodes deleted:", r1.deleted_count, flush=True)
    r2 = db.claims.delete_many({"_id": {"$in": eids}})
    print("  mongo claims deleted:", r2.deleted_count, flush=True)
    r3 = db.show_posters.delete_many({"_id": SHOW1})
    print("  poster lock cleared:", r3.deleted_count, flush=True)
    r4 = db.postctl.update_one({"_id": "post"}, {"$set": {"next_seq": 1, "lock": "", "lock_at": 0}})
    print("  postctl reset:", "ok" if r4.modified_count or r4.matched_count else "MISSING", flush=True)
    pc = db.postctl.find_one({"_id": "post"})
    print("  postctl now: next_seq=%s lock=%r" % (pc.get("next_seq"), pc.get("lock")), flush=True)
    left = db.episodes.count_documents({"id": {"$in": eids}})
    print("  leftover mongo eps:", left, flush=True)
    cli.close()
    print("[done]", flush=True)


if __name__ == "__main__":
    main()
