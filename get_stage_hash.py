# get_stage_hash.py — stage channel ka access_hash nikaal ke config mein save karo
import os, sys, asyncio, json, urllib.request

try:
    import cryptg  # noqa
except Exception:
    os.system(f"{sys.executable} -m pip install -q cryptg")

from telethon import TelegramClient
from telethon.sessions import StringSession

AID = int(os.environ.get("KEY_16", "0").strip())
AHASH = os.environ.get("KEY_17", "").strip()
SS = os.environ.get("KEY_18", "").strip()
SBURL = os.environ.get("KEY_20", "").strip().rstrip("/")
SBKEY = os.environ.get("KEY_21", "").strip()
STAGE = "-1004394456964"

async def main():
    c = TelegramClient(StringSession(SS), AID, AHASH)
    await c.connect()
    ent = await c.get_entity(int(STAGE))
    print(f"[*] stage: {ent.title} | id={ent.id} | access_hash={ent.access_hash}", flush=True)
    await c.disconnect()
    # config update
    body = json.dumps({"id": "config", "state": {"stage_ch": STAGE, "stage_hash": str(ent.access_hash), "at": int(__import__("time").time())}}).encode()
    req = urllib.request.Request(f"{SBURL}/rest/v1/progress", data=body, method="POST",
        headers={"apikey": SBKEY, "Authorization": f"Bearer {SBKEY}",
                 "Content-Type": "application/json", "Prefer": "resolution=merge-duplicates"})
    with urllib.request.urlopen(req, timeout=30) as r:
        print(f"[ok] config saved HTTP {r.status}", flush=True)
    print("[done]", flush=True)

asyncio.run(main())
