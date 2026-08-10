#!/usr/bin/env python3
"""debug_seg2.py — EXACT _local_convert replication (app jaisa playlist + ffmpeg).
Runner pe KEY_10 hai to enc2 decrypt + segment download + playlist write + ffmpeg,
full stderr ke saath. Diagnostic only."""
import os, sys, json, re, base64, hashlib, subprocess, urllib.request, urllib.parse, time
subprocess.run("pip install -q pycryptodome", shell=True, check=False)
from Crypto.Cipher import AES

API = "https://api.kartoons.me/api"
REF = "https://kartoons.me/"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
SB_URL = os.environ.get("KEY_20", "").strip().rstrip("/")
SB_KEY = os.environ.get("KEY_21", "").strip()
GCM = os.environ.get("KEY_10", "").strip()
KEY9 = "bca9e0df1a5abb32906ca3f63ac04cef"
EID = "6858e89f37456fd21e5de450"
RELAY_KEY = "ktsrelay2026"
print("[*] KEY_10 len:", len(GCM), flush=True)

# relays from supabase (app jaisa)
RELAYS = []
try:
    req = urllib.request.Request(f"{SB_URL}/rest/v1/progress?select=state&id=eq.relay&limit=1",
        headers={"apikey": SB_KEY, "Authorization": f"Bearer {SB_KEY}"})
    with urllib.request.urlopen(req, timeout=20) as r:
        arr = json.loads(r.read().decode())
    RELAYS = ((arr[0].get("state") or {}).get("urls")) or [] if arr else []
    print("[*] relays:", [(x.get("type"), x.get("url","")[:40]) for x in RELAYS], flush=True)
except Exception as e:
    print("[!] relay fetch fail:", str(e)[:80], flush=True)

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

def api(path, hdrs=None, timeout=30):
    h = {"User-Agent": UA, "Accept": "application/json", "Origin": REF.rstrip("/"), "Referer": REF}
    if hdrs: h.update(hdrs)
    r = urllib.request.Request(API + path, headers=h)
    try:
        with urllib.request.urlopen(r, timeout=timeout) as resp:
            return resp.status, resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")[:400]

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

def req_bin(path, headers=None):
    """app _req_bin clone — relay chain + direct fallback"""
    url = path if path.startswith("http") else API + path
    h = {"User-Agent": UA, "Accept": "*/*", "Origin": REF.rstrip("/"), "Referer": REF}
    if headers: h.update(headers)
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
                    jb = json.loads(b)
                    if jb.get("error"):
                        print(f"  [relay] {r2.get('url','')[:30]} error body — next", flush=True)
                        continue
                except Exception:
                    pass
            return b
        except Exception as e:
            print(f"  [relay] {r2.get('url','')[:30]} fail {str(e)[:50]} — next", flush=True)
            continue
    try:
        rq = urllib.request.Request(url, headers=h)
        with urllib.request.urlopen(rq, timeout=45) as resp:
            return resp.read()
    except Exception as e:
        print("  [direct] fail:", str(e)[:60], flush=True)
        return b""

def req_text(path, headers=None):
    try:
        return req_bin(path, headers).decode("utf-8", "replace")
    except Exception:
        return ""

# ---- 1. links ----
content = "episode:" + EID
st, body = api("/challenge/pow?content=" + urllib.parse.quote(content))
ch = (json.loads(body).get("data") or {}) if st == 200 else {}
ph = {}
if ch.get("nonce"):
    ph = {"X-Pow-Nonce": ch["nonce"], "X-Pow-Solution": solve_pow(ch["nonce"], ch.get("bits", 16))}
hdrs = {"X-Challenge-Token": TOKEN, "Authorization": f"Bearer {TOKEN}", "X-Challenge-Retry": "true"}
hdrs.update(ph)
st, body = api(f"/shows/episode/{EID}/links", hdrs=hdrs)
print("[*] links:", st, flush=True)
if st != 200:
    sys.exit(1)
data = json.loads(body).get("data") or {}
urls = []
for ln in (data.get("links") or []):
    if not isinstance(ln, dict) or not ln.get("url"): continue
    u = ln["url"]
    dec = dec_gcm(u) if u.startswith("enc2:") else dec_cbc(u)
    if dec.startswith("http"): u = dec
    if re.search(r"(playlist|\.m3u8)", u, re.I): urls.append(u)
