#!/usr/bin/env python3
"""fix_captions_8366.py — USER APPROVED: 5 posts (8366-8370 = Obocchama S1E25-29)
caption fix. Meta Kartoons API se (alive token). Telethon edit (KEY_18).
Kabhi title print nahi — sirf position."""
import os, sys, json, re, urllib.request, asyncio

FIX = {
    8366: "68832d7fb66aa7802ca54c59",  # S1E25
    8367: "68832d7fb66aa7802ca54c5a",  # S1E26
    8368: "68832d7fb66aa7802ca54c5b",  # S1E27
    8369: "68832d7fb66aa7802ca54c5c",  # S1E28
    8370: "68832d7fb66aa7802ca54c5d",  # S1E29
}
SB = os.environ.get("KEY_20", "").strip().rstrip("/")
SBKEY = os.environ.get("KEY_21", "").strip()
SEP = "\u25AC" * 18

def sb_json(url, method="GET", body=None):
    hdrs = {"apikey": SBKEY, "Authorization": f"Bearer {SBKEY}", "Content-Type": "application/json",
            "Prefer": "resolution=merge-duplicates"}
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers=hdrs)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode() or "null")

def get_alive_token():
    d = sb_json(SB + "/rest/v1/progress?select=state&id=eq.tk_voughtx_kts-up&limit=1")
    if not d:
        return None
    st = d[0].get("state") or {}
    if isinstance(st, str):
        st = json.loads(st)
    for t in (st.get("tokens") or []):
        try:
            req = urllib.request.Request("https://api.kartoons.me/api/auth/me",
                headers={"Authorization": f"Bearer {t}", "X-Challenge-Token": t,
                         "User-Agent": "Mozilla/5.0", "Origin": "https://kartoons.me/",
                         "Referer": "https://kartoons.me/"})
            with urllib.request.urlopen(req, timeout=12) as r:
                if r.status == 200:
                    return t
        except Exception:
            pass
    return None

def get_meta(eid, tok):
    for attempt in range(3):
        try:
            req = urllib.request.Request(f"https://api.kartoons.me/api/shows/episode/{eid}",
                headers={"Authorization": f"Bearer {tok}", "X-Challenge-Token": tok,
                         "User-Agent": "Mozilla/5.0", "Origin": "https://kartoons.me/",
                         "Referer": "https://kartoons.me/"})
            with urllib.request.urlopen(req, timeout=25) as r:
                dd = json.loads(r.read().decode()).get("data") or {}
            sid = dd.get("seasonId") or {}
            show = {}
            if isinstance(sid, dict):
                sh = sid.get("showId") or {}
                if isinstance(sh, dict):
                    show = sh
            m = {
                "title": dd.get("title") or "",
                "season": dd.get("seasonNumber") or dd.get("season_number"),
                "episode": dd.get("episodeNumber") or dd.get("episode_number"),
                "show_title": (show.get("title") or ""),
                "show_id": (show.get("_id") or ""),
                "show_image": (show.get("image") or ""),
            }
            # API season field missing (inconsistency) — ye Obocchama S1 hain (verified)
            if m["season"] is None and str(eid).endswith("2ca54c59") or str(eid).endswith("2ca54c5a") or str(eid).endswith("2ca54c5b") or str(eid).endswith("2ca54c5c") or str(eid).endswith("2ca54c5d"):
                m["season"] = 1
            return m
        except Exception:
            import time
            time.sleep(2)
    return {}

def esc(s):
    return str(s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def build_caption(m, size):
    lines = []
    showname = m.get("show_title") or ""
    if m.get("title"):
        lines.append(f"\U0001F3AC <b><code>{esc(m['title'])}</code></b>")
    if showname:
        se = [esc(showname)]
        if m.get("season") is not None and m.get("episode") is not None:
            se.append(f"S{m['season']}-E{m['episode']}")
        lines.append("\U0001F4C0 <b><code>" + " \u00B7 ".join(se) + "</code></b>")
    lines.append(SEP)
    lines.append(f"\u2699\uFE0F Quality: <b>480p</b>")
    lines.append(f"\U0001F4AC Language: <b>Hindi</b>")
    sz = ""
    if size:
        mb = size / 1048576
        sz = f"{mb/1024:.1f} GB" if mb >= 1024 else f"{int(round(mb))} MB"
    if sz:
        lines.append(f"\U0001F4C2 Size: <b>{sz}</b>")
    lines.append(f"\U0001F5F3\uFE0F Category: <b>Show \u2022 Anime</b>")
    lines.append(SEP)
    tgt = "<b><a href=\"https://kartoons.me/\">Kartoons</a></b>"
    if m.get("show_image"):
        lines.append(f"\U0001F3AF {tgt} | <b><a href=\"{esc(m['show_image'])}\">Thumbnail</a></b>")
    else:
        lines.append(f"\U0001F3AF {tgt}")
    return "\n".join(lines)

async def main():
    os.system(f"{sys.executable} -m pip install -q telethon || true")
    from telethon import TelegramClient
    from telethon.sessions import StringSession

    tok = get_alive_token()
    print("alive token:", bool(tok), flush=True)
    if not tok:
        print("koi alive token nahi — abort", flush=True)
        return

    mids_in = ",".join(str(x) for x in FIX.keys())
    rows = sb_json(SB + f"/rest/v1/episodes?select=mid,id,size&mid=in.({mids_in})&order=mid.desc")
    print("rows:", len(rows), flush=True)

    client = TelegramClient(StringSession(os.environ.get("KEY_18", "").strip()),
                            int(os.environ.get("KEY_16", "0").strip()),
                            os.environ.get("KEY_17", "").strip(),
                            connection_retries=2)
    await client.connect()
    await client.get_me()
    ch_id = int(os.environ.get("KEY_2", "0").strip())
    ent = await client.get_entity(ch_id)
    print("entity OK", flush=True)

    ok = 0
    for row in sorted(rows, key=lambda x: x["mid"]):
        mid = row["mid"]
        eid = row["id"]
        m = get_meta(eid, tok)
        print(f"mid {mid}: meta S{m.get('season')}E{m.get('episode')} show={bool(m.get('show_title'))} img={bool(m.get('show_image'))}", flush=True)
        if not m.get("show_title") or m.get("season") is None or m.get("episode") is None:
            print(f"mid {mid}: meta incomplete — skip", flush=True)
            continue
        caption = build_caption(m, row.get("size") or 0)
        try:
            await client.edit_message(ent, mid, caption, parse_mode="html")
            print(f"mid {mid}: caption UPDATED", flush=True)
            ok += 1
        except Exception as e:
            print(f"mid {mid}: edit fail {str(e)[:70]}", flush=True)
        # DB update
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
