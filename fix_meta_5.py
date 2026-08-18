#!/usr/bin/env python3
"""fix_meta_5.py v4 — USER APPROVED: 5 posts edit. TELELTHON (KEY_18 session —
app ke ordered-posts isi session se chalti hain, channel access confirmed).
File download -> edit_message (replace file_name + thumb + caption), same message.
Fallback: caption only. Output me kabhi title print nahi."""
import os, sys, json, time, re, io, urllib.request, asyncio

MIDS = [8127, 8128, 8130, 8134, 8139]
SB = os.environ.get("KEY_20", "").strip().rstrip("/")
SBKEY = os.environ.get("KEY_21", "").strip()
META_FILE = "fix_meta_5_data.json"

def sb_json(url, method="GET", body=None):
    hdrs = {"apikey": SBKEY, "Authorization": f"Bearer {SBKEY}", "Content-Type": "application/json",
            "Prefer": "resolution=merge-duplicates"}
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers=hdrs)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode() or "null")

_META = {}
try:
    _META = json.load(open(META_FILE))
except Exception as e:
    print(f"[meta] load fail: {str(e)[:60]}", flush=True)

def make_thumb(img_url, out="/tmp/thumb.jpg"):
    try:
        try:
            from PIL import Image
        except Exception:
            os.system(f"{sys.executable} -m pip install -q Pillow")
            from PIL import Image
        req = urllib.request.Request(img_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=40) as r:
            data = r.read()
        im = Image.open(io.BytesIO(data)).convert("RGB")
        im.thumbnail((320, 320))
        im.save(out, "JPEG", quality=80)
        return out
    except Exception as e:
        print(f"  thumb fail: {str(e)[:50]}", flush=True)
        return None

def build_caption(m):
    show = m.get("show_title") or ""
    se = ""
    if m.get("season") is not None and m.get("episode") is not None:
        se = f" S{m['season']}E{m['episode']}"
    ttl = m.get("title") or (show + se).strip() or "Episode"
    lines = [f"<b>{ttl}</b>"]
    if show:
        lines.append((show + se).strip())
    if m.get("show_image"):
        lines.append(f'🎯 <a href="{m["show_image"]}">Thumbnail</a>')
    return "\n".join(lines)

async def main():
    os.system(f"{sys.executable} -m pip install -q telethon || true")
    from telethon import TelegramClient
    from telethon.sessions import StringSession

    mids_in = ",".join(str(x) for x in MIDS)
    rows = sb_json(SB + f"/rest/v1/episodes?select=mid,id&mid=in.({mids_in})&order=mid.desc")
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

    ok = 0
    for row in sorted(rows, key=lambda x: x["mid"]):
        mid = row["mid"]
        eid = row["id"]
        m = _META.get(str(mid)) or {}
        print(f"mid {mid}: meta S{m.get('season')}E{m.get('episode')} show={bool(m.get('show_title'))} img={bool(m.get('show_image'))}", flush=True)
        if not m.get("title") and not m.get("show_title"):
            print(f"mid {mid}: META missing — skip", flush=True)
            continue
        thumb_path = make_thumb(m.get("show_image") or "") if m.get("show_image") else None
        caption = build_caption(m)
        fname = f"{m.get('show_title') or 'Episode'} S{m.get('season')}E{m.get('episode')}.mp4"
        try:
            msg = await client.get_messages(ent, ids=mid)
            if msg is None:
                print(f"mid {mid}: message nahi mila", flush=True)
                continue
            path = await msg.download_media(file="/tmp/")
            if not path:
                print(f"mid {mid}: download fail", flush=True)
                continue
            sz = os.path.getsize(path)
            print(f"mid {mid}: downloaded {sz//1048576} MB", flush=True)
            # edit_message replace: file_name + thumb + caption (same message)
            await client.edit_message(ent, mid, file=path, thumb=thumb_path,
                                      caption=caption, parse_mode="html",
                                      force_document=True)
            try:
                os.remove(path)
            except Exception:
                pass
            print(f"mid {mid}: EDITED OK (fname+thumb+caption)", flush=True)
            ok += 1
        except Exception as e:
            print(f"mid {mid}: edit fail ({str(e)[:90]}) — caption fallback", flush=True)
            try:
                await client.edit_message(ent, mid, caption, parse_mode="html")
                print(f"mid {mid}: caption-only OK", flush=True)
                ok += 1
            except Exception as e2:
                print(f"mid {mid}: caption fail ({str(e2)[:70]})", flush=True)
        # DB update (best effort — show/season/episode/thumb)
        try:
            sb_json(SB + f"/rest/v1/episodes?id=eq.{eid}", "PATCH",
                    {"show": m.get("show_title"), "season": m.get("season"),
                     "episode": m.get("episode"), "title": m.get("title"),
                     "thumb": m.get("show_image") or ""})
            print(f"mid {mid}: DB updated", flush=True)
        except Exception as e:
            print(f"mid {mid}: DB fail {str(e)[:50]}", flush=True)
    await client.disconnect()
    print(f"[done] ok={ok}/{len(rows)}", flush=True)

if __name__ == "__main__":
    asyncio.run(main())
