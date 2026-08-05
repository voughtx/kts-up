# bot_session_maker.py — har bot ka session string banao (ek baar)
# Session string reuse karne se ImportBotAuthorization flood nahi aata
import os, asyncio
from pyrogram import Client

AID = os.environ.get("KEY_16", "").strip()
AHASH = os.environ.get("KEY_17", "").strip()
BOT_TOKENS = [os.environ.get(f"KEY_{i}", "").strip() for i in range(22, 28)]
BOT_TOKENS = [t for t in BOT_TOKENS if t]

async def main():
    out = []
    for i, t in enumerate(BOT_TOKENS):
        name = f"botsess{i+1}"
        try:
            c = Client(name, api_id=int(AID), api_hash=AHASH, bot_token=t, no_updates=True,
                       workdir="/tmp")
            await c.start()
            ss = await c.export_session_string()
            me = await c.get_me()
            print(f"bot{i+1} @{me.username}: {ss}")
            out.append(ss)
            await c.stop()
        except Exception as e:
            print(f"bot{i+1} fail: {str(e)[:80]}")
            out.append("")
    # save for reference
    with open("/tmp/bot_sessions.txt", "w") as f:
        for i, s in enumerate(out):
            f.write(f"KEY_{22+i}={s}\n")
    print("[done] sessions saved to /tmp/bot_sessions.txt")

asyncio.run(main())
