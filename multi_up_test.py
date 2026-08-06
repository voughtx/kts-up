# multi_up_test.py — FULL UPLOAD SPEED SUITE (GitHub runner, real secrets)
# Tests:
#  1) baseline: normal telethon upload (user session)
#  2) FastTelethon upload (user session + cryptg) — default conns
#  3) FastTelethon + MORE connections (patched, 40 conns)
#  4) 6 bots parallel FastTelethon (own files) — multi-bot per-file throughput
#  5) CROSS-BOT same file_id part sharing (TRUE multi-bot single file) — works?
# Cleanup: test messages channel se delete
import os, sys, time, asyncio, random

# ensure cryptg (runner deps mein nahi hai)
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
SS = os.environ.get("KEY_18", "").strip()      # telethon user session
AID = int(os.environ.get("KEY_16", "0").strip())
AHASH = os.environ.get("KEY_17", "").strip()
BOT_TOKENS = [os.environ.get(f"KEY_{i}", "").strip() for i in range(22, 28)]
BOT_TOKENS = [t for t in BOT_TOKENS if t]
MB = 1024 * 1024
RESULTS = []

def make_file(path, size):
    with open(path, "wb") as f:
        f.write(os.urandom(size))

def report(name, size, dt):
    spd = size / dt / MB
    RESULTS.append((name, size / MB, dt, spd))
    print(f"[{name}] {size/MB:.0f} MB in {dt:.1f}s = {spd:.2f} MB/s", flush=True)
    return spd

async def resolve_chat(client):
    try:
        return await client.get_entity(int(CHAT))
    except Exception:
        async for d in client.iter_dialogs():
            if d.id == int(CHAT):
                return d.entity
    return None

