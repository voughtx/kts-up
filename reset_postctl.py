# reset_postctl.py — postctl reset + stale claims cleanup (ordered-post unblock)
import os, sys

def main():
    from pymongo import MongoClient
    uri = os.environ.get("KEY_7", "").strip()
    cli = MongoClient(uri, serverSelectionTimeoutMS=15000)
    db = cli.get_database("kts")
    # 1) postctl delete (naya run init karega — next_seq = pehla undone)
    r1 = db.postctl.delete_many({})
    print(f"[ok] postctl deleted: {r1.deleted_count}", flush=True)
    # 2) stale claims cleanup (30 min se purane)
    import time
    r2 = db.claims.delete_many({"at": {"$lt": int(time.time()) - 1800}})
    print(f"[ok] stale claims deleted: {r2.deleted_count}", flush=True)
    # 3) queue entries? (Supabase se — chhod dete hain, ab queue use nahi hoti)
    cli.close()
    print("[done]", flush=True)

main()
