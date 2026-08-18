#!/usr/bin/env python3
"""fix_meta_5.py v3 — USER APPROVED: 5 posts (8127,8128,8130,8134,8139) edit.
Approach: message se asli file_id -> download -> edit_message_media re-upload
(file_name + thumbnail + caption) same message. Fallback: caption only.
Output me kabhi title print nahi. DB rows update.
"""
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
    # upgrade pyrogram to latest (InputMediaDocument file_name/thumb support)
    os.system(f"{sys.executable} -m pip install -q -U pyrogram TgCrypto || true")
    from pyrogram import Client
    from pyrogram.types import InputMediaDocument

    mids_in = ",".join(str(x) for x in MIDS)
    rows = sb_json(SB + f"/rest/v1/episodes?select=mid,id&mid=in.({mids_in})&order=mid.desc")
    print("rows found:", len(rows), flush=True)
    if not rows:
        print("koi rows nahi — abort", flush=True)
        return

    app = Client(":memory:",
        api_id=int(os.environ.get("KEY_16", "0").strip()),
        api_hash=os.environ.get("KEY_17", "").strip(),
        session_string=os.environ.get("KEY_19", "").strip(),
        workdir="/tmp",
    )
    await app.start()
    chat_id = int(os.environ.get("KEY_2", "0").strip())
    try:
        chat = await app.get_chat(chat_id)
        chat_id = chat.id
        print("chat resolved OK", flush=True)
    except Exception as e:
        print("chat resolve fail:", str(e)[:60], flush=True)

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
            # asli file_id message se (fid DB me document.id tha, galat)
            msg = await app.get_messages(chat_id, mid)
            if not msg or not msg.document:
                print(f"mid {mid}: message/document nahi mila", flush=True)
                continue
            real_fid = msg.document.file_id
            print(f"mid {mid}: doc file_id ok ({str(real_fid)[:20]}...)", flush=True)
            # download actual file
            path = await app.download_media(real_fid, in_memory=False)
            if not path:
                print(f"mid {mid}: download fail", flush=True)
                continue
            sz = os.path.getsize(path)
            print(f"mid {mid}: downloaded {sz//1048576} MB", flush=True)
            media = InputMediaDocument(
                media=path,
                file_name=fname,
                thumb=thumb_path,
                caption=caption,
                parse_mode="html",
            )
            await app.edit_message_media(chat_id, mid, media)
            try:
                os.remove(path)
            except Exception:
                pass
            print(f"mid {mid}: EDITED OK (fname+thumb+caption)", flush=True)
            ok += 1
        except Exception as e:
            print(f"mid {mid}: edit fail ({str(e)[:80]}) — caption fallback", flush=True)
            try:
                await app.edit_message_caption(chat_id, mid, caption, parse_mode="html")
                print(f"mid {mid}: caption-only OK", flush=True)
                ok += 1
            except Exception as e2:
                print(f"mid {mid}: caption fail ({str(e2)[:60]})", flush=True)
        # DB update (best effort)
        try:
            sb_json(SB + f"/rest/v1/episodes?id=eq.{eid}", "PATCH",
                    {"show": m.get("show_title"), "season": m.get("season"),
                     "episode": m.get("episode"), "title": m.get("title"),
                     "thumb": m.get("show_image") or ""})
            print(f"mid {mid}: DB updated", flush=True)
        except Exception as e:
            print(f"mid {mid}: DB fail {str(e)[:50]}", flush=True)
    await app.stop()
    print(f"[done] ok={ok}/{len(rows)}", flush=True)

if __name__ == "__main__":
    asyncio.run(main())
