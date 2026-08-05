# KTS fix_captions.py — channel ke purane messages ke captions naye clean format mein edit karta hai
# Bot channel admin hai, isliye editMessageCaption kaam karta hai (uploads bhi wahi bot thread se dekhe the)
import os, json, time, urllib.request as u, urllib.parse as p

K1 = os.environ.get("KEY_1", "").strip()
K2 = os.environ.get("KEY_2", "").strip()
SBURL = os.environ.get("KEY_20", "").strip().rstrip("/")
SBKEY = os.environ.get("KEY_21", "").strip()
TB = os.environ.get("KEY_13", "").rstrip("/")
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
    if show:
        line = f"\U0001F4C0 <b><code>{esc(show)}</code></b>"
        if se:
            line = f"\U0001F4C0 <b><code>{esc(show)} \u00B7 {se}</code></b>"
        lines.append(line)
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
    req = u.Request(f"{SBURL}/rest/v1/episodes?select=*&limit={LIMIT}",
                    headers={"apikey": SBKEY, "Authorization": f"Bearer {SBKEY}"})
    with u.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())

def edit_caption(mid, caption):
    data = p.urlencode({"chat_id": K2, "message_id": mid, "caption": caption, "parse_mode": "HTML"}).encode()
    req = u.Request(f"{TB}/{K1}/editMessageCaption", data=data, method="POST")
    try:
        with u.urlopen(req, timeout=40) as r:
            j = json.loads(r.read().decode())
            return j.get("ok", False), (j.get("description") or "")
    except Exception as e:
        return False, str(e)[:80]

def main():
    eps = sb_get_episodes()
    print(f"[*] total episodes: {len(eps)}")
    okc, failc = 0, 0
    fails = []
    for d in eps:
        mid = d.get("mid")
        if not mid:
            continue
        cap = build_caption(d)
        ok, err = edit_caption(mid, cap)
        if ok:
            okc += 1
        else:
            failc += 1
            fails.append(f"{mid}:{err}")
        time.sleep(0.8)
        if (okc + failc) % 10 == 0:
            print(f"   ... {okc} ok, {failc} fail")
    print(f"[ok] done: {okc} edited, {failc} failed")
    if fails:
        print("fails:", "; ".join(fails[:20]))

if __name__ == "__main__":
    main()
