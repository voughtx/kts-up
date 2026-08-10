#!/usr/bin/env python3
"""debug_seg.py — COTE S1E4 link build -> master -> enc2 decrypt -> segment download
(relay + direct) -> first-bytes hexdump -> exact ffmpeg remux stderr.
Diagnostic only — kuch upload nahi karta."""
import os, sys, json, re, base64, hashlib, subprocess, urllib.request, urllib.parse, time
from Crypto.Cipher import AES

API = "https://api.kartoons.me/api"
REF = "https://kartoons.me/"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
SB_URL = os.environ.get("KEY_20", "").strip().rstrip("/")
SB_KEY = os.environ.get("KEY_21", "").strip()
GCM = os.environ.get("KEY_10", "").strip()
KEY9 = "bca9e0df1a5abb32906ca3f63ac04cef"
EID = "6858e89f37456fd21e5de450"  # COTE S1E4
RELAY = "https://scroll-maintaining-scott-share.trycloudflare.com"  # naya tunnel
RELAY_KEY = "ktsrelay2026"

# ---- token from supabase pool ----
TOKEN = ""
try:
    req = urllib.request.Request(f"{SB_URL}/rest/v1/progress?select=state&id=eq.tk_voughtx_kts-up&limit=1",
        headers={"apikey": SB_KEY, "Authorization": f"Bearer {SB_KEY}"})
    with urllib.request.urlopen(req, timeout=20) as r:
        arr = json.loads(r.read().decode())
    toks = ((arr[0].get("state") or {}).get("tokens")) or [] if arr else []
    if toks:
        TOKEN = toks[0]
        print(f"[ok] pool token ...{TOKEN[-6:]}", flush=True)
except Exception as e:
    print("[!] pool fetch fail:", str(e)[:80], flush=True)

def api(path, hdrs=None, data=None, timeout=30):
    h = {"User-Agent": UA, "Accept": "application/json", "Origin": REF.rstrip("/"), "Referer": REF}
    if hdrs: h.update(hdrs)
    body = None
    if data is not None:
        body = json.dumps(data).encode(); h["Content-Type"] = "application/json"
    r = urllib.request.Request(API + path, data=body, headers=h, method="POST" if body else "GET")
    try:
        with urllib.request.urlopen(r, timeout=timeout) as resp:
            return resp.status, resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")[:400]
    except Exception as e:
        return 0, str(e)[:200]

