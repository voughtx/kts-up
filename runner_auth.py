#!/usr/bin/env python3
"""runner_auth.py — worker relay se FULL auth flow (challenge + links), alive token."""
import urllib.request, urllib.parse, hashlib, json, os

SB_URL = os.environ.get("KEY_20", "").strip().rstrip("/")
SB_KEY = os.environ.get("KEY_21", "").strip()
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
R = "https://kts-url.gobinog.workers.dev/relay"

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
    h = {"User-Agent": UA, "Accept": "application/json", "Origin": "https://kartoons.me/", "Referer": "https://kartoons.me/"}
    if hdrs: h.update(hdrs)
    q = urllib.parse.urlencode([("path", path)] + [(f"h_{k}", v) for k, v in h.items()])
    rq = urllib.request.Request(R + "?" + q, headers={"X-KTS-Key": "ktsrelay2026", "User-Agent": UA})
    try:
        with urllib.request.urlopen(rq, timeout=30) as resp:
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

EID = "684672cb333e6d02d74c2450"  # Mushoku S1E20
for i, tok in enumerate(TOKENS):
    st, body = relay("/challenge/pow?content=" + urllib.parse.quote("episode:" + EID))
    if st != 200:
        print(f"tok{i}: challenge FAIL {st} {body[:80]}", flush=True)
        continue
    ch = json.loads(body).get("data") or {}
    hdrs = {"X-Challenge-Token": tok, "Authorization": f"Bearer {tok}", "X-Challenge-Retry": "true"}
    if ch.get("nonce"):
        hdrs["X-Pow-Nonce"] = ch["nonce"]
        hdrs["X-Pow-Solution"] = solve_pow(ch["nonce"], ch.get("bits", 16))
    st2, body2 = relay(f"/shows/episode/{EID}/links", hdrs)
    ok = "✅" if st2 == 200 else "❌"
    print(f"tok{i} (...{tok[-6:]}): links {st2} {ok} {body2[:60]}", flush=True)
print("[done]", flush=True)
