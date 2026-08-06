# stage_setup.py — STAGE CHANNEL setup (ek baar chalao):
# 1) private channel "KTS Stage" banao (user session se)
# 2) saare bots ko admin banao (wahan multibot upload kar sakein)
# 3) stage_ch id Supabase config doc mein save karo
import os, sys, asyncio, json, urllib.request

try:
    import cryptg  # noqa
except Exception:
    os.system(f"{sys.executable} -m pip install -q cryptg")

from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.functions.channels import CreateChannelRequest, EditAdminRequest, InviteToChannelRequest
from telethon.tl.types import ChatAdminRights, InputChannel

AID = int(os.environ.get("KEY_16", "0").strip())
AHASH = os.environ.get("KEY_17", "").strip()
SS = os.environ.get("KEY_18", "").strip()
SBURL = os.environ.get("KEY_20", "").strip().rstrip("/")
SBKEY = os.environ.get("KEY_21", "").strip()
BOT_TOKENS = [os.environ.get(f"KEY_{i}", "").strip() for i in range(22, 28)]
BOT_TOKENS = [t for t in BOT_TOKENS if t]

RIGHTS = ChatAdminRights(
    post_messages=True, edit_messages=True, delete_messages=True,
    invite_users=True, manage_call=True, pin_messages=True,
    add_admins=False, anonymous=False, manage_chat=False,
    change_info=False, ban_users=False, other=False, manage_video_chats=False
)

def sb_save(state):
    body = json.dumps({"id": "config", "state": state}).encode()
    req = urllib.request.Request(f"{SBURL}/rest/v1/progress", data=body, method="POST",
        headers={"apikey": SBKEY, "Authorization": f"Bearer {SBKEY}",
                 "Content-Type": "application/json", "Prefer": "resolution=merge-duplicates"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.status

async def bot_username(tok):
    c = TelegramClient(StringSession(), AID, AHASH)
    await c.connect()
    await c.start(bot_token=tok)
    me = await c.get_me()
    await c.disconnect()
    return me

async def main():
    print(f"[*] creating stage channel...", flush=True)
    c = TelegramClient(StringSession(SS), AID, AHASH)
    await c.connect()
    me = await c.get_me()
    print(f"[*] user: {me.first_name}", flush=True)
    ch = await c(CreateChannelRequest(
        title="KTS Stage", about="KTS multi-repo staging (auto)",
        broadcast=True, megagroup=False))
    chid = ch.chats[0].id if hasattr(ch, "chats") else ch.chats[0].id
    print(f"[ok] stage channel: {chid}", flush=True)
    # bots invite + admin
    for i, tok in enumerate(BOT_TOKENS):
        try:
            bot = await bot_username(tok)
            print(f"[*] promoting {bot.username}...", flush=True)
            await c(InviteToChannelRequest(ch.chats[0], [bot]))
            await c(EditAdminRequest(ch.chats[0], bot, RIGHTS, rank="stage"))
            print(f"  [ok] @{bot.username} admin", flush=True)
        except Exception as e:
            print(f"  [x] bot{i+1} fail: {str(e)[:80]}", flush=True)
    await c.disconnect()
    # config save
    st = sb_save({"stage_ch": str(chid), "at": int(__import__("time").time())})
    print(f"[ok] config saved (stage_ch={chid}) HTTP {st}", flush=True)
    print("[done]", flush=True)

asyncio.run(main())
