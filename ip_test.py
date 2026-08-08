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
    toks = []
    try:
        SBURL = os.environ.get("KEY_20", "").rstrip("/")
        SBKEY = os.environ.get("KEY_21", "")
        if SBURL and SBKEY:
            r0 = q.Request(f"{SBURL}/rest/v1/progress?select=state&id=eq.tk_voughtx_kts-up&limit=1",
                           headers={"apikey": SBKEY, "Authorization": "Bearer " + SBKEY})
            with q.urlopen(r0, timeout=20) as resp0:
                arr = json.loads(resp0.read().decode())
            st0 = (arr[0].get("state") or {}) if arr else {}
            toks = [t for t in (st0.get("tokens") or []) if t]
            log("tokens from supabase pool:", len(toks))
    except Exception as ex:
        log("supabase token load fail:", str(ex)[:80])
    if not toks:
        log("no tokens — using env KEY_3")
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
    # 6) VIA TUNNEL RELAY (sandbox GCP IP)
    TUN = os.environ.get("KRELAY", "https://carb-heaven-vocabulary-tours.trycloudflare.com")
    log(f"testing via relay: {TUN}")
    def treq(path, headers=None):
        h2 = {"X-KTS-Key": "ktsrelay2026"}
        if headers: h2.update(headers)
        r2 = q.Request(f"{TUN}?path={u.quote(path)}", headers=h2)
        try:
            with q.urlopen(r2, timeout=45) as resp2:
                return resp2.status, resp2.read().decode("utf-8", "replace")
        except Exception as ex:
            try: return ex.code, ex.read().decode()[:150]
            except Exception: return 0, str(ex)[:150]
    st4, body4 = treq("/auth/me", headers={"Authorization": f"Bearer {tok}"})
    log(f"relay /auth/me: HTTP {st4} | {body4[:80]}")
    if st4 == 200:
        content2 = f"episode:{eid}"
        st5, body5 = treq(f"/challenge/pow?content={u.quote(content2)}")
        log(f"relay challenge: HTTP {st5} | {body5[:60]}")
        if st5 == 200:
            d2 = json.loads(body5).get("data") or {}
            if d2.get("enabled") is False:
                hdrs3 = {"X-Challenge-Token": tok, "Authorization": f"Bearer {tok}", "X-Challenge-Retry": "true"}
            else:
                sol2 = pow_solve(d2["nonce"], d2.get("bits", 16))
                hdrs3 = {"X-Challenge-Token": tok, "Authorization": f"Bearer {tok}", "X-Challenge-Retry": "true",
                         "X-Pow-Nonce": d2["nonce"], "X-Pow-Solution": sol2}
            st6, body6 = treq(f"/shows/episode/{eid}/links", headers=hdrs3)
            log(f"relay links: HTTP {st6} | {body6[:120]}")
            if st6 == 200:
                log(">>> RELAY WORKS FROM GH RUNNER!")
    log("DONE")

if __name__ == "__main__":
    main()
    sys.exit(0)
