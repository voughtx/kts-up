#!/usr/bin/env python3
# ip_test.py — GH runner IP + kartoons API raw responses
import os, json, urllib.request as q, urllib.parse as u, hashlib, time, re, sys

API = "https://api.kartoons.me/api"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
REF = "https://kartoons.me/"

def log(*a): print("[iptest]", *a, flush=True)

def req(url, headers=None, timeout=30):
    h = {"User-Agent": UA, "Accept": "application/json", "Origin": REF.rstrip("/"), "Referer": REF}
    if headers: h.update(headers)
    r = q.Request(url, headers=h)
    try:
        with q.urlopen(r, timeout=timeout) as resp:
            return resp.status, resp.read().decode("utf-8", "replace"), dict(resp.headers)
    except Exception as ex:
        try:
            return ex.code, ex.read().decode("utf-8", "replace"), {}
        except Exception:
            return 0, str(ex)[:150], {}

def pow_solve(nonce, bits):
    zeros = "0" * (bits // 4); extra = bits % 4; s = 0
    while True:
        hh = hashlib.sha256(f"{nonce}:{s}".encode()).hexdigest()
        if hh.startswith(zeros):
            if extra:
                if int(hh[len(zeros)], 16) < (1 << (4 - extra)): return str(s)
            else: return str(s)
        s += 1

def main():
    # 1) outbound IP
    try:
        st, body, _ = req("https://api.ipify.org?format=json", timeout=15)
        log("outbound IP:", body)
    except Exception as ex:
        log("ipify fail:", str(ex)[:80])
    # 2) token list
    toks = list(dict.fromkeys(re.findall(r'eyJ[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+', open('/tmp/toks.txt').read()))) if os.path.exists('/tmp/toks.txt') else []
    if not toks:
        log("no tokens file — using env KEY_3")
        toks = [os.environ.get("KEY_3", "")]
    log("tokens:", len(toks))
    tok = toks[0]
    # 3) /auth/me raw
    st, body, hdrs = req(API + "/auth/me", headers={"Authorization": f"Bearer {tok}"})
    log(f"/auth/me: HTTP {st} | {body[:200]}")
    # 4) /challenge/pow raw
    eid = "686e8ab552b2d65b4faafa67"
    content = f"episode:{eid}"
    st, body, _ = req(API + f"/challenge/pow?content={u.quote(content)}")
    log(f"challenge/pow: HTTP {st} | {body[:200]}")
    if st == 200:
        d = json.loads(body).get("data") or {}
        if d.get("enabled") is False:
            hdrs2 = {"X-Challenge-Token": tok, "Authorization": f"Bearer {tok}", "X-Challenge-Retry": "true"}
        else:
            sol = pow_solve(d["nonce"], d.get("bits", 16))
            hdrs2 = {"X-Challenge-Token": tok, "Authorization": f"Bearer {tok}", "X-Challenge-Retry": "true",
                     "X-Pow-Nonce": d["nonce"], "X-Pow-Solution": sol}
        st2, body2, _ = req(API + f"/shows/episode/{eid}/links", headers=hdrs2)
        log(f"links: HTTP {st2} | {body2[:250]}")
    # 5) plain GET shows (no auth)
    st3, body3, _ = req(API + "/shows/68121c7f271f42dd3dd09f50")
    log(f"shows (no auth): HTTP {st3} | {body3[:150]}")
    log("DONE")

if __name__ == "__main__":
    main()
    sys.exit(0)
