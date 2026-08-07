# test_s8.py — S8E1 FULL PIPELINE TEST: 3 servers, multi-quality, highest pick,
# katfile convert try -> local remux fallback. Report kya kaam karta hai.
import os, sys, json, re, subprocess, base64, urllib.request, urllib.parse, hashlib, time
from Crypto.Cipher import AES

API = os.environ.get("KEY_8", "https://api.kartoons.me/api").strip().rstrip("/")
SB_URL = os.environ.get("KEY_20", "").strip().rstrip("/")
SB_KEY = os.environ.get("KEY_21", "").strip()
GCM = os.environ.get("KEY_10", "").strip()
KEY9 = "bca9e0df1a5abb32906ca3f63ac04cef"
TT = os.environ.get("KEY_12", "").strip()
TB = os.environ.get("KEY_11", "").strip()
REF = os.environ.get("KEY_14", "").strip()
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120"
EP = "686e5cad04a20924fcbc7834"  # S8E1
MB = 1024 * 1024

# token from pool
TOKEN = os.environ.get("KEY_3", "").strip()
try:
    url = f"{SB_URL}/rest/v1/progress?select=state&id=eq.tk_voughtx_kts-up&limit=1"
    req = urllib.request.Request(url, headers={"apikey": SB_KEY, "Authorization": f"Bearer {SB_KEY}"})
    with urllib.request.urlopen(req, timeout=20) as r:
        arr = json.loads(r.read().decode())
    st0 = (arr[0].get("state") or {}) if arr else {}
    toks = st0.get("tokens") or []
    if toks:
        TOKEN = toks[0]
except Exception as e:
    print("[!] pool fetch fail:", str(e)[:50], flush=True)

def api(path, hdrs=None):
    h = {"User-Agent": UA, "Accept": "application/json", "Origin": REF.rstrip("/"), "Referer": REF,
         "X-Challenge-Token": TOKEN}
    if hdrs: h.update(hdrs)
    try:
        with urllib.request.urlopen(urllib.request.Request(API + path, headers=h), timeout=30) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")

