# pub_setup.py — temp public channel banao (random username) + print info
import os, asyncio, random, string
from pyrogram import Client

K2 = os.environ.get("KEY_2", "").strip()
PSESS = os.environ.get("KEY_19", "").strip()
AID = os.environ.get("KEY_16", "").strip()
AHASH = os.environ.get("KEY_17", "").strip()

def gen_user():
    r = random.SystemRandom()
    a = ''.join(r.choices(string.ascii_lowercase, k=5))
    b = ''.join(r.choices(string.ascii_lowercase + string.digits, k=3))
    return f"{a}{b}"

async def main():
    app = Client("pubsess", session_string=PSESS, api_id=int(AID) if AID else None,
                 api_hash=AHASH or None, no_updates=True)
    await app.start()
    me = await app.get_me()
    print(f"[*] as {me.first_name}")
    # channel banao
    chat = await app.create_channel("K", about="temporary file pool")
    print(f"[ok] channel created: {chat.id}")
    # username try
    for _ in range(10):
        un = gen_user()
        try:
            await app.set_chat_username(chat.id, un)
            print(f"[ok] username set: {un}")
            print(f"[ok] PUBLIC CHANNEL: t.me/{un}")
            await app.stop()
            return
        except Exception as e:
            print(f"[!] {un} taken/fail: {str(e)[:50]}")
    print("[x] no username — channel private raha")
    await app.stop()

asyncio.run(main())
