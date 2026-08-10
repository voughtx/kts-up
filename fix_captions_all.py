#!/usr/bin/env python3
"""fix_captions_all.py — Miraculous S5E19-25 captions fix (VERIFIED mapping).
E19-21,23 = 1080p · E22,24,25 = 360p (full-file ffprobe se confirmed)."""
import os, sys, json, asyncio, urllib.request

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

def sb_ep_update(eid, patch):
    req = urllib.request.Request(f"{SB_URL}/rest/v1/episodes?id=eq.{eid}",
        data=json.dumps(patch).encode(), method="PATCH",
        headers={"apikey": SB_KEY, "Authorization": f"Bearer {SB_KEY}",
                 "Content-Type": "application/json", "Prefer": "resolution=merge-duplicates"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.status

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

    # mid -> (ep, eid, correct_label) — VERIFIED via full file probe
    targets = {
        3011: (19, "6849900e6ed2282cba655f38", "1080p"),
        3012: (20, "6849900e6ed2282cba655f39", "1080p"),
        3013: (21, "6849900e6ed2282cba655f3a", "1080p"),
        3014: (22, "6849900e6ed2282cba655f3b", "360p"),
        3015: (23, "6849900e6ed2282cba655f3c", "1080p"),
        3016: (24, "6849900e6ed2282cba655f3d", "360p"),
        3017: (25, "6849900e6ed2282cba655f3e", "360p"),
    }
    for mid in sorted(targets):
        ep, eid, want = targets[mid]
        try:
            msg = await client.get_messages(CHANNEL, ids=mid)
            if msg is None:
                print(f"[S5E{ep}] message nahi mila", flush=True)
                continue
            cap = msg.message or ""
            print(f"[S5E{ep} mid={mid}] has576p={'576p' in cap} want={want} head={repr(cap[:70])}", flush=True)
            if "576p" in cap and want != "576p":
                newcap = cap.replace("576p", want)
                await client.edit_message(CHANNEL, mid, newcap)
                print(f"[S5E{ep}] EDITED -> {want} ✅", flush=True)
                try:
                    st = sb_ep_update(eid, {"quality": want, "qualities": [want]})
                    print(f"[S5E{ep}] supabase: {st}", flush=True)
                except Exception as e:
                    print(f"[S5E{ep}] supabase fail: {str(e)[:60]}", flush=True)
            else:
                print(f"[S5E{ep}] koi change nahi", flush=True)
        except Exception as e:
            print(f"[S5E{ep}] EXC {str(e)[:80]}", flush=True)
    await client.disconnect()
    print("[done]", flush=True)

asyncio.run(main())
