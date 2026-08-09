#!/usr/bin/env python3
# del_posts.py — delete msgs 1693-1699 (duplicate Beyblade posters) + log what they were
import os, sys, json, asyncio, urllib.request as q

def log(*a): print("[del]", *a, flush=True)

KID = os.environ.get("KEY_16", "")
KHASH = os.environ.get("KEY_17", "")
SBURL = os.environ.get("KEY_20", "").rstrip("/")
SBKEY = os.environ.get("KEY_21", "")
CHAT = os.environ.get("KEY_2", "")

DEL_FROM, DEL_TO = 1693, 1699

def sb_get(path):
    req = q.Request(SBURL + path, headers={"apikey": SBKEY, "Authorization": "Bearer " + SBKEY})
    with q.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())

def sb_delete(path):
    req = q.Request(SBURL + path, headers={"apikey": SBKEY, "Authorization": "Bearer " + SBKEY}, method="DELETE")
    with q.urlopen(req, timeout=30) as r:
        return r.status

def load_sessions():
    st = (sb_get("/rest/v1/progress?select=state&id=eq.bot_sessions&limit=1") or [{}])[0].get("state") or {}
    return {k: v for k, v in st.items() if isinstance(v, list) and len(v) >= 1}

async def connect(sess):
    from telethon import TelegramClient
    from telethon.sessions import StringSession
    cli = TelegramClient(StringSession(sess), int(KID), KHASH, connection_retries=2, request_retries=2)
    await cli.connect()
    return cli

async def main():
    bots = load_sessions()
    ids = list(range(DEL_FROM, DEL_TO + 1))
    bname = "bot1" if "bot1" in bots else sorted(bots.keys())[0]
    cli = await connect(bots[bname][0])
    try:
        ch = int(CHAT) if str(CHAT).lstrip("-").isdigit() else CHAT
        # 1) log what these messages are
        msgs = await cli.get_messages(ch, ids=ids)
        found = {}
        for m in msgs:
            if m is not None:
                found[m.id] = m
        log(f"found {len(found)}/{len(ids)}")
        for mid in sorted(found.keys()):
            m = found[mid]
            media = "?"
            try:
                if m.photo: media = "PHOTO"
                elif m.video: media = "VIDEO"
                elif m.document: media = "DOC"
                elif m.text: media = "TEXT"
            except Exception: pass
            cap = ""
            try: cap = (m.message or "")[:60].replace("\n", " ")
            except Exception: pass
            log(f"  msg {mid} | {media} | {cap}")
        # 2) delete
        r = await cli.delete_messages(ch, ids)
        log(f"delete {len(ids)} -> {r}")
        # 3) verify gone
        after = await cli.get_messages(ch, ids=ids)
        gone = [i for i in ids if not any(a is not None and a.id == i for a in after)]
        log(f"verified deleted: {len(gone)}/{len(ids)} -> {gone}")
    finally:
        await cli.disconnect()
    # 4) any supabase rows with these mids? (posters shouldn't be there, but clean anyway)
    for mid in ids:
        try:
            st = sb_delete(f"/rest/v1/episodes?mid=eq.{mid}")
            log(f"sb mid {mid} -> {st}")
        except Exception as ex:
            log(f"sb err {mid}: {str(ex)[:60]}")
    log("DONE")

if __name__ == "__main__":
    asyncio.run(main())
    sys.exit(0)
