# check_telethon.py — Telethon session (KEY_18) valid hai? get_me + dc_id
import os, asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession

SS = os.environ.get("KEY_18", "").strip()
AID = os.environ.get("KEY_16", "").strip()
AHASH = os.environ.get("KEY_17", "").strip()

async def main():
    if not SS:
        print("[x] KEY_18 missing")
        return
    client = TelegramClient(StringSession(SS), int(AID), AHASH)
    try:
        await client.connect()
        me = await client.get_me()
        print(f"[ok] connected: {me.first_name} (id={me.id}, dc={client.session.dc_id})")
    except Exception as e:
        print(f"[x] FAIL: {str(e)[:150]}")
    finally:
        try:
            await client.disconnect()
        except Exception:
            pass

asyncio.run(main())
