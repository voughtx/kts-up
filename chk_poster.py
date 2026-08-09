#!/usr/bin/env python3
import os, sys, json, asyncio, urllib.request as q
def log(*a): print("[chk]", *a, flush=True)
KID=os.environ.get("KEY_16",""); KHASH=os.environ.get("KEY_17","")
SBURL=os.environ.get("KEY_20","").rstrip("/"); SBKEY=os.environ.get("KEY_21","")
CHAT=os.environ.get("KEY_2","")
def sb_get(path):
    req=q.Request(SBURL+path, headers={"apikey":SBKEY,"Authorization":"Bearer "+SBKEY})
    with q.urlopen(req,timeout=30) as r: return json.loads(r.read().decode())
async def main():
    st=(sb_get("/rest/v1/progress?select=state&id=eq.bot_sessions&limit=1") or [{}])[0].get("state") or {}
    bots={k:v for k,v in st.items() if isinstance(v,list) and len(v)>=1}
    from telethon import TelegramClient
    from telethon.sessions import StringSession
    bname="bot1" if "bot1" in bots else sorted(bots.keys())[0]
    cli=TelegramClient(StringSession(bots[bname][0]), int(KID), KHASH, connection_retries=2, request_retries=2)
    await cli.connect()
    try:
        ch=int(CHAT) if str(CHAT).lstrip("-").isdigit() else CHAT
        msgs=await cli.get_messages(ch, ids=[2031])
        for m in msgs:
            if m is None: continue
            log(f"msg {m.id} | full caption: {m.message!r}")
            log(f"photo size: {m.photo.sizes[-1].size if m.photo else 'none'} bytes")
    finally:
        await cli.disconnect()
    log("DONE")
asyncio.run(main())
sys.exit(0)
