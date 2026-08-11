#!/usr/bin/env python3
"""runner_seg4.py — DECISIVE: segment fetch via 4 methods compare (truncation test).
urllib HTTP/1.1 vs curl HTTP/2 vs Range header vs worker relay."""
import urllib.request, urllib.parse, hashlib, json, re, base64, subprocess, os, sys, time
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
print("[*] KEY_10 len:", len(GCM), flush=True)

TOKENS = []
try:
    req = urllib.request.Request(f"{SB_URL}/rest/v1/progress?select=state&id=eq.tk_voughtx_kts-up&limit=1",
        headers={"apikey": SB_KEY, "Authorization": f"Bearer {SB_KEY}"})
    with urllib.request.urlopen(req, timeout=20) as r:
        arr = json.loads(r.read().decode())
    TOKENS = ((arr[0].get("state") or {}).get("tokens")) or []
except Exception:
    pass

def relay(path, hdrs=None, timeout=60):
    h = {"User-Agent": UA, "Accept": "*/*", "Origin": REF.rstrip("/"), "Referer": REF}
    if hdrs: h.update(hdrs)
    q = urllib.parse.urlencode([("path", path)] + [(f"h_{k}", v) for k, v in h.items()])
    rq = urllib.request.Request(R + "?" + q, headers={"X-KTS-Key": RELAY_KEY, "User-Agent": UA})
    try:
        with urllib.request.urlopen(rq, timeout=timeout) as resp:
            return resp.status, resp.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()
    except Exception as e:
        return 0, str(e).encode()

def fetch_urllib(url, extra_headers=None):
    h = {"User-Agent": UA, "Accept": "*/*", "Origin": REF.rstrip("/"), "Referer": REF}
    if extra_headers: h.update(extra_headers)
    rq = urllib.request.Request(url, headers=h)
    try:
        with urllib.request.urlopen(rq, timeout=30) as resp:
            return resp.status, resp.read(), dict(resp.headers)
    except urllib.error.HTTPError as e:
        return e.code, e.read(), dict(e.headers)
    except Exception as e:
        return 0, str(e).encode(), {}

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

def get_seg_url(eid, want_host=None):
    """links -> master -> variant -> media -> first segment URL. Returns (seg_url, cdn_host)."""
    for attempt in range(6):
        tok = TOKENS[attempt % len(TOKENS)] if TOKENS else ""
        st, body = relay("/challenge/pow?content=" + urllib.parse.quote("episode:" + eid))
        ch = json.loads(body.decode()).get("data") or {}
        hdrs = {"X-Challenge-Token": tok, "Authorization": f"Bearer {tok}", "X-Challenge-Retry": "true"}
        if ch.get("nonce"):
            hdrs["X-Pow-Nonce"] = ch["nonce"]
            hdrs["X-Pow-Solution"] = solve_pow(ch["nonce"], ch.get("bits", 16))
        st2, body2 = relay(f"/shows/episode/{eid}/links", hdrs)
        if st2 != 200: continue
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
        for u in urls:
            st3, b3 = relay(u)
            if st3 != 200 or b"#EXTM3U" not in b3[:200]: continue
            master = b3.decode("utf-8", "replace")
            variant = ""
            for ln in master.splitlines():
                if ln.strip().startswith("enc2:"):
                    d = dec_gcm(ln.strip())
                    if d.startswith("http"): variant = d; break
            if not variant: continue
            st4, b4 = relay(variant)
            if st4 != 200: continue
            media = b4.decode("utf-8", "replace")
            for ln in media.splitlines():
                ln2 = ln.strip()
                if ln2.startswith("enc2:"):
                    d = dec_gcm(ln2)
                    if d.startswith("http"): return d, urllib.parse.urlparse(d).hostname
                elif ln2.startswith("http") and not ln2.startswith("#"):
                    return ln2, urllib.parse.urlparse(ln2).hostname
        time.sleep(3)
    return None, None

EID = "684672cb333e6d02d74c2450"  # Mushoku S1E20
print("== getting segment URL (retry till v12/v24/v76-style host) ==", flush=True)
seg, host = None, None
for i in range(8):
    seg, host = get_seg_url(EID)
    if not seg: break
    print(f"  attempt {i+1}: host={host}", flush=True)
    if host and ("v12" in host or "v24" in host or "v76" in host or "v33" in host or "v53" in host or "v80" in host or "v36" in host or "v62" in host):
        break
if not seg:
    print("NO SEG URL", flush=True); sys.exit(1)
print(f"SEG URL: {seg[:90]}", flush=True)
print(f"HOST: {host}", flush=True)

# Method 1: urllib HTTP/1.1
t0 = time.time()
st, b, hdrs1 = fetch_urllib(seg)
print(f"\n[1] urllib HTTP/1.1: {st} len={len(b)} mpegts={b[:2]==b'\\x47'} {time.time()-t0:.1f}s", flush=True)
print(f"    headers: content-length={hdrs1.get('Content-Length')} content-range={hdrs1.get('Content-Range')} transfer-enc={hdrs1.get('Transfer-Encoding')}", flush=True)

# Method 2: urllib + Range header
t0 = time.time()
st, b, hdrs2 = fetch_urllib(seg, {"Range": "bytes=0-"})
print(f"[2] urllib + Range: {st} len={len(b)} mpegts={b[:2]==b'\\x47'} {time.time()-t0:.1f}s", flush=True)
print(f"    headers: content-length={hdrs2.get('Content-Length')} content-range={hdrs2.get('Content-Range')}", flush=True)

# Method 3: curl (HTTP/2)
t0 = time.time()
r = subprocess.run(["curl", "-s", "--http2", "-m", "30", "-H", f"User-Agent: {UA}",
    "-H", f"Origin: {REF.rstrip('/')}", "-H", f"Referer: {REF}", "-o", "/tmp/seg_c2.bin", "-w", "%{http_code} %{size_download}", seg],
    capture_output=True, text=True)
sz = os.path.getsize("/tmp/seg_c2.bin") if os.path.exists("/tmp/seg_c2.bin") else 0
b3 = open("/tmp/seg_c2.bin","rb").read() if sz else b""
print(f"[3] curl HTTP/2: {r.stdout} mpegts={b3[:2]==b'\\x47'} {time.time()-t0:.1f}s", flush=True)

# Method 4: worker relay
t0 = time.time()
st, b4 = relay(seg)
print(f"[4] worker relay: {st} len={len(b4)} mpegts={b4[:2]==b'\\x47'} {time.time()-t0:.1f}s", flush=True)

print("[done]", flush=True)
