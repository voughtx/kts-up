# debug_local_convert.py — S5E1 pe exact _local_convert reproduce + full stderr
import os, sys, json, re, subprocess, base64, urllib.request, urllib.parse, hashlib
from Crypto.Cipher import AES

API = "https://api.kartoons.me/api"
# pool token (Supabase tk_voughtx_kts-up idx 0) — captcha KEY_3 403 de raha hai
SB_URL = os.environ.get("KEY_20", "").strip().rstrip("/")
SB_KEY = os.environ.get("KEY_21", "").strip()
TOKEN = os.environ.get("KEY_3", "").strip()
GCM = os.environ.get("KEY_10", "").strip()
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
KEY9 = "bca9e0df1a5abb32906ca3f63ac04cef"
EP = "687a500af27e6f8b5f5c1bdc"  # S5E1

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

print("[*] KEY_10 len:", len(GCM), "| KEY_3 len:", len(TOKEN), flush=True)
content = f"episode:{EP}"
st, b = api("/challenge/pow?content=" + urllib.parse.quote(content), {"X-Challenge-Token": TOKEN})
d = json.loads(b).get("data") or {}
sol = solve_pow(d["nonce"], d.get("bits",16))
hdrs = {"X-Challenge-Token": TOKEN, "Authorization": f"Bearer {TOKEN}", "X-Challenge-Retry": "true",
        "X-Pow-Nonce": d["nonce"], "X-Pow-Solution": sol}
st4, b4 = api(f"/shows/episode/{EP}/links", hdrs)
print("links status:", st4, flush=True)
links = json.loads(b4).get("data") or {}
urls = [l.get("url") for l in links.get("links") or [] if l.get("url")]
if not urls:
    print("[x] no links"); sys.exit(1)
dec = dec_cbc(urls[0])
print("[*] master url:", dec[:70], flush=True)
req = urllib.request.Request(dec, headers={"User-Agent": "Mozilla/5.0", "Origin": "https://kartoons.me", "Referer": "https://kartoons.me/"})
with urllib.request.urlopen(req, timeout=30) as r:
    master = r.read().decode()

# rewritten playlist
out_lines = []
n_enc2 = 0
n_dec = 0
for ln in master.splitlines():
    ln2 = ln.strip()
    if ln2.startswith("enc2:"):
        n_enc2 += 1
        dd = dec_gcm(ln2)
        if dd.startswith("http"):
            n_dec += 1
            out_lines.append(dd)
        else:
            out_lines.append(ln)
            print("[!] decrypt fail:", ln2[:40], "->", dd[:60], flush=True)
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
print(f"[*] playlist: enc2 lines={n_enc2} decrypted={n_dec}", flush=True)
# first 6 lines of rewritten
for l in out_lines[:6]:
    print("   ", l[:90], flush=True)
out = "/tmp/kts_conv.mp4"
if os.path.exists(out):
    os.remove(out)
cmd = f"ffmpeg -y -hide_banner -loglevel error -i {rp} -c copy {out}"
print("[*] running:", cmd[:80], flush=True)
rr = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=1200)
print("rc:", rr.returncode, flush=True)
print("stderr tail:", rr.stderr[-600:], flush=True)
print("out exists:", os.path.exists(out), "size:", os.path.getsize(out) if os.path.exists(out) else 0, flush=True)
print("[done]", flush=True)
