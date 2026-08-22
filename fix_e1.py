#!/usr/bin/env python3
"""fix_e1.py — Infinity Nado S1E1 missing post + poster + DB. Position-only logs."""
import os, sys, json, re, time, urllib.request, urllib.parse

SID = "6992b11d1f6494bacadcbd74"
E1 = "6992b1441f6494bacadcbd7a"
SHOW = "Infinity Nado"
SEASON, EP = 1, 1

SB = os.environ.get("KEY_20", "").strip().rstrip("/")
SBK = os.environ.get("KEY_21", "").strip()
BASE = os.environ.get("KEY_8", "https://api.kartoons.me/api").strip()
CH = int(os.environ.get("KEY_2", "0").strip())
API_ID = os.environ.get("KEY_16", "").strip()
API_HASH = os.environ.get("KEY_17", "").strip()
SESS = os.environ.get("KEY_18", "").strip()
WEB = os.environ.get("KEY_15", "").strip()
K9 = os.environ.get("KEY_9", "").strip()
G10 = os.environ.get("KEY_10", "").strip()
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0"

def log(m):
    print("[e1] " + m, flush=True)

def sb_json(url, method="GET", body=None):
    hdrs = {"apikey": SBK, "Authorization": f"Bearer {SBK}", "Content-Type": "application/json",
            "Prefer": "resolution=merge-duplicates"}
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers=hdrs)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode() or "null")

