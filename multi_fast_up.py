# multi_fast_up.py — MULTI-BOT + FastTelethon upload (user + bot1 + bot2 parallel)
import os, time, asyncio, random
from telethon import TelegramClient
from telethon.sessions import StringSession
from FastTelethon import upload_file

K2 = os.environ.get("KEY_2", "").strip()
TSESS = os.environ.get("KEY_18", "").strip()
AID = os.environ.get("KEY_16", "").strip()
AHASH = os.environ.get("KEY_17", "").strip()
BOT1 = os.environ.get("KEY_22", "").strip()
BOT2 = os.environ.get("KEY_23", "").strip()
MB = 1024 * 1024
FSZ = 67 * MB  # har session 67MB (episode jaisa)

def make_file(path, size):
    with open(path, "wb") as f:
        f.write(os.urandom(size))

async def resolve_chat(client):
    try:
        return await client.get_entity(int(K2))
    except Exception:
        async for d in client.iter_dialogs():
            if d.id == int(K2):
                return d.entity
    return None

async def main():
    # files
    for i in range(3):
        make_file(f"/tmp/mf_{i}.bin", FSZ)

    # clients: user + 2 bots
    clients = []
    cu = TelegramClient(StringSession(TSESS), int(AID), AHASH)
    await cu.connect()
    clients.append(("user", cu))
    for name, tok in (("bot1", BOT1), ("bot2", BOT2)):
        cb = TelegramClient(name, int(AID), AHASH)
        await cb.start(bot_token=tok)
        clients.append((name, cb))

    # chat resolve har client ke liye
    chats = {}
    for name, c in clients:
        ch = await resolve_chat(c)
        chats[name] = ch
        print(f"[*] {name} chat: {ch.title if ch else 'FAIL'}")

    # PARALLEL: sab apni file FastTelethon se upload
    t0 = time.time()

    async def job(idx, name, c):
        if chats[name] is None:
            return None
        with open(f"/tmp/mf_{idx}.bin", "rb") as f:
            ff = await upload_file(c, f)
        await c.send_file(chats[name], ff, caption=f"test {name} fast")
        return time.time() - t0

    results = await asyncio.gather(*[job(i, n, c) for i, (n, c) in enumerate(clients)])
    dt = time.time() - t0
    ok = [r for r in results if r is not None]
    total_mb = len(ok) * FSZ / MB
    print(f"[*] per-session: {[f'{r:.1f}s' if r else 'FAIL' for r in results]}")
    print(f"[MULTI-FAST {len(ok)}] {total_mb:.0f} MB in {dt:.1f}s = {total_mb/dt:.2f} MB/s total")
    if ok:
        print(f"[AVG/session] {FSZ/MB/sum(ok)*len(ok):.2f} MB/s")

    for _, c in clients:
        await c.disconnect()
    print("[done]")

asyncio.run(main())
