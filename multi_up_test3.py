# multi_up_test3.py — ROUND 3: same-bot MULTI-SESSION single-file upload
# E) bot1, 4 auth-key sessions, EK 240MB file, parts split 4 sessions (20 conns each) -> total speed?
# F) control: bot1 single session 20 conns 240MB (per-session baseline)
# G) user session 20 conns 120MB DC5 (repeat check)
# H) bot1 4 sessions x 30 conns (connection scaling)
import os, sys, time, asyncio

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
SS = os.environ.get("KEY_18", "").strip()
AID = int(os.environ.get("KEY_16", "0").strip())
AHASH = os.environ.get("KEY_17", "").strip()
BOT1 = os.environ.get("KEY_22", "").strip()
MB = 1024 * 1024
DC2 = ("149.154.167.51", 443)   # best DC from round 2
DC5 = ("91.108.56.130", 443)

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

async def bot_session(dc=None, tag=""):
    c = TelegramClient(StringSession(), AID, AHASH, connection_retries=2)
    if dc:
        c.session.set_dc(dc[0], dc[1], 443)
    await c.connect()
    await c.start(bot_token=BOT1)
    return c

async def split_upload(sessions, path, part_kb=512, conns=None):
    """Parts ko N sessions pe distribute karke upload — same file_id"""
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
    print("[*] E) bot1 4 sessions, EK 240MB file split upload", flush=True)
    make_file("/tmp/te.bin", 240 * MB)
    s4 = [await bot_session(DC2) for _ in range(4)]
    chat = await resolve_chat(s4[0])
    fid, total, dt = await split_upload(s4, "/tmp/te.bin")
    print(f"  [E] 4 sessions: 240MB in {dt:.1f}s = {240/dt:.2f} MB/s", flush=True)
    try:
        m = await s4[0].send_file(chat, InputFileBig(fid, total, "te.bin"), force_document=True,
                                  caption="E 4-session single file")
        print("  [E] SEND OK — 4-session single-file upload WORKED!", flush=True)
        await s4[0].delete_messages(chat, [m])
    except Exception as e:
        print(f"  [E] send fail: {str(e)[:80]}", flush=True)
    for c in s4:
        await c.disconnect()

    print("\n[*] F) control: bot1 1 session 20 conns 240MB", flush=True)
    try:
        c1 = await bot_session(DC2)
        ch = await resolve_chat(c1)
        t0 = time.time()
        with open("/tmp/te.bin", "rb") as f:
            inp = await FastTelethon.upload_file(c1, f, connection_count=20)
        dt = time.time() - t0
        print(f"  [F] 1 session: 240MB in {dt:.1f}s = {240/dt:.2f} MB/s", flush=True)
        try:
            m = await c1.send_file(ch, inp, force_document=True, caption="F control 1sess")
            await c1.delete_messages(ch, [m])
        except Exception as e:
            print(f"  [F] send fail: {str(e)[:60]}")
        await c1.disconnect()
    except Exception as e:
        print(f"  [F] FAIL: {str(e)[:80]}", flush=True)

    print("\n[*] G) user session 20 conns 120MB DC5 (repeat T2)", flush=True)
    try:
        cu = TelegramClient(StringSession(SS), AID, AHASH)
        await cu.connect()
        me = await cu.get_me()
        print(f"  user dc={cu.session.dc_id} {me.first_name}", flush=True)
        ch = await resolve_chat(cu)
        make_file("/tmp/tg.bin", 120 * MB)
        t0 = time.time()
        with open("/tmp/tg.bin", "rb") as f:
            inp = await FastTelethon.upload_file(cu, f, connection_count=20)
        dt = time.time() - t0
        print(f"  [G] user 20conn: 120MB in {dt:.1f}s = {120/dt:.2f} MB/s", flush=True)
        try:
            m = await cu.send_file(ch, inp, force_document=True, caption="G user 20conn")
            await cu.delete_messages(ch, [m])
        except Exception as e:
            print(f"  [G] send fail: {str(e)[:60]}")
        await cu.disconnect()
    except Exception as e:
        print(f"  [G] FAIL: {str(e)[:80]}", flush=True)

    print("\n[*] H) bot1 4 sessions x 30 conns (connection scaling)", flush=True)
    try:
        s4 = [await bot_session(DC2) for _ in range(4)]
        ch = await resolve_chat(s4[0])
        t0 = time.time()
        async def job30(sess):
            with open("/tmp/te.bin", "rb") as f:
                inp = await FastTelethon.upload_file(sess, f, connection_count=30)
            return inp
        inps = await asyncio.gather(*[job30(s) for s in s4])
        dt = time.time() - t0
        print(f"  [H] 4 sessions x 30 conns (4 files): 960MB in {dt:.1f}s = {960/dt:.2f} MB/s total", flush=True)
        for i, inp in enumerate(inps):
            try:
                m = await s4[i].send_file(ch, inp, force_document=True, caption=f"H {i}")
                await s4[i].delete_messages(ch, [m])
            except Exception:
                pass
        for c in s4:
            await c.disconnect()
    except Exception as e:
        print(f"  [H] FAIL: {str(e)[:100]}", flush=True)

    print("\n[done]", flush=True)

asyncio.run(main())
