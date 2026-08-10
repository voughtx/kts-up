#!/usr/bin/env python3
"""diag_quality.py — Miraculous S5E15-25 asli video resolution detect.
Har episode ka pehla segment download + ffprobe height. Diagnostic only."""
import os, sys, json, re, base64, hashlib, subprocess, urllib.request, urllib.parse
subprocess.run("pip install -q pycryptodome", shell=True, check=False)
from Crypto.Cipher import AES

API = "https://api.kartoons.me/api"
REF = "https://kartoons.me/"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
SB_URL = os.environ.get("KEY_20", "").strip().rstrip("/")
SB_KEY = os.environ.get("KEY_21", "").strip()
GCM = os.environ.get("KEY_10", "").strip()
KEY9 = "bca9e0df1a5abb32906ca3f63ac04cef"
RELAY_KEY = "ktsrelay2026"
print("[*] KEY_10 len:", len(GCM), flush=True)

RELAYS = []
try:
    req = urllib.request.Request(f"{SB_URL}/rest/v1/progress?select=state&id=eq.relay&limit=1",
        headers={"apikey": SB_KEY, "Authorization": f"Bearer {SB_KEY}"})
    with urllib.request.urlopen(req, timeout=20) as r:
        arr = json.loads(r.read().decode())
    RELAYS = ((arr[0].get("state") or {}).get("urls")) or [] if arr else []
    print("[*] relays:", [x.get("url","")[:30] for x in RELAYS], flush=True)
except Exception as e:
    print("[!] relay fetch fail:", str(e)[:60], flush=True)

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
    print("[!] pool fetch fail:", str(e)[:60], flush=True)

def api(path, hdrs=None, timeout=30):
    h = {"User-Agent": UA, "Accept": "application/json", "Origin": REF.rstrip("/"), "Referer": REF}
    if hdrs: h.update(hdrs)
    r = urllib.request.Request(API + path, headers=h)
    try:
        with urllib.request.urlopen(r, timeout=timeout) as resp:
            return resp.status, resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")[:200]

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
    for nv in (iv, bytes(12)):
        try:
            c = AES.new(key, AES.MODE_GCM, nonce=nv)
            return c.decrypt_and_verify(ct, tag).decode("utf-8", "replace")
        except Exception:
            continue
    return ""

def req_bin(path):
    url = path if path.startswith("http") else API + path
    h = {"User-Agent": UA, "Accept": "*/*", "Origin": REF.rstrip("/"), "Referer": REF}
    for r2 in RELAYS:
        try:
            if r2.get("type") == "prefix":
                rurl = r2["url"] + url
            else:
                rurl = r2["url"] + "?" + urllib.parse.urlencode([("path", url)] + [(f"h_{k}", v) for k, v in h.items()])
            rq = urllib.request.Request(rurl, headers={"X-KTS-Key": RELAY_KEY})
            with urllib.request.urlopen(rq, timeout=60) as resp:
                b = resp.read()
            if b[:1] == b"{":
                try:
                    if json.loads(b).get("error"): continue
                except Exception:
                    pass
            return b
        except Exception:
            continue
    try:
        rq = urllib.request.Request(url, headers=h)
        with urllib.request.urlopen(rq, timeout=45) as resp:
            return resp.read()
    except Exception:
        return b""

def ep_height(eid):
    """Return height of first video segment, or None."""
    content = "episode:" + eid
    st, body = api("/challenge/pow?content=" + urllib.parse.quote(content))
    ch = (json.loads(body).get("data") or {}) if st == 200 else {}
    ph = {}
    if ch.get("nonce"):
        ph = {"X-Pow-Nonce": ch["nonce"], "X-Pow-Solution": solve_pow(ch["nonce"], ch.get("bits", 16))}
    hdrs = {"X-Challenge-Token": TOKEN, "Authorization": f"Bearer {TOKEN}", "X-Challenge-Retry": "true"}
    hdrs.update(ph)
    st, body = api(f"/shows/episode/{eid}/links", hdrs=hdrs)
    if st != 200:
        return None, f"links {st}"
    data = json.loads(body).get("data") or {}
    urls = []
    for ln in (data.get("links") or []):
        if not isinstance(ln, dict) or not ln.get("url"): continue
        u = ln["url"]
        dec = dec_gcm(u) if u.startswith("enc2:") else dec_cbc(u)
        if dec.startswith("http"): u = dec
        if re.search(r"(playlist|\.m3u8)", u, re.I): urls.append(u)
    if not urls:
        return None, "no playlist"
    master = ""
    for url in urls:
        b2 = req_bin(url)
        if b2 and b"#EXTM3U" in b2[:200]:
            master = b2.decode("utf-8", "replace")
            break
    if not master:
        return None, "no master"
    segs = []
    for ln in master.splitlines():
        ln2 = ln.strip()
        if ln2.startswith("enc2:"):
            d = dec_gcm(ln2)
            if d.startswith("http"): segs.append(d)
        elif ln2.startswith("http") and not ln2.startswith("#"):
            segs.append(ln2)
        if len(segs) >= 4:
            break
    if not segs:
        return None, "no seg"
    blobs = []
    for i, seg in enumerate(segs):
        b3 = req_bin(seg)
        if not b3:
            continue
        blobs.append(b3)
        p = f"/tmp/q_seg_{i}.bin"
        open(p, "wb").write(b3)
        # probe single
        pr = subprocess.run(f"ffprobe -v error -select_streams v:0 -show_entries stream=height,width -of csv=p=0 {p}",
                            shell=True, capture_output=True, text=True, timeout=30)
        h = (pr.stdout or "").strip()
        if h and h != "N/A":
            return h, None
    # try combine init + media (fMP4)
    if len(blobs) >= 2:
        open("/tmp/q_comb.bin", "wb").write(b"".join(blobs))
        pr = subprocess.run(f"ffprobe -v error -select_streams v:0 -show_entries stream=height,width -of csv=p=0 /tmp/q_comb.bin",
                            shell=True, capture_output=True, text=True, timeout=30)
        h = (pr.stdout or "").strip()
        if h and h != "N/A":
            return h, None
    first = blobs[0][:16] if blobs else b""
    return None, f"no probe ({len(segs)} segs, first={first.hex()})"

# S5E15..E25 eids (Miraculous 68498e886ed2282cba655f24 → S5 ep eids)
EIDS = {
    15: "6849900e6ed2282cba655f34",
    16: "6849900e6ed2282cba655f35",
    17: "6849900e6ed2282cba655f36",
    18: "6849900e6ed2282cba655f37",
    19: "6849900e6ed2282cba655f38",
    20: "6849900e6ed2282cba655f39",
    21: "6849900e6ed2282cba655f3a",
    22: "6849900e6ed2282cba655f3b",
    23: "6849900e6ed2282cba655f3c",
    24: "6849900e6ed2282cba655f3d",
    25: "6849900e6ed2282cba655f3e",
}
for ep, eid in EIDS.items():
    try:
        h, err = ep_height(eid)
        print(f"S5E{ep}: {'HEIGHT='+h if h else 'ERR '+str(err)}", flush=True)
    except Exception as e:
        print(f"S5E{ep}: EXC {str(e)[:60]}", flush=True)
print("[done]", flush=True)
