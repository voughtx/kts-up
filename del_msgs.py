#!/usr/bin/env python3
"""del_msgs.py — channel messages 7852..7876 delete (user approved).
Sirf metadata log (id). Kuch aur touch nahi."""
import os, sys, asyncio

try:
    import cryptg  # noqa
except Exception:
    os.system(f"{sys.executable} -m pip install -q cryptg")

from telethon import TelegramClient
from telethon.sessions import StringSession

AID = int(os.environ.get("KEY_16", "0").strip())
AHASH = os.environ.get("KEY_17", "").strip()
CH = int(os.environ.get("KEY_2", "0").strip())

async def main():
    ss = os.environ.get("KEY_18", "").strip()
    if not ss:
        print("no user session", flush=True)
        return
    c = TelegramClient(StringSession(ss), AID, AHASH, connection_retries=2)
    await c.connect()
    ent = await c.get_entity(CH)
    ok=0; fail=0
    # 7852..7876 — delete (poster + text + eps)
    for mid in range(7852, 7877):
        try:
            m = await c.get_messages(ent, ids=mid)
            if m is None:
                print(f"{mid} skip-none", flush=True)
                continue
            await c.delete_messages(ent, [mid])
            print(f"{mid} deleted", flush=True)
            ok+=1
        except Exception as e:
            print(f"{mid} ERR {str(e)[:60]}", flush=True)
            fail+=1
        await asyncio.sleep(0.5)
    print(f"deleted {ok} | fail {fail}", flush=True)
    await c.disconnect()
    print("[done]", flush=True)

asyncio.run(main())
