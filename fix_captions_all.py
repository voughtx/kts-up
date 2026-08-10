#!/usr/bin/env python3
"""fix_captions_all.py — Miraculous S5E16-25: Telegram message se actual video dims
read karke caption quality label verify + fix + Supabase update."""
import os, sys, json, asyncio, urllib.request

SB_URL = os.environ.get("KEY_20", "").strip().rstrip("/")
SB_KEY = os.environ.get("KEY_21", "").strip()
API_ID = int(os.environ.get("KEY_16", "0") or 0)
API_HASH = os.environ.get("KEY_17", "").strip()
CHANNEL = int(os.environ.get("KEY_2", "-1003808766192").strip())

print(f"[*] api_id={API_ID} hash_len={len(API_HASH)}", flush=True)

def sb_get(path):
    req = urllib.request.Request(f"{SB_URL}/rest/v1/progress?select=state&id=eq.{path}",
        headers={"apikey": SB_KEY, "Authorization": f"Bearer {SB_KEY}"})
    with urllib.request.urlopen(req, timeout=20) as r:
        arr = json.loads(r.read().decode())
    return arr[0]["state"] if arr else {}

def sb_ep_update(eid, patch):
    req = urllib.request.Request(f"{SB_URL}/rest/v1/episodes?id=eq.{eid}",
        data=json.dumps(patch).encode(), method="PATCH",
        headers={"apikey": SB_KEY, "Authorization": f"Bearer {SB_KEY}",
                 "Content-Type": "application/json", "Prefer": "resolution=merge-duplicates"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.status

def h_to_label(h):
    if not h: return None
    if h >= 1920: return "1080p"
    if h >= 1280: return "720p"
    if h >= 1000: return "576p"
    if h >= 700: return "480p"
    return "360p"

async def main():
    from telethon import TelegramClient
    from telethon.sessions import StringSession
    sessions = sb_get("bot_sessions")
    bots = {k: v for k, v in sessions.items() if k.startswith("bot") and isinstance(v, list)}
    pool = []
    for bname, slist in bots.items():
        for s in slist:
            pool.append((bname, s))

    # mid -> (ep, eid)
    targets = {
        3008: (16, "6849900e6ed2282cba655f35"),
        3009: (17, "6849900e6ed2282cba655f36"),
        3010: (18, "6849900e6ed2282cba655f37"),
        3011: (19, "6849900e6ed2282cba655f38"),
        3012: (20, "6849900e6ed2282cba655f39"),
        3013: (21, "6849900e6ed2282cba655f3a"),
        3014: (22, "6849900e6ed2282cba655f3b"),
        3015: (23, "6849900e6ed2282cba655f3c"),
        3016: (24, "6849900e6ed2282cba655f3d"),
        3017: (25, "6849900e6ed2282cba655f3e"),
    }

    # find one working client first
    client = None
    used_bot = None
    for bname, sess in pool:
        try:
            c = TelegramClient(StringSession(sess), API_ID, API_HASH)
            await c.connect()
            if await c.is_user_authorized():
                client = c
                used_bot = bname
                print(f"[ok] client via {bname}", flush=True)
                break
            await c.disconnect()
        except Exception:
            continue
    if client is None:
        print("[!] koi bot session kaam nahi kiya", flush=True)
        return

    for mid in sorted(targets):
        ep, eid = targets[mid]
        try:
            msg = await client.get_messages(CHANNEL, ids=mid)
            if msg is None:
                print(f"[{mid}] message nahi mila", flush=True)
                continue
            cap = msg.message or ""
            # dims from video/document
            w = h = None
            if msg.video:
                w, h = msg.video.w, msg.video.h
            if msg.document:
                from telethon.tl.types import DocumentAttributeVideo
                for a in msg.document.attributes:
                    if isinstance(a, DocumentAttributeVideo):
                        w, h = a.w, a.h
            if (not w or not h) and msg.document:
                # partial download: pehle ~4MB, ffprobe se height
                import subprocess
                try:
                    p = f"/tmp/probe_{mid}.bin"
                    if os.path.exists(p):
                        os.remove(p)
                    with open(p, "wb") as f:
                        async for chunk in client.iter_download(msg.document, offset=0, stride=1024*1024):
                            f.write(chunk)
                            if f.tell() >= 4*1024*1024:
                                break
                    if os.path.exists(p) and os.path.getsize(p) > 0:
                        pr = subprocess.run(
                            f"ffprobe -v error -show_streams -of json {p}",
                            shell=True, capture_output=True, text=True, timeout=40)
                        try:
                            jj = json.loads(pr.stdout)
                            for st in (jj.get("streams") or []):
                                if st.get("codec_type") == "video" and st.get("height"):
                                    w, h = st["width"], st["height"]
                                    break
                        except Exception:
                            pass
                        print(f"    [dbg] partial {os.path.getsize(p)}B probe -> {w}x{h}", flush=True)
                except Exception as e:
                    print(f"    [dbg] partial dl fail: {str(e)[:60]}", flush=True)
            label = h_to_label(h)
            print(f"[S5E{ep} mid={mid}] dims={w}x{h} label={label} caption_q={'576p' in cap} caption_head={repr(cap[:60])}", flush=True)
            if label and "576p" in cap and label != "576p":
                newcap = cap.replace("576p", label)
                await client.edit_message(CHANNEL, mid, newcap)
                print(f"[S5E{ep}] EDITED -> {label} ✅", flush=True)
                try:
                    st = sb_ep_update(eid, {"quality": label, "qualities": [label]})
                    print(f"[S5E{ep}] supabase: {st}", flush=True)
                except Exception as e:
                    print(f"[S5E{ep}] supabase fail: {str(e)[:60]}", flush=True)
            elif label and label == "576p":
                print(f"[S5E{ep}] 576p sahi hai — koi change nahi", flush=True)
            else:
                print(f"[S5E{ep}] dims nahi mile — skip", flush=True)
        except Exception as e:
            print(f"[S5E{ep}] EXC {str(e)[:80]}", flush=True)

    await client.disconnect()
    print("[done]", flush=True)

asyncio.run(main())
