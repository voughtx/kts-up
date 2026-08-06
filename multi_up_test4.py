# multi_up_test4.py — ROUND 4: pipelined multi-session upload (upload_file_multi)
# E2) 2 sessions (bot2) x 10 conns each, EK 240MB -> speed?
# E3) 2 sessions (bot2) x 15 conns each -> speed?
# E4) 3 sessions (bot2+bot3 sessions?) — same bot chahiye; agar ek bot ke 3+ hon to
import os, sys, time, json, asyncio, urllib.request

try:
    import cryptg  # noqa
except Exception:
    print("[*] installing cryptg...", flush=True)
    os.system(f"{sys.executable} -m pip install -q cryptg")
    import cryptg  # noqa

from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.types import DocumentAttributeFilename
import FastTelethon

CHAT = os.environ.get("KEY_2", "").strip()
AID = int(os.environ.get("KEY_16", "0").strip())
AHASH = os.environ.get("KEY_17", "").strip()
SBURL = os.environ.get("KEY_20", "").strip()
SBKEY = os.environ.get("KEY_21", "").strip()
MB = 1024 * 1024

def sb_sessions():
    req = urllib.request.Request(f"{SBURL}/rest/v1/progress?select=state&id=eq.bot_sessions&limit=1",
                                 headers={"apikey": SBKEY, "Authorization": f"Bearer {SBKEY}"})
    with urllib.request.urlopen(req, timeout=30) as r:
        d = json.loads(r.read().decode())
    return (d[0].get("state") or {}) if d else {}

def make_file(path, size):
    with open(path, "wb") as f:
        f.write(os.urandom(size))

async def resolve_chat(client):
    try:
        return await client.get_entity(int(CHAT))
    except Exception:
        async for d in client.iter_dialogs():
            if d.id == int(CHAT):
                return d.entity
    return None

async def run_test(label, clients, path, conns, name):
    ch = await resolve_chat(clients[0])
    t0 = time.time()
    with open(path, "rb") as f:
        inp = await FastTelethon.upload_file_multi(clients, f, conns_per_client=conns)
    dt = time.time() - t0
    fsz = os.path.getsize(path)
    print(f"  [{label}] {len(clients)} sess x {conns} conns: {fsz/MB:.0f}MB in {dt:.1f}s = {fsz/dt/MB:.2f} MB/s", flush=True)
    try:
        from telethon import utils as tlu
        m = await clients[0].send_file(ch, tlu.get_input_media(inp, force_document=True,
                                       attributes=[DocumentAttributeFilename(file_name=name)]),
                                       force_document=True, caption=f"{label} test")
        print(f"  [{label}] SEND OK", flush=True)
        await clients[0].delete_messages(ch, [m])
    except Exception as e:
        print(f"  [{label}] send fail: {str(e)[:80]}", flush=True)

async def main():
    st = sb_sessions()
    print(f"[*] stored: {sum(len(v) for v in st.values() if isinstance(v, list))} sessions", flush=True)
    for k, v in st.items():
        print(f"  {k}: {len(v) if isinstance(v, list) else '?'}", flush=True)

    make_file("/tmp/t4.bin", 240 * MB)

    # E2: 2 sessions x 10 conns (bot with >=2)
    bot = None
    for k, v in st.items():
        if isinstance(v, list) and len(v) >= 2:
            bot = (k, v[:2])
            break
    if bot:
        print(f"\n[*] E2: {bot[0]} 2 sessions x 10 conns", flush=True)
        clients = []
        for i, ss in enumerate(bot[1]):
            c = TelegramClient(StringSession(ss), AID, AHASH)
            await c.connect()
            print(f"  sess{i+1} dc={c.session.dc_id}", flush=True)
            clients.append(c)
        await run_test("E2", clients, "/tmp/t4.bin", 10, "t4.bin")
        for c in clients:
            await c.disconnect()

        print(f"\n[*] E3: {bot[0]} 2 sessions x 15 conns", flush=True)
        clients = []
        for i, ss in enumerate(bot[1]):
            c = TelegramClient(StringSession(ss), AID, AHASH)
            await c.connect()
            print(f"  sess{i+1} dc={c.session.dc_id}", flush=True)
            clients.append(c)
        await run_test("E3", clients, "/tmp/t4.bin", 15, "t4.bin")
        for c in clients:
            await c.disconnect()
    else:
        print("[*] no bot with 2 sessions — E2/E3 skip", flush=True)

    # E4: 3-4 sessions of same bot (agar ho)
    bot4 = None
    for k, v in st.items():
        if isinstance(v, list) and len(v) >= 4:
            bot4 = (k, v[:4])
            break
    if bot4:
        print(f"\n[*] E4: {bot4[0]} 4 sessions x 10 conns", flush=True)
        clients = []
        for ss in bot4[1]:
            c = TelegramClient(StringSession(ss), AID, AHASH)
            await c.connect()
            clients.append(c)
        await run_test("E4", clients, "/tmp/t4.bin", 10, "t4.bin")
        for c in clients:
            await c.disconnect()
    else:
        print("[*] no bot with 4 sessions — E4 skip (factory round 2 ke baad)", flush=True)

    print("\n[done]", flush=True)

asyncio.run(main())