async def main():
    print(f"[*] cryptg: ", end="")
    try:
        import cryptg
        print(f"OK ({cryptg.__file__.split('/')[-1]})")
    except Exception as e:
        print(f"MISSING ({str(e)[:60]})")

    sent_msgs = []  # (client, chat, msg) cleanup ke liye

    # ============ USER SESSION SETUP ============
    print("\n=== USER SESSION ===")
    cu = TelegramClient(StringSession(SS), AID, AHASH)
    await cu.connect()
    me = await cu.get_me()
    print(f"[*] user: {me.first_name} | dc={cu.session.dc_id}")
    chat = await resolve_chat(cu)
    if chat is None:
        print("[x] chat resolve fail — abort")
        return
    print(f"[*] chat: {getattr(chat, 'title', chat)}")

    # ---- TEST 1: baseline normal upload 32MB ----
    print("\n--- TEST 1: normal telethon upload (32MB) ---")
    make_file("/tmp/t1.bin", 32 * MB)
    t0 = time.time()
    with open("/tmp/t1.bin", "rb") as f:
        inp = await cu.upload_file(f, file_name="t1.bin")
    dt = time.time() - t0
    report("T1-normal", 32 * MB, dt)
    try:
        m = await cu.send_file(chat, inp, force_document=True, caption="T1 normal baseline")
        sent_msgs.append((cu, chat, m))
    except Exception as e:
        print(f"[!] send: {str(e)[:80]}")

    # ---- TEST 2: FastTelethon default (20 conns) 120MB ----
    print("\n--- TEST 2: FastTelethon default conns (120MB) ---")
    make_file("/tmp/t2.bin", 120 * MB)
    t0 = time.time()
    with open("/tmp/t2.bin", "rb") as f:
        inp = await FastTelethon.upload_file(cu, f)
    dt = time.time() - t0
    report("T2-fast-default", 120 * MB, dt)
    try:
        m = await cu.send_file(chat, inp, force_document=True, caption="T2 fast default")
        sent_msgs.append((cu, chat, m))
    except Exception as e:
        print(f"[!] send: {str(e)[:80]}")

    # ---- TEST 3: FastTelethon 40 conns (patched) 120MB ----
    print("\n--- TEST 3: FastTelethon 40 conns (120MB) ---")
    make_file("/tmp/t3.bin", 120 * MB)
    t0 = time.time()
    with open("/tmp/t3.bin", "rb") as f:
        inp = await FastTelethon.upload_file(cu, f, connection_count=40)
    dt = time.time() - t0
    report("T3-fast-40", 120 * MB, dt)
    try:
        m = await cu.send_file(chat, inp, force_document=True, caption="T3 fast 40conn")
        sent_msgs.append((cu, chat, m))
    except Exception as e:
        print(f"[!] send: {str(e)[:80]}")

    # ---- TEST 4: 6 bots parallel FastTelethon own files ----
    print(f"\n--- TEST 4: {len(BOT_TOKENS)} bots parallel FastTelethon (30MB each) ---")
    bots = []
    for i, tok in enumerate(BOT_TOKENS):
        b = TelegramClient(f"bot{i}", AID, AHASH)
        try:
            await b.start(bot_token=tok)
        except Exception as e:
            print(f"[!] bot{i} start fail: {str(e)[:60]}")
            continue
        bots.append(b)
    print(f"[*] bots ready: {len(bots)}")
    bchats = {}
    for i, b in enumerate(bots):
        try:
            bchats[i] = await b.get_entity(int(CHAT))
        except Exception:
            bchats[i] = None
        # register peer via user (forward dummy) — admin rights
        try:
            meb = await b.get_me()
            await cu.send_message(meb.username or f"bot{i}", "hi")
        except Exception:
            pass
    await asyncio.sleep(3)
    per = 30 * MB
    for i in range(len(bots)):
        make_file(f"/tmp/t4_{i}.bin", per)
    t0 = time.time()
    async def job4(i):
        if bchats[i] is None:
            return "nochat"
        with open(f"/tmp/t4_{i}.bin", "rb") as f:
            inp = await FastTelethon.upload_file(bots[i], f)
        try:
            m = await bots[i].send_file(bchats[i], inp, force_document=True, caption=f"T4 bot{i}")
            sent_msgs.append((bots[i], bchats[i], m))
            return time.time() - t0
        except Exception as e:
            return f"fail:{str(e)[:40]}"
    res4 = await asyncio.gather(*[job4(i) for i in range(len(bots))])
    dt4 = time.time() - t0
    ok4 = [r for r in res4 if isinstance(r, float)]
    n4 = len(ok4)
    tot4 = n4 * per
    print(f"[*] per-bot: {[f'{r:.1f}s' if isinstance(r,float) else r for r in res4]}")
    if n4:
        report(f"T4-multi{len(bots)}", tot4, dt4)
        print(f"   (avg/session {per/MB/sum(ok4)*n4:.2f} MB/s)", flush=True)

    # ---- TEST 5: CROSS-BOT same file_id (TRUE multi-bot single file) ----
    print("\n--- TEST 5: cross-bot same file_id parts (2 bots) ---")
    if len(bots) >= 2:
        make_file("/tmp/t5.bin", 48 * MB)
        fid = helpers.generate_random_long()
        ps = 512 * 1024
        total = (48 * MB + ps - 1) // ps
        data = open("/tmp/t5.bin", "rb").read()
        t0 = time.time()
        async def up_parts(bot, start, end):
            for p in range(start, end):
                chunk = data[p * ps:(p + 1) * ps]
                await bot(SaveBigFilePartRequest(fid, p, total, chunk))
        half = total // 2
        await asyncio.gather(
            up_parts(bots[0], 0, half),
            up_parts(bots[1], half, total),
        )
        dt5 = time.time() - t0
        report("T5-crossbot-upload", 48 * MB, dt5)
        try:
            m = await bots[0].send_file(bchats[0], InputFileBig(fid, total, "t5.bin"),
                                        force_document=True, caption="T5 crossbot same file")
            sent_msgs.append((bots[0], bchats[0], m))
            print("[T5] SUCCESS — cross-bot parts merge ho gaye!", flush=True)
        except Exception as e:
            print(f"[T5] FAIL (expected agar parts auth-key-bound): {str(e)[:100]}", flush=True)

    # ============ SUMMARY ============
    print("\n===== SUMMARY =====")
    for name, sz, dt, spd in RESULTS:
        print(f"  {name:20s} {sz:6.0f} MB  {dt:7.1f}s  {spd:6.2f} MB/s")
    if RESULTS:
        best = max(RESULTS, key=lambda r: r[3])
        print(f"  BEST: {best[0]} @ {best[3]:.2f} MB/s")

    # ============ CLEANUP: test messages delete ============
    print("\n--- cleanup: deleting test messages ---")
    for cli, ch, m in sent_msgs:
        try:
            await cli.delete_messages(ch, [m])
        except Exception as e:
            print(f"[!] del fail: {str(e)[:60]}")
    print("[cleanup done]")

    await cu.disconnect()
    for b in bots:
        try:
            await b.disconnect()
        except Exception:
            pass
    print("[done]")

asyncio.run(main())