def sb_post(table, row):
    req = urllib.request.Request(SB + "/rest/v1/" + table,
        data=json.dumps(row).encode(), method="POST",
        headers={"apikey": SBK, "Authorization": f"Bearer {SBK}", "Content-Type": "application/json",
                 "Prefer": "resolution=merge-duplicates"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.status

def get_token():
    d = sb_json(SB + "/rest/v1/progress?select=state&id=eq.tk_voughtx_kts-up&limit=1")
    st = d[0]["state"] if d else {}
    toks = st.get("tokens") or []
    idx = int(st.get("idx") or 0)
    return toks[idx % len(toks)] if toks else ""

def api(path, timeout=40):
    req = urllib.request.Request(BASE + path, headers={
        "User-Agent": UA, "Accept": "application/json",
        "Origin": "https://kartoons.me/", "Referer": "https://kartoons.me/",
        "Authorization": "Bearer " + TOK, "X-Challenge-Token": TOK})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())

def fetch(url, timeout=60):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Referer": "https://kartoons.me/", "Origin": "https://kartoons.me/"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()

def dec_gcm(enc):
    try:
        from Crypto.Cipher import AES
    except Exception:
        os.system(f"{sys.executable} -m pip install -q pycryptodome")
        from Crypto.Cipher import AES
    import base64, hashlib
    s = enc[5:] if enc.startswith("enc2:") else enc
    raw = b64u(s)
    iv, body = raw[:12], raw[12:]
    key = hashlib.sha256(G10.encode()).digest()
    ct, tag = body[:-16], body[-16:]
    c = AES.new(key, AES.MODE_GCM, nonce=iv)
    return c.decrypt_and_verify(ct, tag).decode("utf-8", "replace")

def b64u(s):
    b = s.replace("-", "+").replace("_", "/")
    b += "=" * ((4 - len(b) % 4) % 4)
    import base64
    return base64.b64decode(b)

def dec_cbc(url):
    try:
        from Crypto.Cipher import AES
        import base64
        raw = b64u(url)
        iv, ct = raw[:16], raw[16:]
        c = AES.new(K9.encode()[:32], AES.MODE_CBC, iv)
        pt = c.decrypt(ct)
        pad = pt[-1]
        if 1 <= pad <= 16 and pt[-pad:] == bytes([pad]) * pad:
            pt = pt[:-pad]
        return pt.decode("utf-8", "replace")
    except Exception:
        return url

def dec_url(s):
    if not s:
        return s
    if s.startswith("enc2:"):
        return dec_gcm(s)
    if s.startswith("http"):
        return s
    if re.fullmatch(r"[A-Za-z0-9_\-+/=]+", s or ""):
        dec = dec_cbc(s)
        if dec != s and dec.startswith("http"):
            return dec
    return s

def pow_solve(nonce, bits):
    import hashlib
    zeros = "0" * (bits // 4)
    extra = bits % 4
    s = 0
    while True:
        hh = hashlib.sha256(f"{nonce}:{s}".encode()).hexdigest()
        if hh.startswith(zeros):
            if extra:
                if int(hh[len(zeros)], 16) < (1 << (4 - extra)):
                    return str(s)
            else:
                return str(s)
        s += 1

def main():
    global TOK
    TOK = get_token()
    log("token tail " + TOK[-6:] + " | api_id len " + str(len(API_ID)) + " | sess len " + str(len(SESS)))

    # 1) episode detail (meta)
    j = api(f"/shows/episode/{E1}")
    d = j.get("data") or j
    title = d.get("title") or ""
    ep_num = d.get("episodeNumber") or EP
    log(f"ep meta title_len={len(title)} epNum={ep_num}")

    # 2) links with PoW
    content = "episode:" + E1
    ch = api("/challenge/pow?content=" + urllib.parse.quote(content))
    cd = ch.get("data") or {}
    hdrs = {}
    if cd.get("enabled") is not False:
        nonce, bits = cd.get("nonce"), cd.get("bits", 16)
        sol = pow_solve(nonce, bits)
        hdrs = {"X-Pow-Nonce": nonce, "X-Pow-Solution": sol, "X-Challenge-Retry": "true"}
        log(f"pow solved bits={bits} sol_len={len(sol)}")
    lreq = urllib.request.Request(BASE + f"/shows/episode/{E1}/links", headers={
        "User-Agent": UA, "Accept": "application/json",
        "Origin": "https://kartoons.me/", "Referer": "https://kartoons.me/",
        "Authorization": "Bearer " + TOK, "X-Challenge-Token": TOK, **hdrs})
    with urllib.request.urlopen(lreq, timeout=30) as r:
        lj = json.loads(r.read().decode())
    ld = lj.get("data") or lj
    lns = ld.get("links") if isinstance(ld, dict) else ld
    links = []
    for ln in (lns or []):
        if not isinstance(ln, dict) or not ln.get("url"):
            continue
        u = dec_url(ln["url"])
        if re.search(r"(playlist|\.m3u8)", u, re.I):
            links.append(u)
        else:
            log("non-playlist link: " + u[:50])
    log("playlist links: " + str(len(links)))
    if not links:
        log("FAIL no playlist")
        return

    # 2) master + best variant
    master = None
    for u in links:
        try:
            body = fetch(u).decode()
            if body.lstrip().startswith("#EXTM3U"):
                master = body
                log("master got len " + str(len(body)))
                break
        except Exception as ex:
            log("master fail " + str(ex)[:60])
    if master is None:
        log("FAIL no master")
        return

    # 3) local_convert: decrypt enc2 -> parallel download -> remux
    import subprocess, concurrent.futures
    out_lines = []
    for ln in master.splitlines():
        ln2 = ln.strip()
        if ln2.startswith("enc2:"):
            dec = dec_gcm(ln2)
            out_lines.append(dec if dec.startswith("http") else ln)
        elif ln2.startswith("#EXT-X-MAP:"):
            m = re.search(r'URI="([^"]+)"', ln2)
            if m and m.group(1).startswith("enc2:"):
                dec = dec_gcm(m.group(1))
                out_lines.append(ln2.replace(m.group(1), dec))
            else:
                out_lines.append(ln)
        else:
            out_lines.append(ln)
    ptxt = "\n".join(out_lines)
    media = [l for l in out_lines if l.startswith("http") and not l.startswith("#")]
    log(f"decrypted media lines: {len(media)}")
    if not ptxt.startswith("#EXTM3U") or "enc2:" in ptxt or not media:
        log("FAIL playlist invalid")
        return

    seg_dir = "/tmp/e1_segs"
    subprocess.run(f"rm -rf {seg_dir}", shell=True, capture_output=True)
    os.makedirs(seg_dir, exist_ok=True)
    jobs = []
    for ln in out_lines:
        l = ln.strip()
        if l.startswith("#EXT-X-MAP:"):
            m = re.search(r'URI="([^"]+)"', l)
            if m:
                u = m.group(1)
                if not u.startswith("http"):
                    u = urllib.parse.urljoin(links[0], u)
                jobs.append(("map", u, l, m.group(1)))
            else:
                jobs.append(("pass", None, ln, None))
        elif l.startswith("http"):
            jobs.append(("seg", l, None, None))
        else:
            jobs.append(("pass", None, ln, None))

    def dl(j):
        kind, u, orig, mapu = j
        if kind == "pass":
            return j, True, b""
        try:
            req = urllib.request.Request(u, headers={"User-Agent": UA, "Referer": "https://kartoons.me/", "Origin": "https://kartoons.me/"})
            with urllib.request.urlopen(req, timeout=60) as r:
                b = r.read()
            if kind == "map" and b and len(b) > 100:
                return j, True, b
            if kind == "seg" and b and len(b) > 188 and b[:1] != b"<":
                return j, True, b
            return j, False, b""
        except Exception as ex:
            return j, False, str(ex)[:40]

    dl_map = {}
    fails = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
        for jj, ok, b in ex.map(dl, jobs):
            if not ok:
                fails.append(jj[1][:50] if jj[1] else "?")
                break
            dl_map[id(jj)] = b
    if fails:
        log("FAIL segment download: " + fails[0])
        return
    final_lines = []
    seg_i = 0
    for jj in jobs:
        kind, u, orig, mapu = jj
        if kind == "pass":
            final_lines.append(orig)
            continue
        b = dl_map.get(id(jj))
        if kind == "map":
            fp = f"{seg_dir}/init_{seg_i}"; seg_i += 1
            open(fp, "wb").write(b)
            final_lines.append(orig.replace(mapu, fp))
        else:
            fp = f"{seg_dir}/seg_{seg_i}"; seg_i += 1
            open(fp, "wb").write(b)
            final_lines.append(fp)
    log(f"segments saved: {seg_i}")
    rp = "/tmp/e1_play.m3u8"
    open(rp, "w").write("\n".join(final_lines))
    out = f"/tmp/e1_{E1[-6:]}.mp4"
    r = subprocess.run(["ffmpeg", "-y", "-allowed_extensions", "ALL", "-i", rp,
                        "-c", "copy", "-bsf:a", "aac_adtstoasc", out],
                       capture_output=True, text=True, timeout=1500)
    log("ffmpeg rc " + str(r.returncode))
    if r.returncode != 0:
        log("ffmpeg err " + r.stderr[-200:].replace("\n", " "))
        return
    sz = os.path.getsize(out)
    log("file size " + str(sz))
    if sz < 500000:
        log("FAIL too small")
        return

    # 4) probe
    try:
        pr = subprocess.run(["ffprobe", "-v", "quiet", "-print_format", "json", "-show_streams",
                             "-select_streams", "v:0", out], capture_output=True, text=True, timeout=60)
        s0 = json.loads(pr.stdout)["streams"][0]
        dur = float(s0.get("duration", 0)); w = int(s0.get("width", 0)); h = int(s0.get("height", 0))
        log(f"probe dur={dur:.0f} {w}x{h}")
    except Exception:
        dur = w = h = 0

    # 5) thumbnail (episode image se)
    thumb = None
    img = d.get("image") or ""
    if img:
        try:
            tpath = "/tmp/e1_thumb.jpg"
            raw = fetch(img)
            open(tpath, "wb").write(raw)
            from PIL import Image
            im = Image.open(tpath); im.thumbnail((320, 320))
            if im.mode != "RGB": im = im.convert("RGB")
            im.save(tpath, "JPEG", quality=80)
            thumb = tpath
            log("thumb ok")
        except Exception as ex:
            log("thumb fail " + str(ex)[:60])

    # 6) post via telethon (user session)
    from telethon import TelegramClient
    from telethon.sessions import StringSession
    from telethon.tl.types import DocumentAttributeFilename
    import asyncio

    q = "1080p" if (w and h and h >= 1080) else ("720p" if (w and h and h >= 720) else "")
    fname = re.sub(r'[^A-Za-z0-9 _.-]', '', (title or SHOW))[:80] + f" S{SEASON}E{EP}" + (f" {q}" if q else "") + ".mp4"
    web = (WEB + "episodeId=" + E1) if WEB else ""
    dom = "Kartoons"
    cap = f"<b>{re.sub(r'[<>&]', lambda m: {'<':'&lt;','>':'&gt;','&':'&amp;'}[m.group()], title)}</b>\n" \
          f"<b>{re.sub(r'[<>&]', lambda m: {'<':'&lt;','>':'&gt;','&':'&amp;'}[m.group()], SHOW)} · S{SEASON}-E{EP}</b>\n" \
          "──────────────────\n" \
          + (f"⚙️ Quality: <b>{q}</b>\n" if q else "") + \
          "💬 Language: <b>Hindi</b>\n" \
          + (f"📂 Size: <b>{sz//1000000} MB</b>\n" if sz else "") + \
          (f"🕐 Duration: <b>{int(dur/60)} min</b>\n" if dur else "") + \
          "🗳️ Category: <b>Show</b>\n──────────────────\n" \
          + (f"🎯 <b><a href=\"{web}\">{dom}</a></b>" if web else "")

    async def post():
        client = TelegramClient(StringSession(SESS), int(API_ID), API_HASH)
        await client.connect()
        try:
            ent = await client.get_entity(CH)
            msg = await client.send_file(ent, out, force_document=True, caption=cap,
                                         parse_mode="html", thumb=thumb,
                                         attributes=[DocumentAttributeFilename(file_name=fname)])
            return msg.id
        finally:
            await client.disconnect()

    mid = asyncio.run(post())
    log("posted mid=" + str(mid))

    # 7) DB row
    try:
        st2 = sb_post("episodes", [{"id": E1, "mid": mid, "season": SEASON, "episode": EP,
                                    "show": SHOW, "at": int(time.time())}])
        log("db insert " + str(st2))
    except Exception as ex:
        log("db fail " + str(ex)[:80])

    # 8) poster (showlist se) + pin
    try:
        d2 = sb_json(SB + "/rest/v1/progress?select=state&id=eq.showlist&limit=1")
        ent2 = None
        for e in d2[0]["state"]["shows"]:
            if e.get("name") == SHOW:
                ent2 = e; break
        poster_url = (ent2 or {}).get("poster") or ""
        pcap = f"<b>{SHOW}</b>\nTotal • S1 | Ep{ent2.get('total') if ent2 else 26}"
        if poster_url:
            pimg = "/tmp/e1_poster.jpg"
            open(pimg, "wb").write(fetch(poster_url))
            async def post_poster():
                client = TelegramClient(StringSession(SESS), int(API_ID), API_HASH)
                await client.connect()
                try:
                    entx = await client.get_entity(CH)
                    m2 = await client.send_file(entx, pimg, caption=pcap, parse_mode="html")
                    try:
                        await client.pin_message(entx, m2.id)
                        log("poster pinned")
                    except Exception:
                        log("poster pin fail")
                    return m2.id
                finally:
                    await client.disconnect()
            pmid = asyncio.run(post_poster())
            log("poster mid=" + str(pmid))
    except Exception as ex:
        log("poster fail " + str(ex)[:80])

    log("DONE")

if __name__ == "__main__":
    main()
