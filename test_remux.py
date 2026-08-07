# test_remux.py — S5E1: enc2 decrypt + ffmpeg -c copy -bsf:a aac_adtstoasc (NO RE-ENCODE)
# Time + verify + size measure — professional remux solution test
import os, sys, json, re, subprocess, base64, urllib.request, urllib.parse, hashlib, time
from Crypto.Cipher import AES

API = "https://api.kartoons.me/api"
SB_URL = os.environ.get("KEY_20", "").strip().rstrip("/")
SB_KEY = os.environ.get("KEY_21", "").strip()
GCM = os.environ.get("KEY_10", "").strip()
KEY9 = "bca9e0df1a5abb32906ca3f63ac04cef"
EP = "687a500af27e6f8b5f5c1bdc"  # S5E1

# pool token (kts-up idx 0)
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
    print("[!] pool fetch fail:", str(e)[:60], flush=True)

def api(path, hdrs=None):
    h = {"User-Agent": "Mozilla/5.0", "Accept": "application/json", "Origin": "https://kartoons.me",
         "Referer": "https://kartoons.me/", "X-Challenge-Token": TOKEN}
    if hdrs: h.update(hdrs)
    try:
        with urllib.request.urlopen(urllib.request.Request(API + path, headers=h), timeout=30) as r:
            return r.status, r.read().decode("utf-8","replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8","replace")

def solve_pow(nonce, bits):
    z = "0"*(bits//4); s = 0
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
    return pt.decode("utf-8","replace")

def dec_gcm(enc):
    s = enc[5:] if enc.startswith("enc2:") else enc
    raw = b64u(s)
    iv, body = raw[:12], raw[12:]
    key = hashlib.sha256(GCM.encode()).digest()
    ct, tag = body[:-16], body[-16:]
    try:
        c = AES.new(key, AES.MODE_GCM, nonce=iv)
        return c.decrypt_and_verify(ct, tag).decode("utf-8","replace")
    except Exception:
        try:
            c = AES.new(key, AES.MODE_GCM, nonce=bytes(12))
            return c.decrypt_and_verify(ct, tag).decode("utf-8","replace")
        except Exception:
            return enc

print("[*] GCM len:", len(GCM), "| TOKEN tail:", TOKEN[-6:], flush=True)
t_total = time.time()

# 1) links
content = f"episode:{EP}"
st, b = api("/challenge/pow?content=" + urllib.parse.quote(content), {"X-Challenge-Token": TOKEN})
d = json.loads(b).get("data") or {}
sol = solve_pow(d["nonce"], d.get("bits",16))
hdrs = {"X-Challenge-Token": TOKEN, "Authorization": f"Bearer {TOKEN}", "X-Challenge-Retry": "true",
        "X-Pow-Nonce": d["nonce"], "X-Pow-Solution": sol}
st4, b4 = api(f"/shows/episode/{EP}/links", hdrs)
print("[*] links:", st4, flush=True)
links = json.loads(b4).get("data") or {}
urls = [l.get("url") for l in links.get("links") or [] if l.get("url")]
dec = dec_cbc(urls[0])
req = urllib.request.Request(dec, headers={"User-Agent": "Mozilla/5.0", "Origin": "https://kartoons.me", "Referer": "https://kartoons.me/"})
with urllib.request.urlopen(req, timeout=30) as r:
    master = r.read().decode()

# 2) rewrite playlist
out_lines = []
n_enc2 = n_ok = 0
for ln in master.splitlines():
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
rp = "/tmp/kts_play.m3u8"
open(rp, "w").write("\n".join(out_lines))
print(f"[*] playlist: enc2={n_enc2} decrypted={n_ok}", flush=True)

# 3) ffmpeg -c copy -bsf:a aac_adtstoasc (NO RE-ENCODE)
out = "/tmp/kts_out.mp4"
if os.path.exists(out):
    os.remove(out)
t0 = time.time()
cmd = ("ffmpeg -y -hide_banner -loglevel error -protocol_whitelist file,http,https,tcp,tls,crypto,data "
       f"-i {rp} -c copy -bsf:a aac_adtstoasc -movflags +faststart {out}")
print("[*] ffmpeg remux start...", flush=True)
rr = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=1800)
t1 = time.time()
print(f"[*] rc={rr.returncode} | ffmpeg time: {t1-t0:.1f}s", flush=True)
if rr.stderr:
    print("[*] stderr:", rr.stderr[-300:], flush=True)
print("[*] out exists:", os.path.exists(out), "| size:", (os.path.getsize(out)/1024/1024 if os.path.exists(out) else 0), "MB", flush=True)

# 4) verify
if os.path.exists(out) and os.path.getsize(out) > 10*1024*1024:
    pr = subprocess.run(f"ffprobe -v error -show_entries stream=codec_type,codec_name -show_entries format=duration -of json {out}",
                        shell=True, capture_output=True, text=True, timeout=60)
    jf = json.loads(pr.stdout)
    streams = jf.get("streams") or []
    dur = float((jf.get("format") or {}).get("duration") or 0)
    has_v = any(s.get("codec_type") == "video" for s in streams)
    has_a = any(s.get("codec_type") == "audio" for s in streams)
    codecs = [(s.get("codec_type"), s.get("codec_name")) for s in streams]
    print(f"[*] VERIFY: video={has_v} audio={has_a} dur={dur:.0f}s codecs={codecs}", flush=True)
    print(f"[*] TOTAL TIME: {time.time()-t_total:.1f}s | {'✅ PROPER MP4 (NO RE-ENCODE)' if (has_v and has_a and dur>60) else '❌ FAIL'}", flush=True)
else:
    print("[x] output missing/fail", flush=True)
print("[done]", flush=True)
