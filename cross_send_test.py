# cross_send_test.py — KYA USER SESSION BOT KE UPLOAD HUE PARTS SEND KAR SAKTA HAI?
# Bot session parts upload karega (SaveBigFilePartRequest) -> user session send_file (InputFileBig)
# Agar success -> stage channel ki zaroorat nahi, user directly main channel pe ordered post karega
import os, sys, asyncio, json, urllib.request, time

try:
    import cryptg  # noqa
except Exception:
    os.system(f"{sys.executable} -m pip install -q cryptg")

from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.types import InputFileBig
from telethon.tl.functions.upload import SaveBigFilePartRequest
from telethon import helpers

CHAT = os.environ.get("KEY_2", "").strip()
AID = int(os.environ.get("KEY_16", "0").strip())
AHASH = os.environ.get("KEY_17", "").strip()
SS = os.environ.get("KEY_18", "").strip()
SBURL = os.environ.get("KEY_20", "").strip().rstrip("/")
SBKEY = os.environ.get("KEY_21", "").strip()
MB = 1024 * 1024

def sb_sessions():
    req = urllib.request.Request(f"{SBURL}/rest/v1/progress?select=state&id=eq.bot_sessions&limit=1",
                                 headers={"apikey": SBKEY, "Authorization": f"Bearer {SBKEY}"})
    with urllib.request.urlopen(req, timeout=30) as r:
        d = json.loads(r.read().decode())
    return (d[0].get("state") or {}) if d else {}

async def main():
    st = sb_sessions()
    bot1 = (st.get("bot1") or [])
    if not bot1:
        print("[x] bot1 sessions missing — check bot_sessions doc")
        return
    print(f"[*] bot1 sessions: {len(bot1)}", flush=True)

    # test file 20MB
    path = "/tmp/cross.bin"
    with open(path, "wb") as f:
        f.write(os.urandom(20 * MB))

    # BOT uploads parts
    bot = TelegramClient(StringSession(bot1[0]), AID, AHASH)
    await bot.connect()
    print(f"[*] bot connected dc={bot.session.dc_id}", flush=True)
    fid = helpers.generate_random_long()
    ps = 512 * 1024
    total = (20 * MB + ps - 1) // ps
    data = open(path, "rb").read()
    t0 = time.time()
    for p in range(total):
        await bot(SaveBigFilePartRequest(fid, p, total, data[p * ps:(p + 1) * ps]))
    print(f"[ok] bot uploaded {total} parts in {time.time()-t0:.1f}s", flush=True)
    await bot.disconnect()

    # USER sends the file (same file_id)
    user = TelegramClient(StringSession(SS), AID, AHASH)
    await user.connect()
    ch = await user.get_entity(int(CHAT))
    try:
        m = await user.send_file(ch, InputFileBig(fid, total, "cross.bin"),
                                 force_document=True, caption="cross-send test")
        print(f"[🎉] USER SEND OK — mid={m.id}", flush=True)
        await user.delete_messages(ch, [m])
        print("[RESULT] SUCCESS — user bot ke parts send kar sakta hai!", flush=True)
    except Exception as e:
        print(f"[x] user send fail: {str(e)[:120]}", flush=True)
        print("[RESULT] FAIL — parts bot-account bound hain", flush=True)
    await user.disconnect()
    print("[done]", flush=True)

asyncio.run(main())
