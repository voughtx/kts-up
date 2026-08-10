#!/usr/bin/env python3
"""diag_full_files.py — E19-25 posted videos download karke ffprobe height.
Full file download (Telethon) — definitive resolution check."""
import os, sys, json, asyncio, subprocess, urllib.request

SB_URL = os.environ.get("KEY_20", "").strip().rstrip("/")
SB_KEY = os.environ.get("KEY_21", "").strip()
API_ID = int(os.environ.get("KEY_16", "0") or 0)
API_HASH = os.environ.get("KEY_17", "").strip()
CHANNEL = int(os.environ.get("KEY_2", "-1003808766192").strip())

def sb_get(path):
    req = urllib.request.Request(f"{SB_URL}/rest/v1/progress?select=state&id=eq.{path}",
        headers={"apikey": SB_KEY, "Authorization": f"Bearer {SB_KEY}"})
    with urllib.request.urlopen(req, timeout=20) as r:
        arr = json.loads(r.read().decode())
    return arr[0]["state"] if arr else {}

async def main():
    from telethon import TelegramClient
    from telethon.sessions import StringSession
    sessions = sb_get("bot_sessions")
    pool = []
    for bname, slist in sessions.items():
        if bname.startswith("bot") and isinstance(slist, list):
            for s in slist:
                pool.append((bname, s))
    client = None
    for bname, sess in pool:
        try:
            c = TelegramClient(StringSession(sess), API_ID, API_HASH)
            await c.connect()
            if await c.is_user_authorized():
                client = c
                print(f"[ok] client via {bname}", flush=True)
                break
            await c.disconnect()
        except Exception:
            continue
    if client is None:
        print("[!] no client", flush=True)
        return

    mids = {3011: 19, 3012: 20, 3013: 21, 3014: 22, 3015: 23, 3016: 24, 3017: 25}
    for mid in sorted(mids):
        ep = mids[mid]
        try:
            msg = await client.get_messages(CHANNEL, ids=mid)
            if msg is None or not msg.document:
                print(f"[S5E{ep}] no doc", flush=True)
                continue
            p = f"/tmp/full_{ep}.mp4"
            if os.path.exists(p):
                os.remove(p)
            await client.download_media(msg, file=p)
            sz = os.path.getsize(p) if os.path.exists(p) else 0
            pr = subprocess.run(f"ffprobe -v error -show_streams -of json {p}",
                                shell=True, capture_output=True, text=True, timeout=60)
            h = None
            try:
                jj = json.loads(pr.stdout)
                for st in (jj.get("streams") or []):
                    if st.get("codec_type") == "video" and st.get("height"):
                        h = f"{st['width']}x{st['height']}"
                        break
            except Exception:
                pass
            print(f"[S5E{ep} mid={mid}] size={sz/1048576:.1f}MB height={h}", flush=True)
        except Exception as e:
            print(f"[S5E{ep}] EXC {str(e)[:80]}", flush=True)
    await client.disconnect()
    print("[done]", flush=True)

asyncio.run(main())
