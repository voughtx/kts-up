#!/usr/bin/env python3
"""fix_meta_5.py — USER APPROVED: 5 posts (8127,8128,8130,8134,8139) ka
caption + filename + thumbnail fix. DELETE nahi — EDIT karke (same message).
Meta Kartoons API se (relay) — sirf position/title-required data, output
me kabhi title print nahi. DB rows bhi update (show/season/episode/thumb).
"""
import os, json, time, re, io, urllib.request, urllib.parse, asyncio

MIDS = [8127, 8128, 8130, 8134, 8139]
SB = os.environ.get("KEY_20", "").strip().rstrip("/")
SBKEY = os.environ.get("KEY_21", "").strip()
RELAY = "https://kts-url.gobinog.workers.dev/relay"

def sb_json(url, method="GET", body=None):
    hdrs = {"apikey": SBKEY, "Authorization": f"Bearer {SBKEY}", "Content-Type": "application/json",
            "Prefer": "resolution=merge-duplicates"}
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers=hdrs)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode() or "null")

def relay(path):
    # pool token se auth (episode meta LOGIN_REQUIRED)
    tok = ""
    try:
        d = sb_json(SB + "/rest/v1/progress?select=state&id=eq.tk_voughtx_kts-up&limit=1")
        if d:
            st = d[0].get("state") or {}
            if isinstance(st, str): st = json.loads(st)
            toks = st.get("tokens") or []
            idx = int(st.get("idx") or 0)
            if toks:
                tok = toks[idx % len(toks)]
    except Exception:
        pass
    params = [("path", path)]
    if tok:
        params.append(("h_Authorization", "Bearer " + tok))
    q = urllib.parse.urlencode(params)
    req = urllib.request.Request(RELAY + "?" + q,
        headers={"X-KTS-Key": "ktsrelay2026", "User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())

def get_meta(eid):
    """Episode meta — sirf fields chahiye (title kabhi print nahi)."""
    d = relay(f"/shows/episode/{eid}")
    dd = (d or {}).get("data") or {}
    sid = dd.get("seasonId") or {}
    show = {}
    if isinstance(sid, dict):
        sh = sid.get("showId") or {}
        if isinstance(sh, dict):
            show = sh
    return {
        "title": dd.get("title") or "",
        "season": dd.get("seasonNumber") or dd.get("season_number"),
        "episode": dd.get("episodeNumber") or dd.get("episode_number"),
        "show_title": (show.get("title") or ""),
        "show_id": (show.get("_id") or ""),
        "show_image": (show.get("image") or ""),
    }

def make_thumb(img_url, out="/tmp/thumb.jpg"):
    """Poster -> 320px JPEG thumbnail."""
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

def build_caption(m, mid, has_thumb_url):
    """App jaise caption (HTML). Title text include; thumb link ya poster URL."""
    show = m.get("show_title") or ""
    se = ""
    if m.get("season") is not None and m.get("episode") is not None:
        se = f" S{m['season']}E{m['episode']}"
    ttl = m.get("title") or (show + se)
    lines = [f"<b>{ttl}</b>"]
    if show:
        lines.append(f"{show}{se}".strip())
    if has_thumb_url:
        lines.append(f'🎯 <a href="{has_thumb_url}">Thumbnail</a>')
    return "\n".join(lines)

async def fix_post(app, mid, eid, dbrow):
    from pyrogram.types import InputMediaDocument
    m = get_meta(eid)
    print(f"mid {mid}: meta S{m.get('season')}E{m.get('episode')} show={bool(m.get('show_title'))} img={bool(m.get('show_image'))}", flush=True)
    if not m.get("title") and not m.get("show_title"):
        print(f"mid {mid}: META FAIL — skip (guard)", flush=True)
        return False
    thumb_path = make_thumb(m.get("show_image") or "") if m.get("show_image") else None
    # caption me poster link (thumb URL) — user ne bola thumb na set ho to caption me link
    caption = build_caption(m, mid, m.get("show_image") or "")
    fname = f"{m.get('show_title') or 'Episode'} S{m.get('season')}E{m.get('episode')}.mp4"
    chat = int(os.environ.get("KEY_2", "0").strip())
    try:
        # try edit with file_id reference (instant) + file_name + thumb + caption
        media = InputMediaDocument(
            media=dbrow.get("fid") or dbrow.get("id") or "",
            file_name=fname,
            thumb=thumb_path,
            caption=caption,
            parse_mode="html",
        )
        await app.edit_message_media(chat, mid, media)
        print(f"mid {mid}: edited (file_id ref + fname + thumb) OK", flush=True)
    except Exception as e:
        print(f"mid {mid}: file_id edit fail ({str(e)[:60]}) — re-upload try", flush=True)
        try:
            # download + re-upload (edit media replace)
            path = await app.download_media(dbrow.get("fid") or mid)
            if not path:
                print(f"mid {mid}: download fail", flush=True); return False
            media2 = InputMediaDocument(
                media=path, file_name=fname, thumb=thumb_path,
                caption=caption, parse_mode="html")
            await app.edit_message_media(chat, mid, media2)
            os.path.exists(path) and os.remove(path)
            print(f"mid {mid}: edited (re-upload) OK", flush=True)
        except Exception as e2:
            print(f"mid {mid}: re-upload edit fail ({str(e2)[:70]})", flush=True)
            # fallback: sirf caption (agar kuch nahi hua to)
            try:
                await app.edit_message_caption(chat, mid, caption, parse_mode="html")
                print(f"mid {mid}: caption-only edit OK", flush=True)
            except Exception as e3:
                print(f"mid {mid}: caption edit fail ({str(e3)[:50]})", flush=True)
                return False
    # DB update
    try:
        sb_json(SB + f"/rest/v1/episodes?id=eq.{eid}", "PATCH",
                {"show": m.get("show_title"), "season": m.get("season"),
                 "episode": m.get("episode"), "title": m.get("title"),
                 "thumb": m.get("show_image") or ""})
        print(f"mid {mid}: DB updated", flush=True)
    except Exception as e:
        print(f"mid {mid}: DB update fail {str(e)[:50]}", flush=True)
    return True

async def main():
    from pyrogram import Client
    # fetch rows
    mids_in = ",".join(str(x) for x in MIDS)
    rows = sb_json(SB + f"/rest/v1/episodes?select=mid,id,fid&mid=in.({mids_in})&order=mid.desc")
    print("rows found:", len(rows), flush=True)
    if not rows:
        print("koi rows nahi — abort", flush=True); return
    app = Client(":memory:",
        api_id=int(os.environ.get("KEY_16", "0").strip()),
        api_hash=os.environ.get("KEY_17", "").strip(),
        session_string=os.environ.get("KEY_18", "").strip(),
    )
    await app.start()
    ok = 0
    for row in sorted(rows, key=lambda x: x["mid"]):
        try:
            if await fix_post(app, row["mid"], row["id"], row):
                ok += 1
        except Exception as e:
            print(f"mid {row['mid']}: ERR {str(e)[:70]}", flush=True)
    await app.stop()
    print(f"[done] ok={ok}/{len(rows)}", flush=True)

if __name__ == "__main__":
    asyncio.run(main())
