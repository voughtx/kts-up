# stage_hashes.py — har bot ke liye stage channel ka access_hash (re-promote trick)
# Bot client ONLINE hai, user usi waqt bot ko channel admin re-promote karta hai →
# bot ko updateChatParticipantAdmin update milta hai → channel entity (id+access_hash)
# cache ho jata hai → get_entity kaam karta hai → hash save config mein
import os, sys, asyncio, json, time, urllib.request

try:
    import cryptg  # noqa
except Exception:
    os.system(f"{sys.executable} -m pip install -q cryptg")

from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.functions.channels import EditAdminRequest as _EAR
from telethon.tl.types import ChatAdminRights as _CAR

AID = int(os.environ.get("KEY_16", "0").strip())
AHASH = os.environ.get("KEY_17", "").strip()
SS = os.environ.get("KEY_18", "").strip()
SBURL = os.environ.get("KEY_20", "").strip().rstrip("/")
SBKEY = os.environ.get("KEY_21", "").strip()
BOT_TOKENS = [os.environ.get(f"KEY_{i}", "").strip() for i in range(22, 28)]
BOT_TOKENS = [t for t in BOT_TOKENS if t]
STAGE = -1004394456964
RIGHTS = _CAR(post_messages=True, edit_messages=True, delete_messages=True,
              invite_users=True, pin_messages=True, add_admins=False, anonymous=False,
              change_info=False, ban_users=False)

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
    stage = await user.get_entity(STAGE)
    print(f"[*] user view: {stage.title} id={stage.id} hash={stage.access_hash}", flush=True)
    for i, tok in enumerate(BOT_TOKENS):
        name = f"bot{i+1}"
        if name in hashes:
            print(f"[*] {name} already has hash — skip", flush=True)
            continue
        try:
            bot = TelegramClient(f"hb_{name}", AID, AHASH)
            await bot.start(bot_token=tok)
            me = await bot.get_me()
            # RE-PROMOTE while bot ONLINE -> bot ko update milega
            try:
                await user(_EAR(stage, me, RIGHTS, rank="stage"))
                await asyncio.sleep(4)
            except Exception as ep:
                print(f"    (promote note: {str(ep)[:70]})", flush=True)
            ent = await bot.get_entity(STAGE)
            h = int(ent.access_hash)
            hashes[name] = str(h)
            print(f"[ok] {name} @{me.username}: hash={h}", flush=True)
            await bot.disconnect()
        except Exception as e:
            print(f"[x] {name} fail: {str(e)[:90]}", flush=True)
        cfg["stage_hashes"] = hashes
        sb_save_config(cfg)
    await user.disconnect()
    cfg["stage_hashes"] = hashes
    st = sb_save_config(cfg)
    print(f"[*] saved hashes: {hashes} HTTP {st}", flush=True)
    print("[done]", flush=True)

asyncio.run(main())
