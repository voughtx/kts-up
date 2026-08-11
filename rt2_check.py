#!/usr/bin/env python3
"""runner_rt2.py — runner se FULL relay flow: challenge + links (app jaisa)."""
import urllib.request, urllib.parse, hashlib, json, os

TOK = ""
try:
    req = urllib.request.Request("https://opplyuxdjlqlnatobuno.supabase.co/rest/v1/progress?select=state&id=eq.tk_voughtx_kts-up&limit=1",
        headers={"apikey": os.environ.get("KEY_21",""), "Authorization": "Bearer " + os.environ.get("KEY_21","")})
    with urllib.request.urlopen(req, timeout=20) as r:
        arr = json.loads(r.read().decode())
    toks = ((arr[0].get("state") or {}).get("tokens")) or []
    TOK = toks[0]
    print("token:", TOK[-8:], flush=True)
except Exception as e:
    print("token fail:", str(e)[:60], flush=True)

R = "https://kts-url.gobinog.workers.dev/relay"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"

def relay(path, hdrs=None):
    h = {"User-Agent": UA, "Accept": "application/json", "Origin": "https://kartoons.me/", "Referer": "https://kartoons.me/"}
    if hdrs: h.update(hdrs)
    q = urllib.parse.urlencode([("path", path)] + [(f"h_{k}", v) for k, v in h.items()])
    # UA actual REQUEST headers mein bhi (CF 1010 bypass) — app jaisa
    req = urllib.request.Request(R + "?" + q, headers={"X-KTS-Key": "ktsrelay2026", "User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")[:200]
    except Exception as e:
        return 0, str(e)[:150]

def solve_pow(nonce, bits):
    z = "0" * (bits // 4); extra = bits % 4; s = 0
    while True:
        hh = hashlib.sha256(f"{nonce}:{s}".encode()).hexdigest()
        if hh.startswith(z):
            if extra:
                if int(hh[len(z)], 16) < (1 << (4 - extra)): return str(s)
            else: return str(s)
        s += 1

EID = "684672cb333e6d02d74c2450"
print("== challenge via worker relay ==", flush=True)
st, body = relay("/challenge/pow?content=" + urllib.parse.quote("episode:" + EID))
print("  challenge:", st, body[:100], flush=True)
ch = {}
if st == 200:
    try: ch = (json.loads(body).get("data") or {})
    except: pass
hdrs = {"X-Challenge-Token": TOK, "Authorization": f"Bearer {TOK}", "X-Challenge-Retry": "true"}
if ch.get("nonce"):
    hdrs["X-Pow-Nonce"] = ch["nonce"]
    hdrs["X-Pow-Solution"] = solve_pow(ch["nonce"], ch.get("bits", 16))
print("== links via worker relay ==", flush=True)
st2, body2 = relay(f"/shows/episode/{EID}/links", hdrs)
print("  links:", st2, body2[:120], flush=True)
print("[done]", flush=True)
