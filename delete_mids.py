# delete_mids.py — channel se test mids delete + Supabase links rows delete
import os, json, urllib.request as u, asyncio
from pyrogram import Client

K2 = os.environ.get("KEY_2", "").strip()
SBURL = os.environ.get("KEY_20", "").strip().rstrip("/")
SBKEY = os.environ.get("KEY_21", "").strip()
PSESS = os.environ.get("KEY_19", "").strip()
AID = os.environ.get("KEY_16", "").strip()
AHASH = os.environ.get("KEY_17", "").strip()
MIDS = [int(x) for x in os.environ.get("MIDS", "").split(",") if x.strip()]
LINK_IDS = [x for x in os.environ.get("LINK_IDS", "").split(",") if x.strip()]

async def main():
    app = Client("delsess", session_string=PSESS, api_id=int(AID) if AID else None,
                 api_hash=AHASH or None, no_updates=True)
    await app.start()
    chat = None
    try:
        chat = await app.get_chat(int(K2))
    except Exception:
        async for d in app.get_dialogs():
            if d.chat and d.chat.id == int(K2):
                chat = d.chat
                break
    if chat is None:
        print("[x] chat fail")
        await app.stop()
        return
    cid = chat.id if hasattr(chat, "id") else chat
    # 1. delete channel mids (chunks of 100)
    if MIDS:
        for i in range(0, len(MIDS), 100):
            chunk = MIDS[i:i+100]
            try:
                await app.delete_messages(cid, chunk)
                print(f"[ok] deleted mids {chunk}")
            except Exception as e:
                print(f"[!] del fail {chunk}: {str(e)[:60]}")
    await app.stop()
    # 2. delete supabase links rows
    for lid in LINK_IDS:
        try:
            req = u.Request(f"{SBURL}/rest/v1/links?id=eq.{u.quote(lid)}", method="DELETE",
                            headers={"apikey": SBKEY, "Authorization": f"Bearer {SBKEY}"})
            with u.urlopen(req, timeout=30) as r:
                print(f"[ok] link row {lid} deleted ({r.status})")
        except Exception as e:
            print(f"[!] link row {lid} fail: {str(e)[:60]}")
    print("[done]")

asyncio.run(main())