def solve_pow(nonce, bits):
    z = "0" * (bits // 4); extra = bits % 4; s = 0
    while True:
        hh = hashlib.sha256(f"{nonce}:{s}".encode()).hexdigest()
        if hh.startswith(z):
            if extra:
                if int(hh[len(z)], 16) < (1 << (4 - extra)): return str(s)
            else: return str(s)
        s += 1

def b64u(s):
    b = s.replace("-", "+").replace("_", "/")
    b += "=" * ((4 - len(b) % 4) % 4)
    return base64.b64decode(b)

def dec_cbc(url):
    raw = b64u(url); iv, ct = raw[:16], raw[16:]
    c = AES.new(KEY9.encode()[:32], AES.MODE_CBC, iv)
    pt = c.decrypt(ct); pad = pt[-1]
    if 1 <= pad <= 16 and pt[-pad:] == bytes([pad]) * pad:
        pt = pt[:-pad]
    return pt.decode("utf-8", "replace")

def dec_gcm(enc):
    s = enc[5:] if enc.startswith("enc2:") else enc
    raw = b64u(s); iv, body = raw[:12], raw[12:]
    key = hashlib.sha256(GCM.encode()).digest()
    ct, tag = body[:-16], body[-16:]
    try:
        c = AES.new(key, AES.MODE_GCM, nonce=iv)
        return c.decrypt_and_verify(ct, tag).decode("utf-8", "replace")
    except Exception:
        try:
            c = AES.new(key, AES.MODE_GCM, nonce=bytes(12))
            return c.decrypt_and_verify(ct, tag).decode("utf-8", "replace")
        except Exception as e:
            return ""

def fetch(url, via_relay=False, hdrs=None):
    h = {"User-Agent": UA, "Accept": "*/*", "Origin": REF.rstrip("/"), "Referer": REF}
    if hdrs: h.update(hdrs)
    if via_relay:
        q = urllib.parse.urlencode([("path", url)] + [(f"h_{k}", v) for k, v in h.items()])
        rurl = RELAY + "?" + q
        rh = {"X-KTS-Key": RELAY_KEY}
        try:
            r = urllib.request.Request(rurl, headers=rh)
            with urllib.request.urlopen(r, timeout=60) as resp:
                return resp.status, resp.read()
        except urllib.error.HTTPError as e:
            return e.code, e.read()
        except Exception as e:
            return 0, str(e).encode()
    try:
        r = urllib.request.Request(url, headers=h)
        with urllib.request.urlopen(r, timeout=60) as resp:
            return resp.status, resp.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()
    except Exception as e:
        return 0, str(e).encode()

# ---- 1. links ----
content = "episode:" + EID
st, body = api("/challenge/pow?content=" + urllib.parse.quote(content))
ch = (json.loads(body).get("data") or {}) if st == 200 else {}
print("[*] challenge:", st, "nonce?", bool(ch.get("nonce")), "bits:", ch.get("bits"), flush=True)
ph = {}
if ch.get("nonce"):
    sol = solve_pow(ch["nonce"], ch.get("bits", 16))
    ph = {"X-Pow-Nonce": ch["nonce"], "X-Pow-Solution": sol}
hdrs = {"X-Challenge-Token": TOKEN, "Authorization": f"Bearer {TOKEN}", "X-Challenge-Retry": "true"}
hdrs.update(ph)
st, body = api(f"/shows/episode/{EID}/links", hdrs=hdrs)
print("[*] links:", st, flush=True)
if st != 200:
    print("  body:", body[:300], flush=True); sys.exit(1)
data = json.loads(body).get("data") or {}
links = [ln for ln in (data.get("links") or []) if isinstance(ln, dict) and ln.get("url")]
print("[*] raw links:", len(links), flush=True)
urls = []
for ln in links:
    u = ln["url"]
    if u.startswith("enc2:"):
        dec = dec_gcm(u)
        print("  enc2-link dec:", "OK" if dec else "FAIL", flush=True)
        if dec: urls.append(dec)
    else:
        try:
            dec = dec_cbc(u)
            if dec.startswith("http"): urls.append(dec)
            else: urls.append(u)
        except Exception:
            urls.append(u)
urls = [u for u in urls if re.search(r"(playlist|\.m3u8)", u, re.I)]
print("[*] playlist links:", len(urls), flush=True)
for u in urls: print("  ", u[:90], flush=True)

# ---- 2. master + segments ----
for url in urls:
    st2, b2 = fetch(url, via_relay=False)
    print(f"\n[*] master direct: {st2} len={len(b2)} m3u8={'#EXTM3U' in (b2.decode(errors='replace') if isinstance(b2, bytes) else str(b2))}", flush=True)
    if st2 != 200: continue
    text = b2.decode("utf-8", "replace")
    segs = []
    for ln in text.splitlines():
        ln = ln.strip()
        if ln.startswith("enc2:"):
            d = dec_gcm(ln)
            if d: segs.append(d)
    print("[*] decrypted segments:", len(segs), flush=True)
    if not segs: continue
    for i, su in enumerate(segs[:3]):
        print(f"\n--- seg {i} ---", flush=True)
        print("  url:", su[:110], flush=True)
        # relay first (runner's path), then direct
        st3, b3 = fetch(su, via_relay=True)
        print(f"  via relay: {st3} len={len(b3)}", flush=True)
        if b3[:2] == b"\x47":
            print("  MAGIC: MPEG-TS (0x47) OK!!", flush=True)
        else:
            print("  first bytes:", b3[:40], flush=True)
            print("  starts html?", b3[:1] in (b"<", b"{"), flush=True)
        st4, b4 = fetch(su, via_relay=False)
        print(f"  direct: {st4} len={len(b4)}", flush=True)
        if b4[:2] == b"\x47":
            print("  direct MAGIC: MPEG-TS OK!!", flush=True)
        else:
            print("  direct first bytes:", b4[:40], flush=True)
        if b3[:2] == b"\x47":
            # save + ffmpeg test with playlist
            os.makedirs("/tmp/kts_segs_dbg", exist_ok=True)
            for j, su2 in enumerate(segs[:5]):
                st5, b5 = fetch(su2, via_relay=True)
                if st5 == 200 and len(b5) > 10000:
                    open(f"/tmp/kts_segs_dbg/seg_{j}", "wb").write(b5)
            open("/tmp/kts_segs_dbg/play.m3u8", "w").write(
                "#EXTM3U\n#EXT-X-VERSION:3\n#EXT-X-TARGETDURATION:12\n"
                + "".join(f"#EXTINF:12.0,\n/tmp/kts_segs_dbg/seg_{j}\n" for j in range(5))
                + "#EXT-X-ENDLIST\n")
            rr = subprocess.run(
                "ffmpeg -y -hide_banner -loglevel error -protocol_whitelist file,http,https,tcp,tls,crypto,data -max_reload 3 -i /tmp/kts_segs_dbg/play.m3u8 -c copy -bsf:a aac_adtstoasc -movflags +faststart /tmp/kts_segs_dbg/out.mp4",
                shell=True, capture_output=True, text=True, timeout=300)
            print("\n[*] ffmpeg rc:", rr.returncode, flush=True)
            print("  stderr:", rr.stderr[-500:], flush=True)
            import os as _o
            print("  out exists:", _o.path.exists("/tmp/kts_segs_dbg/out.mp4"), flush=True)
            break
    break
print("\n[done]", flush=True)
