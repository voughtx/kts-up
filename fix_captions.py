# KTS fix_captions.py v2 — channel ke saare episodes ke captions NAYE format mein edit karta hai
# Naya format: Size + duration combined ("67 MB • 6 min") + 🎯 Kartoons | Thumbnail wapas
# Duration: Kartoons all-episodes API se ek call mein milta hai (durationMinutes)
import os, json, time

K2 = os.environ.get("KEY_2", "").strip()
SBURL = os.environ.get("KEY_20", "").strip().rstrip("/")
SBKEY = os.environ.get("KEY_21", "").strip()
PSESS = os.environ.get("KEY_19", "").strip()
AID = os.environ.get("KEY_16", "").strip()
AHASH = os.environ.get("KEY_17", "").strip()
LIMIT = int(os.environ.get("LIMIT", "200"))
API = os.environ.get("KEY_8", "").strip()
SHOWID = os.environ.get("SHOW_ID", "").strip()

def esc(s):
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

SEP = "\u25AC" * 18

def build_caption(d, dur=None):
    lines = []
    if d.get("title"):
        lines.append(f"\U0001F3AC <b><code>{esc(d['title'])}</code></b>")
    show = d.get("show") or ""
    se = None
    if d.get("season") is not None and d.get("episode") is not None:
        se = f"S{d['season']}-E{d['episode']}"
    if show and se:
        lines.append(f"\U0001F4C0 <b><code>{esc(show)} \u00B7 {se}</code></b>")
    elif show:
        lines.append(f"\U0001F4C0 <b><code>{esc(show)}</code></b>")
    elif (d.get("type") or "").startswith("movie") and d.get("title"):
        lines.append(f"\U0001F4C0 <b><code>{esc(d['title'])}</code></b>")
    lines.append(SEP)
    if d.get("quality"):
        lines.append(f"\u2699\uFE0F Quality: <b>{esc(d['quality'])}</b>")
    lines.append(f"\U0001F4AC Language: <b>{esc(d.get('lang') or 'Hindi')}</b>")
    sz = ""
    size = d.get("size") or 0
    if size:
        mb = size / (1024 * 1024)
        if mb >= 1024:
            sz = f"{int(round(mb/1024))} GB"
        else:
            sz = f"{int(round(mb))} MB"
    if dur:
        if sz:
            sz = f"{sz} \u2022 {int(dur)} min"
        else:
            sz = f"{int(dur)} min"
    if sz:
        lines.append(f"\U0001F4C2 Size: <b>{sz}</b>")
    tlab = "Movie" if (d.get("type") or "").startswith("movie") else "Show"
    clab = d.get("category") or ""
    lines.append(f"\U0001F5F3\uFE0F Category: <b>{esc(tlab)} \u2022 {esc(clab)}</b>")
    lines.append(SEP)
    tgt = ""
    web = d.get("web") or ""
    thumb = d.get("thumb") or ""
    if web:
        dom = web.split("//")[-1].split("/")[0]
        lab = dom.split(".")[0].capitalize() if "." in dom else dom
        tgt = f"<b><a href=\"{esc(web)}\">{esc(lab)}</a></b>"
    if tgt and thumb:
        lines.append(f"\U0001F3AF {tgt} | <b><a href=\"{esc(thumb)}\">Thumbnail</a></b>")
    elif tgt:
        lines.append(f"\U0001F3AF {tgt}")
    elif thumb:
        lines.append(f"\U0001F3AF <b><a href=\"{esc(thumb)}\">Thumbnail</a></b>")
    return "\n".join(lines)

def sb_get_episodes():
    import urllib.request as u
    req = u.Request(f"{SBURL}/rest/v1/episodes?select=*&limit={LIMIT}",
                    headers={"apikey": SBKEY, "Authorization": f"Bearer {SBKEY}"})
    with u.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())

def fetch_durations():
    """Kartoons all-episodes se durationMinutes map (episode_id -> minutes)."""
    if not (API and SHOWID):
        return {}
    import urllib.request as u
    out = {}
    try:
        # seasons list
        req = u.Request(f"{API}/shows/{SHOWID}", headers={"User-Agent": "Mozilla/5.0",
                       "Accept": "application/json", "Origin": "https://kartoons.me", "Referer": "https://kartoons.me/"})
        with u.urlopen(req, timeout=30) as r:
            sj = json.loads(r.read().decode())
        seasons = [s for s in (sj.get("data", {}).get("seasons") or []) if s.get("_id")]
        for s in seasons:
            req2 = u.Request(f"{API}/shows/{SHOWID}/season/{s['_id']}/all-episodes",
                             headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json",
                                      "Origin": "https://kartoons.me", "Referer": "https://kartoons.me/"})
            with u.urlopen(req2, timeout=30) as r2:
                ej = json.loads(r2.read().decode())
            for e in (ej.get("data") or []):
                out[e.get("_id")] = e.get("durationMinutes") or 0
    except Exception as ex:
        print(f"[!] durations fetch fail: {str(ex)[:80]}")
    return out

def main():
    from pyrogram import Client, enums
    import asyncio

    durs = fetch_durations()
    print(f"[*] durations map: {len(durs)} episodes")

    async def run():
        app = Client("fixsess", session_string=PSESS, api_id=int(AID) if AID else None,
                     api_hash=AHASH or None, no_updates=True)
        await app.start()
        me = await app.get_me()
        print(f"[*] connected as {me.username or me.first_name} (bot={me.is_bot})")
        chat = None
        try:
            chat = await app.get_chat(int(K2))
        except Exception:
            print("[!] get_chat fail — dialogs scan...")
            async for d in app.get_dialogs():
                if d.chat and d.chat.id == int(K2):
                    chat = d.chat
                    break
        if chat is None:
            print("[x] channel resolve fail")
            await app.stop()
            return
        print(f"[*] target resolved: {chat.title} ({chat.id})")
        eps = sb_get_episodes()
        print(f"[*] total episodes: {len(eps)}")
        okc, failc = 0, 0
        fails = []
        for d in eps:
            mid = d.get("mid")
            if not mid:
                continue
            dur = durs.get(d.get("id") or "", 0) or None
            cap = build_caption(d, dur)
            try:
                await app.edit_message_caption(chat.id, int(mid), cap, parse_mode=enums.ParseMode.HTML)
                okc += 1
            except Exception as e:
                failc += 1
                fails.append(f"{mid}:{str(e)[:60]}")
            time.sleep(0.4)
            if (okc + failc) % 10 == 0:
                print(f"   ... {okc} ok, {failc} fail")
        print(f"[ok] done: {okc} edited, {failc} failed")
        if fails:
            print("fails:", "; ".join(fails[:20]))
        await app.stop()

    asyncio.run(run())

if __name__ == "__main__":
    main()
