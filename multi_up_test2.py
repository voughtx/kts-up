# multi_up_test2.py — ROUND 2: DC sweep + same-bot multi-auth-key same-file
# A) bot token se har DC (1-5) pe login → FastTelethon upload 60MB → fastest DC dhoondo
# B) SAME bot token 2x login (2 auth keys) → same file_id parts split → merge hota hai?
# C) user session 1MB parts test
# D) bot best-DC 200MB upload (MTProto bot big file limit check)
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

DCS = {
    1: ("149.154.175.50", 443),
    2: ("149.154.167.51", 443),
    3: ("149.154.175.100", 443),
    4: ("149.154.167.91", 443),
    5: ("91.108.56.130", 443),
}

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

async def main():
    print("[*] A) DC SWEEP — bot1 har DC pe 60MB upload", flush=True)
    dc_speeds = {}
    sent = []
    for dc_id, (ip, port) in DCS.items():
        try:
            c = TelegramClient(StringSession(), AID, AHASH, connection_retries=2)
            c.session.set_dc(dc_id, ip, port)
            await c.connect()
            await c.start(bot_token=BOT1)
            me = await c.get_me()
            chat = await resolve_chat(c)
            if chat is None:
                print(f"  DC{dc_id}: chat fail", flush=True)
                await c.disconnect()
                continue
            path = f"/tmp/dc{dc_id}.bin"
            make_file(path, 60 * MB)
            t0 = time.time()
            with open(path, "rb") as f:
                inp = await FastTelethon.upload_file(c, f)
            dt = time.time() - t0
            spd = 60 / dt
            dc_speeds[dc_id] = spd
            print(f"  DC{dc_id} ({ip}): 60MB in {dt:.1f}s = {spd:.2f} MB/s", flush=True)
            try:
                m = await c.send_file(chat, inp, force_document=True, caption=f"DC{dc_id} test")
                sent.append((c, chat, m))
            except Exception as e:
                print(f"    send fail: {str(e)[:60]}")
            await c.disconnect()
        except Exception as e:
            print(f"  DC{dc_id}: FAIL {str(e)[:80]}", flush=True)
    best_dc = max(dc_speeds, key=dc_speeds.get) if dc_speeds else None
    print(f"  BEST DC: {best_dc} @ {dc_speeds.get(best_dc, 0):.2f} MB/s", flush=True)

    # cleanup A
    for cli, ch, m in sent:
        try:
            await cli.delete_messages(ch, [m])
        except Exception:
            pass

    print("\n[*] B) SAME-BOT 2 AUTH-KEYS same file_id parts", flush=True)
    if best_dc:
        bip, bport = DCS[best_dc]
        c1 = TelegramClient(StringSession(), AID, AHASH)
        c2 = TelegramClient(StringSession(), AID, AHASH)
        c1.session.set_dc(best_dc, bip, bport)
        c2.session.set_dc(best_dc, bip, bport)
        await c1.connect(); await c1.start(bot_token=BOT1)
        await c2.connect(); await c2.start(bot_token=BOT1)
        m1 = await c1.get_me()
        m2 = await c2.get_me()
        print(f"  c1: {m1.username} auth1 | c2: {m2.username} auth2 (different auth keys?)", flush=True)
        make_file("/tmp/tb.bin", 48 * MB)
        fid = helpers.generate_random_long()
        ps = 512 * 1024
        total = (48 * MB + ps - 1) // ps
        data = open("/tmp/tb.bin", "rb").read()
        half = total // 2
        t0 = time.time()
        async def up_parts(c, start, end):
            for p in range(start, end):
                await c(SaveBigFilePartRequest(fid, p, total, data[p * ps:(p + 1) * ps]))
        await asyncio.gather(up_parts(c1, 0, half), up_parts(c2, half, total))
        dt = time.time() - t0
        print(f"  parts uploaded in {dt:.1f}s ({48/dt:.2f} MB/s)", flush=True)
        ch1 = await resolve_chat(c1)
        try:
            m = await c1.send_file(ch1, InputFileBig(fid, total, "tb.bin"), force_document=True,
                                   caption="B same-bot-2auth")
            sent2 = [(c1, ch1, m)]
            print("  [B] SUCCESS — same bot, 2 auth keys parts merge ho gaye!!", flush=True)
        except Exception as e:
            sent2 = []
            print(f"  [B] FAIL: {str(e)[:90]}", flush=True)
        for cli, ch, m in sent2:
            try:
                await cli.delete_messages(ch, [m])
            except Exception:
                pass
        await c1.disconnect(); await c2.disconnect()

    print("\n[*] C) user session — FastTelethon 1MB parts (120MB)", flush=True)
    try:
        cu = TelegramClient(StringSession(SS), AID, AHASH)
        await cu.connect()
        me = await cu.get_me()
        chat = await resolve_chat(cu)
        if chat:
            make_file("/tmp/tc.bin", 120 * MB)
            t0 = time.time()
            with open("/tmp/tc.bin", "rb") as f:
                inp = await FastTelethon.upload_file(cu, f, part_size_kb=1024)
            dt = time.time() - t0
            print(f"  user 1MB parts: 120MB in {dt:.1f}s = {120/dt:.2f} MB/s", flush=True)
            try:
                m = await cu.send_file(chat, inp, force_document=True, caption="C user 1MB parts")
                await cu.delete_messages(chat, [m])
            except Exception as e:
                print(f"    send fail: {str(e)[:60]}")
        await cu.disconnect()
    except Exception as e:
        print(f"  C FAIL: {str(e)[:80]}", flush=True)

    print("\n[*] D) bot best-DC 200MB upload (MTProto bot big-file check)", flush=True)
    if best_dc:
        bip, bport = DCS[best_dc]
        try:
            cd = TelegramClient(StringSession(), AID, AHASH)
            cd.session.set_dc(best_dc, bip, bport)
            await cd.connect()
            await cd.start(bot_token=BOT1)
            chat = await resolve_chat(cd)
            if chat:
                make_file("/tmp/td.bin", 200 * MB)
                t0 = time.time()
                with open("/tmp/td.bin", "rb") as f:
                    inp = await FastTelethon.upload_file(cd, f)
                dt = time.time() - t0
                print(f"  bot 200MB: {dt:.1f}s = {200/dt:.2f} MB/s", flush=True)
                try:
                    m = await cd.send_file(chat, inp, force_document=True, caption="D bot 200MB")
                    print("  [D] send OK — bot 200MB possible", flush=True)
                    await cd.delete_messages(chat, [m])
                except Exception as e:
                    print(f"  [D] send fail: {str(e)[:80]}", flush=True)
            await cd.disconnect()
        except Exception as e:
            print(f"  D FAIL: {str(e)[:80]}", flush=True)

    print("\n[done]", flush=True)

asyncio.run(main())
