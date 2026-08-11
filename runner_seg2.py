#!/usr/bin/env python3
"""runner_seg2.py — Mushoku CDN segment direct vs relay test."""
import urllib.request, urllib.parse, hashlib, json, re, base64, subprocess, os, sys
subprocess.run("pip install -q pycryptodome", shell=True, check=False)
from Crypto.Cipher import AES

API = "https://api.kartoons.me/api"
REF = "https://kartoons.me/"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
SB_URL = os.environ.get("KEY_20", "").strip().rstrip("/")
SB_KEY = os.environ.get("KEY_21", "").strip()
GCM = os.environ.get("KEY_10", "").strip()
KEY9 = "bca9e0df1a5abb32906ca3f63ac04cef"
R = "https://kts-url.gobinog.workers.dev/relay"
RELAY_KEY = "ktsrelay2026"

TOKENS = []
try:
    req = urllib.request.Request(f"{SB_URL}/rest/v1/progress?select=state&id=eq.tk_voughtx_kts-up&limit=1",
        headers={"apikey": SB_KEY, "Authorization": f"Bearer {SB_KEY}"})
    with urllib.request.urlopen(req, timeout=20) as r:
        arr = json.loads(r.read().decode())
    TOKENS = ((arr[0].get("state") or {}).get("tokens")) or []
    print("[ok] pool tokens:", len(TOKENS), flush=True)
except Exception as e:
    print("[!] pool fail:", str(e)[:60], flush=True)

def relay(path, hdrs=None):
    h = {"User-Agent": UA, "Accept": "*/*", "Origin": REF.rstrip("/"), "Referer": REF}
    if hdrs: h.update(hdrs)
    q = urllib.parse.urlencode([("path", path)] + [(f"h_{k}", v) for k, v in h.items()])
    rq = urllib.request.Request(R + "?" + q, headers={"X-KTS-Key": RELAY_KEY, "User-Agent": UA})
    try:
        with urllib.request.urlopen(rq, timeout=50) as resp:
            return resp.status, resp.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()

def direct_bin(url, hdrs=None, timeout=30):
    h = {"User-Agent": UA, "Accept": "*/*", "Origin": REF.rstrip("/"), "Referer": REF}
    if hdrs: h.update(hdrs)
    rq = urllib.request.Request(url, headers=h)
    try:
        with urllib.request.urlopen(rq, timeout=timeout) as resp:
            return resp.status, resp.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()
    except Exception as e:
        return 0, str(e).encode()

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
    b = s.replace("-", "+").replace("_", "/"); b += "=" * ((4 - len(b) % 4) % 4)
    return base64.b64decode(b)

def dec_cbc(url):
    raw = b64u(url); iv, ct = raw[:16], raw[16:]
    c = AES.new(KEY9.encode()[:32], AES.MODE_CBC, iv)
    pt = c.decrypt(ct); pad = pt[-1]
    if 1 <= pad <= 16 and pt[-pad:] == bytes([pad]) * pad: pt = pt[:-pad]
    return pt.decode("utf-8", "replace")

def dec_gcm(enc):
    s = enc[5:] if enc.startswith("enc2:") else enc
    raw = b64u(s); iv, body = raw[:12], raw[12:]
    key = hashlib.sha256(GCM.encode()).digest()
    ct, tag = body[:-16], body[-16:]
    for nv in (iv, bytes(12)):
        try:
            c = AES.new(key, AES.MODE_GCM, nonce=nv)
            return c.decrypt_and_verify(ct, tag).decode("utf-8", "replace")
        except Exception:
            continue
    return ""

EID = "684672cb333e6d02d74c2450"  # Mushoku S1E20
tok = TOKENS[0] if TOKENS else ""
st, body = relay("/challenge/pow?content=" + urllib.parse.quote("episode:" + EID))
ch = json.loads(body.decode()).get("data") or {}
hdrs = {"X-Challenge-Token": tok, "Authorization": f"Bearer {tok}", "X-Challenge-Retry": "true"}
if ch.get("nonce"):
    hdrs["X-Pow-Nonce"] = ch["nonce"]
    hdrs["X-Pow-Solution"] = solve_pow(ch["nonce"], ch.get("bits", 16))
st2, body2 = relay(f"/shows/episode/{EID}/links", hdrs)
print("links via relay:", st2, flush=True)
if st2 != 200:
    print("  body:", body2[:150], flush=True); sys.exit(1)
data = json.loads(body2.decode()).get("data") or {}
urls = []
for ln in (data.get("links") or []):
    if not isinstance(ln, dict) or not ln.get("url"): continue
    u = ln["url"]
    try:
        dec = dec_cbc(u)
        if dec.startswith("http"): u = dec
    except Exception: pass
    if re.search(r"(playlist|\.m3u8)", u, re.I): urls.append(u)
print("playlist links:", len(urls), flush=True)

master = b""
for u in urls:
    st3, b3 = relay(u)
    if st3 == 200 and b"#EXTM3U" in b3[:200]:
        master = b3; print("master via relay:", len(master), "enc2:", b"enc2:" in master, flush=True); break
    print("master relay fail:", st3, b3[:60], flush=True)

segs = []
for ln in master.decode("utf-8", "replace").splitlines():
    ln2 = ln.strip()
    if ln2.startswith("enc2:"):
        d = dec_gcm(ln2)
        if d.startswith("http"): segs.append(d)
    elif ln2.startswith("http") and not ln2.startswith("#"):
        segs.append(ln2)
print("segments:", len(segs), flush=True)

for i, su in enumerate(segs[:6]):
    st4, b4 = direct_bin(su)
    print(f"seg{i} DIRECT: {st4} len={len(b4)} mpegts={b4[:2]==b'\\x47'} head={b4[:20]!r}", flush=True)
    if st4 != 200 or b4[:2] != b"\x47":
        st5, b5 = relay(su)
        print(f"seg{i} RELAY : {st5} len={len(b5)} mpegts={b5[:2]==b'\\x47'}", flush=True)
print("[done]", flush=True)