def solve_pow(nonce, bits):
    z = "0" * (bits // 4); s = 0
    while True:
        if hashlib.sha256(f"{nonce}:{s}".encode()).hexdigest().startswith(z):
            return str(s)
        s += 1

def b64u(s):
    b = s.replace("-", "+").replace("_", "/")
    b += "=" * ((4 - len(b) % 4) % 4)
    return base64.b64decode(b)

def dec_cbc(url):
    raw = b64u(url)
    iv, ct = raw[:16], raw[16:]
    c = AES.new(KEY9.encode()[:32], AES.MODE_CBC, iv)
    pt = c.decrypt(ct)
    pad = pt[-1]
    if 1 <= pad <= 16 and pt[-pad:] == bytes([pad]) * pad:
        pt = pt[:-pad]
    return pt.decode("utf-8", "replace")

def dec_gcm(enc):
    s = enc[5:] if enc.startswith("enc2:") else enc
    raw = b64u(s)
    iv, body = raw[:12], raw[12:]
    key = hashlib.sha256(GCM.encode()).digest()
    ct, tag = body[:-16], body[-16:]
    try:
        c = AES.new(key, AES.MODE_GCM, nonce=iv)
        return c.decrypt_and_verify(ct, tag).decode("utf-8", "replace")
    except Exception:
        try:
            c = AES.new(key, AES.MODE_GCM, nonce=bytes(12))
            return c.decrypt_and_verify(ct, tag).decode("utf-8", "replace")
        except Exception:
            return enc

def dec_url(url):
    if not url: return url
    if url.startswith("enc2:"): return dec_gcm(url)
    if url.startswith("http"): return url
    if re.fullmatch(r"[A-Za-z0-9_\-+/=]+", url or ""):
        dec = dec_cbc(url)
        if dec != url and dec.startswith("http"): return dec
    return url

def parse_master(text, base):
    variants = []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("#EXT-X-STREAM-INF"):
            res, bw = "?", "?"
            m = re.search(r"RESOLUTION=(\d+)x(\d+)", line)
            if m: res = f"{m.group(1)}x{m.group(2)}"
            m = re.search(r"BANDWIDTH=(\d+)", line)
            if m: bw = str(int(int(m.group(1)) / 1000)) + "k"
            j = i + 1
            while j < len(lines) and (not lines[j].strip() or lines[j].strip().startswith("#")):
                j += 1
            uri = lines[j].strip() if j < len(lines) else ""
            url = dec_url(uri)
            if not url.startswith("http"):
                url = urllib.parse.urljoin(base, url)
            variants.append({"resolution": res, "bandwidth": bw, "url": url})
            i = j
        else:
            i += 1
    return variants

def rval(res_str):
    m = re.match(r"(\d+)x(\d+)", res_str or "")
    if m: return int(m.group(2))
    m2 = re.search(r"(\d+)p", res_str or "")
    return int(m2.group(1)) if m2 else 0

def katfile_convert(url, fname):
    body = json.dumps({"pageUrl": url, "url": url, "type": "hls", "referer": REF,
                       "origin": REF.rstrip("/"), "cookie": "", "userAgent": UA, "filename": fname}).encode()
    req = urllib.request.Request(f"{TB}/api/convert", data=body, method="POST",
        headers={"User-Agent": UA, "X-API-Token": TT, "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            j = json.loads(resp.read().decode())
    except urllib.error.HTTPError as ex:
        return None, f"convert HTTP {ex.code}"
    job = j.get("id")
    if not job:
        return None, "no job id"
    for i in range(30):
        time.sleep(4)
        try:
            req2 = urllib.request.Request(f"{TB}/api/jobs/{job}", headers={"User-Agent": UA, "X-API-Token": TT})
            with urllib.request.urlopen(req2, timeout=20) as resp:
                j2 = json.loads(resp.read().decode())
            state = j2.get("state")
            if state == "done":
                return f"{TB}/api/download/{job}", j2.get("size") or 0
            if state == "error":
                return None, f"katfile error: {str(j2.get('error'))[:100]}"
        except Exception as e:
            pass
    return None, "timeout"

def local_remux(url):
    # fetch media playlist
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Origin": REF.rstrip("/"), "Referer": REF})
    with urllib.request.urlopen(req, timeout=45) as r:
        text = r.read().decode("utf-8", "replace")
    out_lines = []
    n_enc2 = n_ok = 0
    for ln in text.splitlines():
        ln2 = ln.strip()
        if ln2.startswith("enc2:"):
            n_enc2 += 1
            dd = dec_gcm(ln2)
            if dd.startswith("http"):
                n_ok += 1
                out_lines.append(dd)
            else:
                out_lines.append(ln)
        elif ln2.startswith("#EXT-X-MAP:"):
            m = re.search(r'URI="([^"]+)"', ln2)
            if m and m.group(1).startswith("enc2:"):
                dd = dec_gcm(m.group(1))
                out_lines.append(ln2.replace(m.group(1), dd))
            else:
                out_lines.append(ln)
        else:
            out_lines.append(ln)
    rp = "/tmp/s8_play.m3u8"
    open(rp, "w").write("\n".join(out_lines))
    out = "/tmp/s8_out.mp4"
    if os.path.exists(out): os.remove(out)
    t0 = time.time()
    cmd = (f"ffmpeg -y -hide_banner -loglevel error -protocol_whitelist file,http,https,tcp,tls,crypto,data "
           f"-max_reload 3 -i {rp} -c copy -bsf:a aac_adtstoasc -movflags +faststart {out}")
    rr = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=1500)
    dt = time.time() - t0
    if rr.returncode == 0 and os.path.exists(out) and os.path.getsize(out) > 10 * MB:
        return os.path.getsize(out), dt, n_enc2, n_ok
    return None, dt, n_enc2, n_ok

print(f"[*] GCM len: {len(GCM)} | TOKEN tail: {TOKEN[-6:]} | TB: {TB[:30]}", flush=True)

# 1) links
content = f"episode:{EP}"
st, b = api("/challenge/pow?content=" + urllib.parse.quote(content), {"X-Challenge-Token": TOKEN})
d = json.loads(b).get("data") or {}
sol = solve_pow(d["nonce"], d.get("bits", 16))
hdrs = {"X-Challenge-Token": TOKEN, "Authorization": f"Bearer {TOKEN}", "X-Challenge-Retry": "true",
        "X-Pow-Nonce": d["nonce"], "X-Pow-Solution": sol}
st4, b4 = api(f"/shows/episode/{EP}/links", hdrs)
print("[*] links status:", st4, flush=True)
data = json.loads(b4).get("data") or {}
links = data.get("links") or []
print(f"[*] servers: {len(links)}", flush=True)

# 2) sab servers ke variants
all_variants = []
for i, l in enumerate(links):
    try:
        dec = dec_cbc(l["url"])
        req = urllib.request.Request(dec, headers={"User-Agent": UA, "Origin": REF.rstrip("/"), "Referer": REF})
        with urllib.request.urlopen(req, timeout=30) as r:
            master = r.read().decode()
        v = parse_master(master, dec)
        print(f"[*] server{i+1}: {len(v)} variants -> {[(x['resolution'], x['bandwidth']) for x in v]}", flush=True)
        all_variants += v
    except Exception as e:
        print(f"[!] server{i+1} fail: {str(e)[:60]}", flush=True)

if not all_variants:
    print("[x] koi variant nahi — direct segments case", flush=True)
    sys.exit(1)

# 3) highest quality pick (desc)
all_variants.sort(key=lambda v: rval(v["resolution"]), reverse=True)
print(f"[*] sorted (desc): {[(x['resolution'], x['bandwidth']) for x in all_variants]}", flush=True)
target = all_variants[0]
print(f"[*] HIGHEST PICK: {target['resolution']} ({target['bandwidth']}) url={target['url'][:60]}", flush=True)

# 4) katfile try
print("[*] KATFILE try...", flush=True)
t0 = time.time()
dl, sz = katfile_convert(target["url"], f"S8E1_test_{target['resolution']}")
print(f"[*] katfile: {'OK size=' + str(int(sz)//MB) + 'MB' if dl else 'FAIL: ' + str(sz)} | time={time.time()-t0:.0f}s", flush=True)

# 5) local remux fallback (hamesha test — report dono)
print("[*] LOCAL REMUX (fallback path test)...", flush=True)
lsize, ldt, n_enc2, n_ok = local_remux(target["url"])
if lsize:
    print(f"[*] local remux: OK {int(lsize)//MB}MB in {ldt:.0f}s | enc2 segs: {n_enc2} decrypted: {n_ok}", flush=True)
    # verify
    pr = subprocess.run(f"ffprobe -v error -show_entries stream=codec_type,codec_name -show_entries format=duration -of json /tmp/s8_out.mp4",
                        shell=True, capture_output=True, text=True, timeout=60)
    jf = json.loads(pr.stdout)
    streams = jf.get("streams") or []
    dur = float((jf.get("format") or {}).get("duration") or 0)
    has_v = any(s.get("codec_type") == "video" for s in streams)
    has_a = any(s.get("codec_type") == "audio" for s in streams)
    print(f"[*] VERIFY: v={has_v} a={has_a} dur={dur:.0f}s codecs={[(s.get('codec_type'),s.get('codec_name')) for s in streams]}", flush=True)
else:
    print(f"[x] local remux fail ({ldt:.0f}s, enc2={n_enc2}, ok={n_ok})", flush=True)

print("[done]", flush=True)
