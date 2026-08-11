import os, json
from pymongo import MongoClient
uri = os.environ.get("KEY_7", "").strip()
client = MongoClient(uri, serverSelectionTimeoutMS=15000)
db = client["kts"]
targets = [
    "6825c4c70509281774f8fea8",
    "6825c4c70509281774f8fea9",
    "6825c4c70509281774f8feaa",
    "6825c4c70509281774f8feab",
]
res = db.claims.delete_many({"_id": {"$in": targets}})
print("claims deleted:", res.deleted_count, flush=True)
pc = db.postctl.find_one({"_id": "post"})
if pc:
    print("next_seq:", pc.get("next_seq"), "| lock:", str(pc.get("lock",""))[:25], flush=True)
    db.postctl.update_one({"_id": "post"}, {"$set": {"lock": "", "lock_at": 0}})
    print("lock cleared", flush=True)
left = list(db.claims.find({"_id": {"$in": targets}}))
print("remaining:", len(left), flush=True)
client.close()
print("[done]", flush=True)
