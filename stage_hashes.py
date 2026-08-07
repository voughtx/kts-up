# stage_hashes.py — har bot ke liye stage channel ka access_hash nikaalo (forward trick)
# User session stage channel se dummy msg forward karta hai har bot ko →
# bot apne session mein entity cache karta hai → get_entity → access_hash read → config save
import os, sys, asyncio, json, time, urllib.request

try:
    import cryptg  # noqa
except Exception:
    os.system(f"{sys.executable} -m pip install -q cryptg")

from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.functions.messages import ExportChatInviteRequest as _ECI
from telethon.tl.functions.channels import JoinChannelRequest as _JCR

AID = int(os.environ.get("KEY_16", "0").strip())
AHASH = os.environ.get("KEY_17", "").strip()
SS = os.environ.get("KEY_18", "").strip()
SBURL = os.environ.get("KEY_20", "").strip().rstrip("/")
SBKEY = os.environ.get("KEY_21", "").strip()
BOT_TOKENS = [os.environ.get(f"KEY_{i}", "").strip() for i in range(22, 28)]
BOT_TOKENS = [t for t in BOT_TOKENS if t]
STAGE = -1004394456964

def sb_config():
    try:
        url = f"{SBURL}/rest/v1/progress?select=state&id=eq.config&limit=1"
        req = urllib.request.Request(url, headers={"apikey": SBKEY, "Authorization": f"Bearer {SBKEY}"})
        with urllib.request.urlopen(req, timeout=20) as r:
            arr = json.loads(r.read().decode())
        return (arr[0].get("state") or {}) if arr else {}
    except Exception as e:
        print(f"[!] config read fail: {str(e)[:80]}")
        return {}

def sb_save_config(state):
    body = json.dumps({"id": "config", "state": state}).encode()
    req = urllib.request.Request(f"{SBURL}/rest/v1/progress", data=body, method="POST",
        headers={"apikey": SBKEY, "Authorization": f"Bearer {SBKEY}",
                 "Content-Type": "application/json", "Prefer": "resolution=merge-duplicates"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.status

async def main():
    cfg = sb_config()
    hashes = dict(cfg.get("stage_hashes") or {})
    print(f"[*] existing hashes: {hashes}", flush=True)
    user = TelegramClient(StringSession(SS), AID, AHASH)
    await user.connect()
    # stage channel ko user se resolve + dummy message
    stage = await user.get_entity(STAGE)
    print(f"[*] user view: {stage.title} id={stage.id} hash={stage.access_hash}", flush=True)
    # invite link banao (bots join kar sakein -> khud ka access_hash milega)
    inv = await user(_ECI(stage))
    invite = inv.link
    print(f"[*] invite: {invite}", flush=True)
    for i, tok in enumerate(BOT_TOKENS):
        name = f"bot{i+1}"
        if name in hashes:
            print(f"[*] {name} already has hash — skip", flush=True)
            continue
        try:
            bot = TelegramClient(f"hb_{name}", AID, AHASH)
            await bot.start(bot_token=tok)
            me = await bot.get_me()
            # bot invite link se join kare (admin permission already hai)
            try:
                await bot(_JCR(invite))
                await asyncio.sleep(2)
            except Exception as ej:
                print(f"    (join maybe already: {str(ej)[:60]})", flush=True)
            ent = await bot.get_entity(STAGE)
            h = int(ent.access_hash)
            hashes[name] = str(h)
            print(f"[ok] {name} @{me.username}: hash={h}", flush=True)
            await bot.disconnect()
        except Exception as e:
            print(f"[x] {name} fail: {str(e)[:100]}", flush=True)
        # progress save
        cfg["stage_hashes"] = hashes
        sb_save_config(cfg)
    await user.disconnect()
    cfg["stage_hashes"] = hashes
    st = sb_save_config(cfg)
    print(f"[*] saved hashes: {hashes} HTTP {st}", flush=True)
    print("[done]", flush=True)

asyncio.run(main())
