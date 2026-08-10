#!/usr/bin/env python3
"""fix_captions.py — Miraculous S5E16-18 captions fix (576p -> 1080p) + Supabase update.
Reads actual caption via Telethon, replaces quality, edits message, updates DB."""
import os, sys, json, asyncio, urllib.request

SB_URL = os.environ.get("KEY_20", "").strip().rstrip("/")
SB_KEY = os.environ.get("KEY_21", "").strip()
API_ID = int(os.environ.get("KEY_16", "0") or 0)
API_HASH = os.environ.get("KEY_17", "").strip()
CHANNEL = int(os.environ.get("KEY_2", "-1003808766192").strip())

print(f"[*] api_id={API_ID} hash_len={len(API_HASH)} channel={CHANNEL}", flush=True)

# --- supabase helpers ---
def sb_get(path):
    req = urllib.request.Request(f"{SB_URL}/rest/v1/progress?select=state&id=eq.{path}",
        headers={"apikey": SB_KEY, "Authorization": f"Bearer {SB_KEY}"})
    with urllib.request.urlopen(req, timeout=20) as r:
        arr = json.loads(r.read().decode())
    return arr[0]["state"] if arr else {}

def sb_upsert(row):
    req = urllib.request.Request(f"{SB_URL}/rest/v1/progress",
        data=json.dumps(row).encode(), method="POST",
        headers={"apikey": SB_KEY, "Authorization": f"Bearer {SB_KEY}",
                 "Content-Type": "application/json", "Prefer": "resolution=merge-duplicates"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.status

def sb_ep_update(eid, patch):
    req = urllib.request.Request(f"{SB_URL}/rest/v1/episodes?id=eq.{eid}",
        data=json.dumps(patch).encode(), method="PATCH",
        headers={"apikey": SB_KEY, "Authorization": f"Bearer {SB_KEY}",
                 "Content-Type": "application/json", "Prefer": "resolution=merge-duplicates"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.status

# --- telethon ---
async def main():
    from telethon import TelegramClient
    from telethon.sessions import StringSession
    sessions = sb_get("bot_sessions")
    bots = {k: v for k, v in sessions.items() if k.startswith("bot") and isinstance(v, list)}
    print("[*] bots available:", sorted(bots.keys()), flush=True)

    # (ep, eid, mid) — confirmed 1080p via segment probe
    targets = [
        (16, "6849900e6ed2282cba655f35", 3008),
        (17, "6849900e6ed2282cba655f36", 3009),
        (18, "6849900e6ed2282cba655f37", 3010),
    ]

    # pool of all sessions (bot1..6 x 4)
    pool = []
    for bname, slist in bots.items():
        for s in slist:
            pool.append((bname, s))

    # map: mid -> which bot posted (try all)
    for ep, eid, mid in targets:
        done = False
        for bname, sess in pool:
            try:
                client = TelegramClient(StringSession(sess), API_ID, API_HASH)
                await client.connect()
                if not await client.is_user_authorized():
                    await client.disconnect()
                    continue
                msg = await client.get_messages(CHANNEL, ids=mid)
                if msg is None:
                    await client.disconnect()
                    continue
                cap = msg.message or ""
                print(f"[S5E{ep}] bot={bname} mid={mid} caption_has_576p={'576p' in cap} len={len(cap)}", flush=True)
                print(f"[S5E{ep}] caption_head={repr(cap[:120])}", flush=True)
                if "576p" in cap:
                    newcap = cap.replace("576p", "1080p")
                    await client.edit_message(CHANNEL, mid, newcap)
                    print(f"[S5E{ep}] EDITED -> 1080p ✅", flush=True)
                    # update supabase
                    try:
                        st = sb_ep_update(eid, {"quality": "1080p", "qualities": ["1080p"]})
                        print(f"[S5E{ep}] supabase update: {st}", flush=True)
                    except Exception as e:
                        print(f"[S5E{ep}] supabase update fail: {str(e)[:60]}", flush=True)
                else:
                    print(f"[S5E{ep}] 576p nahi mila — caption alag hai, koi edit nahi", flush=True)
                await client.disconnect()
                done = True
                break
            except Exception as e:
                try:
                    await client.disconnect()
                except Exception:
                    pass
                continue
        if not done:
            print(f"[S5E{ep}] kisi bot se edit nahi hua ❌", flush=True)

asyncio.run(main())
print("[done]", flush=True)
