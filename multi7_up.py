# multi7_up.py — MULTI-BOT UPLOAD TEST: user + 6 bots, har session 10MB file upload kare
# Compare: single session upload vs 7 sessions parallel
import os, time, asyncio
from pyrogram import Client

K2 = os.environ.get("KEY_2", "").strip()
PSESS = os.environ.get("KEY_19", "").strip()
AID = os.environ.get("KEY_16", "").strip()
AHASH = os.environ.get("KEY_17", "").strip()
BOT_TOKENS = [os.environ.get(f"KEY_{i}", "").strip() for i in range(22, 28)]
BOT_TOKENS = [t for t in BOT_TOKENS if t]
SRC_MID = int(os.environ.get("MIDS", "441").split(",")[0])
MB = 1024 * 1024
FILESZ = 10 * MB  # 10MB per file
WORKERS = 3

def make_file(path, size):
    with open(path, "wb") as f:
        f.write(os.urandom(size))

async def upload_one(app, cid, path, name, progress=None):
    t0 = time.time()
    await app.send_document(cid, path, file_name=name, disable_notification=True, progress=progress)
    dt = time.time() - t0
    return dt

async def main():
    print(f"[*] sessions: user + {len(BOT_TOKENS)} bots | file: {FILESZ/MB:.0f}MB each")
    user = Client("u1", api_id=int(AID), api_hash=AHASH, session_string=PSESS, no_updates=True)
    await user.start()
    try:
        uchat = await user.get_chat(int(K2))
    except Exception:
        uchat = None
        async for d in user.get_dialogs():
            if d.chat and d.chat.id == int(K2):
                uchat = d.chat
                break
    if uchat is None:
        print("[!] user chat fail")
        await user.stop()
        return
    ucid = uchat.id if hasattr(uchat, "id") else uchat

    # test files
    make_file("/tmp/up_ctl.bin", FILESZ)
    for i in range(len(BOT_TOKENS)):
        make_file(f"/tmp/up_{i}.bin", FILESZ)

    # CONTROL: user single upload
    t0 = time.time()
    await upload_one(user, ucid, "/tmp/up_ctl.bin", "ctl_test.bin")
    dt = time.time() - t0
    print(f"[CONTROL user] {FILESZ/MB:.0f} MB in {dt:.1f}s = {FILESZ/dt/MB:.2f} MB/s")

    # bots start (updates ON) + peer register
    bots = []
    for i, tok in enumerate(BOT_TOKENS):
        b = Client(f"b{i+1}", api_id=int(AID), api_hash=AHASH, bot_token=tok)
        await b.start()
        me = await b.get_me()
        try:
            await user.forward_messages(me.username or f"b{i+1}", ucid, [SRC_MID])
        except Exception:
            pass
        bots.append(b)
    await asyncio.sleep(6)

    # MULTI: 7 sessions, har ek apni file upload (parallel)
    sessions = [user] + bots
    t0 = time.time()

    async def job(idx):
        app = sessions[idx]
        try:
            ch = await app.get_chat(int(K2))
        except Exception as e:
            print(f"   [s{idx}] get_chat fail: {str(e)[:40]}")
            return None
        cid = ch.id if hasattr(ch, "id") else ch
        path = f"/tmp/up_{idx}.bin"
        name = f"up_{idx}.bin"
        try:
            dt = await upload_one(app, cid, path, name)
            return dt
        except Exception as e:
            print(f"   [s{idx}] upload fail: {str(e)[:60]}")
            return None

    results = await asyncio.gather(*[job(i) for i in range(len(sessions))])
    dt = time.time() - t0
    ok = [r for r in results if r]
    print(f"[*] per-session: {[f'{r:.1f}s' if r else 'FAIL' for r in results]}")
    n_ok = len(ok)
    total_mb = n_ok * FILESZ / MB
    print(f"[MULTI-{n_ok}] {total_mb:.0f} MB in {dt:.1f}s = {total_mb/dt:.2f} MB/s total")
    if ok:
        print(f"[AVG per-session] {FILESZ/MB/sum(ok)*len(ok):.2f} MB/s")

    await user.stop()
    for b in bots:
        await b.stop()
    print("[done]")

asyncio.run(main())