print("[*] playlist links:", len(urls), flush=True)

master_text = ""
for url in urls:
    st2, b2 = api(url, hdrs={"Accept": "*/*"})
    if st2 == 200 and "#EXTM3U" in b2:
        master_text = b2
        print("[*] master OK len:", len(b2), flush=True)
        break

# ---- 2. EXACT _local_convert clone ----
out_lines = []
for ln in master_text.splitlines():
    ln2 = ln.strip()
    if ln2.startswith("enc2:"):
        dec = dec_gcm(ln2)
        out_lines.append(dec if dec.startswith("http") else ln)
    elif ln2.startswith("#EXT-X-MAP:"):
        m = re.search(r'URI="([^"]+)"', ln2)
        if m and m.group(1).startswith("enc2:"):
            d2 = dec_gcm(m.group(1))
            out_lines.append(ln2.replace(m.group(1), d2))
        else:
            out_lines.append(ln)
    else:
        out_lines.append(ln)

ptxt = "\n".join(out_lines)
media = [l for l in out_lines if l.startswith("http") and not l.startswith("#")]
print("[*] validate: EXTM3U:", ptxt.startswith("#EXTM3U"), "| enc2 left:", "enc2:" in ptxt, "| media:", len(media), flush=True)

seg_dir = "/tmp/kts_segs"
subprocess.run(f"rm -rf {seg_dir}", shell=True)
os.makedirs(seg_dir, exist_ok=True)
final_lines = []
seg_i = 0
fail = False
dl = 0
for ln in out_lines:
    l = ln.strip()
    if l.startswith("#EXT-X-MAP:"):
        m = re.search(r'URI="([^"]+)"', l)
        if m:
            u2 = m.group(1)
            if not u2.startswith("http"):
                u2 = urllib.parse.urljoin(url, u2)
            bd = req_bin(u2)
            if bd and len(bd) > 100:
                fp = f"{seg_dir}/init_{seg_i}"
                seg_i += 1
                open(fp, "wb").write(bd)
                final_lines.append(l.replace(m.group(1), fp))
                dl += 1
            else:
                fail = True
                print(f"[!] init fail {u2[:40]} len={len(bd)}", flush=True)
                break
        else:
            final_lines.append(ln)
    elif l.startswith("http"):
        bd = req_bin(l)
        if bd and len(bd) > 10000:
            fp = f"{seg_dir}/seg_{seg_i}"
            seg_i += 1
            open(fp, "wb").write(bd)
            final_lines.append(fp)
            dl += 1
        else:
            fail = True
            print(f"[!] seg fail {l[:50]} len={len(bd)}", flush=True)
            break
    else:
        final_lines.append(ln)
print("[*] downloaded:", dl, "| fail:", fail, flush=True)

ptxt2 = "\n".join(final_lines)
rp = "/tmp/kts_play.m3u8"
open(rp, "w").write(ptxt2)
print("[*] playlist written:", os.path.getsize(rp), "bytes", flush=True)
print("--- playlist first 12 lines ---", flush=True)
for l in ptxt2.splitlines()[:12]:
    print("   ", l[:90], flush=True)
print("--- segment files ---", flush=True)
import glob
files = sorted(glob.glob(f"{seg_dir}/*"))[:6]
for f in files:
    print("   ", f, os.path.getsize(f), flush=True)
    print("      magic:", open(f, "rb").read(3), flush=True)

out = "/tmp/kts_conv.mp4"
if os.path.exists(out): os.remove(out)
cmd = (f"ffmpeg -y -hide_banner -loglevel error -protocol_whitelist file,http,https,tcp,tls,crypto,data "
       f"-max_reload 3 -i {rp} -c copy -bsf:a aac_adtstoasc -movflags +faststart {out}")
print("[*] running:", cmd, flush=True)
rr = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=1500)
print("[*] ffmpeg rc:", rr.returncode, flush=True)
print("--- stderr (full) ---", flush=True)
print(rr.stderr[-2000:], flush=True)
print("--- stdout ---", flush=True)
print(rr.stdout[-500:], flush=True)
print("out exists:", os.path.exists(out), flush=True)
if os.path.exists(out):
    print("out size:", os.path.getsize(out), flush=True)
print("[done]", flush=True)
