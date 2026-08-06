# multi_up_test3b.py — ROUND 3b: STORED sessions se multi-session single-file upload
# E) 4 stored sessions (ek bot) EK 240MB file split -> speed?
# F) control: 1 stored session 20 conns 240MB
# G) USER account 2 sessions (KEY_18 + KEY_19) same-file split!
# H) 3 bots x 1 session x 3 files parallel (batch)
import os, sys, time, json, asyncio, urllib.request

try:
    import cryptg  # noqa
except Exception:
    print("[*] installing cryptg...", flush=True)
    os.system(f"{sys.executable} -m pip install -q cryptg")
    import cryptg  # noqa

from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.types import InputFileBig
from telethon.tl.functions.upload import SaveBigFilePartRequest
from telethon import helpers
import FastTelethon

CHAT = os.environ.get("KEY_2", "").strip()
SS18 = os.environ.get("KEY_18", "").strip()
SS19 = os.environ.get("KEY_19", "").strip()
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

async def split_upload(sessions, path, part_kb=512):
    fid = helpers.generate_random_long()
    fsz = os.path.getsize(path)
    ps = part_kb * 1024
    total = (fsz + ps - 1) // ps
    data = open(path, "rb").read()
    n = len(sessions)
    bounds = [(total * i // n, total * (i + 1) // n) for i in range(n)]
    t0 = time.time()
    async def job(sess, start, end):
        for p in range(start, end):
            await sess(SaveBigFilePartRequest(fid, p, total, data[p * ps:(p + 1) * ps]))
    await asyncio.gather(*[job(s, a, b) for s, (a, b) in zip(sessions, bounds)])
    dt = time.time() - t0
    return fid, total, dt

async def main():
    st = sb_sessions()
    print(f"[*] stored sessions: {sum(len(v) for v in st.values() if isinstance(v, list))}", flush=True)
    for k, v in st.items():
        print(f"  {k}: {len(v) if isinstance(v, list) else '?'} sessions", flush=True)

    # ===== E) 4 sessions same bot, one 240MB file =====
    print("\n[*] E) 4 stored sessions (1 bot), EK 240MB file split", flush=True)
    bot_sess = None
    for k, v in st.items():
        if isinstance(v, list) and len(v) >= 2:
            bot_sess = v[:4]
            print(f"  using {k} sessions ({len(bot_sess)})", flush=True)
            break
    if bot_sess:
        make_file("/tmp/te.bin", 240 * MB)
        clients = []
        for ss in bot_sess:
            c = TelegramClient(StringSession(ss), AID, AHASH)
            await c.connect()
            clients.append(c)
        chat = await resolve_chat(clients[0])
        fid, total, dt = await split_upload(clients, "/tmp/te.bin")
        print(f"  [E] 4 sessions: 240MB in {dt:.1f}s = {240/dt:.2f} MB/s", flush=True)
        try:
            m = await clients[0].send_file(chat, InputFileBig(fid, total, "te.bin"),
                                           force_document=True, caption="E 4sess onefile")
            print("  [E] SEND OK!", flush=True)
            await clients[0].delete_messages(chat, [m])
        except Exception as e:
            print(f"  [E] send fail: {str(e)[:80]}", flush=True)
        for c in clients:
            await c.disconnect()
    else:
        print("  [E] skip — kisi bot ke paas 4 sessions nahi", flush=True)

    # ===== F) control: 1 session 20 conns 240MB =====
    print("\n[*] F) control: 1 session, FastTelethon 20 conns, 240MB", flush=True)
    one = None
    for k, v in st.items():
        if isinstance(v, list) and v:
            one = (k, v[0])
            break
    if one:
        try:
            c = TelegramClient(StringSession(one[1]), AID, AHASH)
            await c.connect()
            ch = await resolve_chat(c)
            t0 = time.time()
            with open("/tmp/te.bin", "rb") as f:
                inp = await FastTelethon.upload_file(c, f, connection_count=20)
            dt = time.time() - t0
            print(f"  [F] 1 sess ({one[0]}): 240MB in {dt:.1f}s = {240/dt:.2f} MB/s", flush=True)
            try:
                m = await c.send_file(ch, inp, force_document=True, caption="F control")
                await c.delete_messages(ch, [m])
            except Exception as e:
                print(f"  [F] send fail: {str(e)[:60]}")
            await c.disconnect()
        except Exception as e:
            print(f"  [F] FAIL: {str(e)[:80]}", flush=True)

    # ===== G) USER 2 sessions (KEY_18 + KEY_19) same file =====
    print("\n[*] G) USER account: KEY_18 + KEY_19 same-file split (240MB)", flush=True)
    try:
        c1 = TelegramClient(StringSession(SS18), AID, AHASH)
        c2 = TelegramClient(StringSession(SS19), AID, AHASH)
        await c1.connect(); await c2.connect()
        me1 = await c1.get_me(); me2 = await c2.get_me()
        print(f"  user sessions: {me1.first_name} dc={c1.session.dc_id} + {me2.first_name} dc={c2.session.dc_id}", flush=True)
        ch = await resolve_chat(c1)
        fid, total, dt = await split_upload([c1, c2], "/tmp/te.bin")
        print(f"  [G] user 2 sessions: 240MB in {dt:.1f}s = {240/dt:.2f} MB/s", flush=True)
        try:
            m = await c1.send_file(ch, InputFileBig(fid, total, "te.bin"), force_document=True,
                                   caption="G user 2sess")
            print("  [G] SEND OK — user 2 sessions merge!", flush=True)
            await c1.delete_messages(ch, [m])
        except Exception as e:
            print(f"  [G] send fail: {str(e)[:80]}", flush=True)
        await c1.disconnect(); await c2.disconnect()
    except Exception as e:
        print(f"  [G] FAIL: {str(e)[:80]}", flush=True)

    # ===== H) batch: 3 bots x 3 files parallel =====
    print("\n[*] H) batch: 3 sessions (alag bots) x 3 files parallel (90MB each)", flush=True)
    picks = []
    for k, v in st.items():
        if isinstance(v, list) and v:
            picks.append((k, v[0]))
        if len(picks) >= 3:
            break
    if len(picks) >= 2:
        try:
            files = []
            for i in range(len(picks)):
                make_file(f"/tmp/th{i}.bin", 90 * MB)
                files.append(f"/tmp/th{i}.bin")
            clients = []
            for k, ss in picks:
                c = TelegramClient(StringSession(ss), AID, AHASH)
                await c.connect()
                clients.append(c)
            ch = await resolve_chat(clients[0])
            t0 = time.time()
            async def job(i):
                with open(files[i], "rb") as f:
                    return await FastTelethon.upload_file(clients[i], f, connection_count=20)
            inps = await asyncio.gather(*[job(i) for i in range(len(clients))])
            dt = time.time() - t0
            tot = 90 * len(clients)
            print(f"  [H] {len(clients)} files parallel: {tot}MB in {dt:.1f}s = {tot/dt:.2f} MB/s total", flush=True)
            for i, inp in enumerate(inps):
                try:
                    m = await clients[i].send_file(ch, inp, force_document=True, caption=f"H {picks[i][0]}")
                    await clients[i].delete_messages(ch, [m])
                except Exception:
                    pass
            for c in clients:
                await c.disconnect()
        except Exception as e:
            print(f"  [H] FAIL: {str(e)[:100]}", flush=True)

    print("\n[done]", flush=True)

asyncio.run(main())
