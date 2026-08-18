#!/usr/bin/env python3
"""fix_meta_5.py v5 — USER APPROVED: 5 posts (8127,8128,8130,8134,8139) SIRF caption
update — app ke exact format me. Koi file download/upload/thumb nahi (fast+safe).
Meta JSON se; DB update. Telethon KEY_18 session."""
import os, sys, json, re, urllib.request, asyncio

MIDS = [8127, 8128, 8130, 8134, 8139]
SB = os.environ.get("KEY_20", "").strip().rstrip("/")
SBKEY = os.environ.get("KEY_21", "").strip()
SEP = "\u25AC" * 18

META_FILE = "fix_meta_5_data.json"

def sb_json(url, method="GET", body=None):
    hdrs = {"apikey": SBKEY, "Authorization": f"Bearer {SBKEY}", "Content-Type": "application/json",
            "Prefer": "resolution=merge-duplicates"}
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers=hdrs)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode() or "null")

def esc(s):
    return str(s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def build_caption(m, size):
    lines = []
    showname = m.get("show_title") or ""
    if showname == "Doraemon":
        showname = "Doraemon (HUNGAMA)"
    if m.get("title"):
        lines.append(f"\U0001F3AC <b><code>{esc(m['title'])}</code></b>")
    if showname:
        se = [esc(showname)]
        if m.get("season") is not None and m.get("episode") is not None:
            se.append(f"S{m['season']}-E{m['episode']}")
        lines.append("\U0001F4C0 <b><code>" + " \u00B7 ".join(se) + "</code></b>")
    lines.append(SEP)
    q = m.get("quality") or "480p"
    lines.append(f"\u2699\uFE0F Quality: <b>{esc(q)}</b>")
    lines.append(f"\U0001F4AC Language: <b>{esc(m.get('lang') or 'Hindi')}</b>")
    sz = ""
    if size:
        mb = size / (1048576)
        sz = f"{mb/1024:.1f} GB" if mb >= 1024 else f"{int(round(mb))} MB"
    if sz:
        lines.append(f"\U0001F4C2 Size: <b>{sz}</b>")
    lines.append(f"\U0001F5F3\uFE0F Category: <b>{esc('Show \u2022 ' + (m.get('category') or 'Anime'))}</b>")
    lines.append(SEP)
    tgt = f"<b><a href=\"{esc('https://kartoons.me/')}\">Kartoons</a></b>"
    if m.get("show_image"):
        lines.append(f"\U0001F3AF {tgt} | <b><a href=\"{esc(m['show_image'])}\">Thumbnail</a></b>")
    else:
        lines.append(f"\U0001F3AF {tgt}")
    return "\n".join(lines)

async def main():
    os.system(f"{sys.executable} -m pip install -q telethon || true")
    from telethon import TelegramClient
    from telethon.sessions import StringSession

    mids_in = ",".join(str(x) for x in MIDS)
    rows = sb_json(SB + f"/rest/v1/episodes?select=mid,id,size,quality&mid=in.({mids_in})&order=mid.desc")
    print("rows found:", len(rows), flush=True)
    if not rows:
        print("koi rows nahi — abort", flush=True)
        return

    client = TelegramClient(StringSession(os.environ.get("KEY_18", "").strip()),
                            int(os.environ.get("KEY_16", "0").strip()),
                            os.environ.get("KEY_17", "").strip(),
                            connection_retries=2)
    await client.connect()
    await client.get_me()
    ch_id = int(os.environ.get("KEY_2", "0").strip())
    try:
        ent = await client.get_entity(ch_id)
        print("entity resolved OK", flush=True)
    except Exception as e:
        print("entity resolve fail:", str(e)[:60], flush=True)
        await client.disconnect()
        return

    _META = {}
    try:
        _META = json.load(open(META_FILE))
    except Exception as e:
        print(f"[meta] load fail: {str(e)[:60]}", flush=True)
    ok = 0
    for row in sorted(rows, key=lambda x: x["mid"]):
        mid = row["mid"]
        eid = row["id"]
        m = dict(_META.get(str(mid)) or {})
        m["quality"] = row.get("quality") or "480p"
        size = row.get("size") or 0
        caption = build_caption(m, size)
        try:
            await client.edit_message(ent, mid, caption, parse_mode="html")
            print(f"mid {mid}: caption UPDATED OK", flush=True)
            ok += 1
        except Exception as e:
            print(f"mid {mid}: caption fail ({str(e)[:80]})", flush=True)
    await client.disconnect()
    print(f"[done] captions ok={ok}/{len(rows)}", flush=True)

if __name__ == "__main__":
    asyncio.run(main())
