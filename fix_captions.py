# KTS fix_captions.py — channel ke purane messages ke captions naye clean format mein edit karta hai
# Pyrogram (user account) se — kyunki uploads user account se hue the, bot edit nahi kar sakta
import os, json, time

K2 = os.environ.get("KEY_2", "").strip()
SBURL = os.environ.get("KEY_20", "").strip().rstrip("/")
SBKEY = os.environ.get("KEY_21", "").strip()
PSESS = os.environ.get("KEY_19", "").strip()
AID = os.environ.get("KEY_16", "").strip()
AHASH = os.environ.get("KEY_17", "").strip()
LIMIT = int(os.environ.get("LIMIT", "200"))

def esc(s):
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

SEP = "\u25AC" * 18

def build_caption(d):
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
    size = d.get("size") or 0
    if size:
        mb = size / (1024 * 1024)
        if mb >= 1024:
            lines.append(f"\U0001F4C2 Size: <b>{int(round(mb/1024))} GB</b>")
        else:
            lines.append(f"\U0001F4C2 Size: <b>{int(round(mb))} MB</b>")
    tlab = "Movie" if (d.get("type") or "").startswith("movie") else "Show"
    clab = d.get("category") or ""
    lines.append(f"\U0001F5F3\uFE0F Category: <b>{esc(tlab)} \u2022 {esc(clab)}</b>")
    lines.append(SEP)
    return "\n".join(lines)

def sb_get_episodes():
    import urllib.request as u
    req = u.Request(f"{SBURL}/rest/v1/episodes?select=*&limit={LIMIT}",
                    headers={"apikey": SBKEY, "Authorization": f"Bearer {SBKEY}"})
    with u.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())

def main():
    from pyrogram import Client
    import asyncio

    async def run():
        app = Client("fixsess", session_string=PSESS, api_id=int(AID) if AID else None,
                     api_hash=AHASH or None, no_updates=True)
        await app.start()
        me = await app.get_me()
        print(f"[*] connected as {me.username or me.first_name} (bot={me.is_bot})")
        eps = sb_get_episodes()
        print(f"[*] total episodes: {len(eps)}")
        okc, failc = 0, 0
        fails = []
        for d in eps:
            mid = d.get("mid")
            if not mid:
                continue
            cap = build_caption(d)
            try:
                await app.edit_message_caption(int(K2), int(mid), cap, parse_mode="html")
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
