#!/usr/bin/env python3
"""api_test.py — runner se kartoons API direct test (auth ke saath):
1) /shows/{id} direct
2) seasons fetch direct
3) relay worker
Batata hai kaunsa path ab kaam karta hai."""
import os, sys, json, time, urllib.request, urllib.parse

def sbget(qs):
    SBURL = os.environ.get("KEY_20", "").strip().rstrip("/")
    SBKEY = os.environ.get("KEY_21", "").strip()
    req = urllib.request.Request(f"{SBURL}/rest/v1/progress?{qs}",
        headers={"apikey": SBKEY, "Authorization": f"Bearer {SBKEY}"})
    with urllib.request.urlopen(req, timeout=25) as r:
        return json.loads(r.read().decode())

def main():
    t = sbget("select=state&id=eq.token&limit=1")
    tok = (t[0].get("state") or {}).get("token", "")
    sid = "68354cfb2d3fded2dcca04e1"
    hdrs = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36",
            "Accept": "application/json", "Origin": "https://kartoons.me/", "Referer": "https://kartoons.me/",
            "Authorization": f"Bearer {tok}"}

    # 1) DIRECT
    t0 = time.time()
    try:
        req = urllib.request.Request(f"https://api.kartoons.me/api/shows/{sid}", headers=hdrs)
        with urllib.request.urlopen(req, timeout=25) as r:
            b = r.read().decode()
        print(f"DIRECT /shows: {time.time()-t0:.1f}s -> {r.status} {'OK' if '\"success\":true' in b else 'BAD:'+b[:60]}", flush=True)
    except Exception as e:
        print(f"DIRECT /shows: {time.time()-t0:.1f}s -> EXC {str(e)[:80]}", flush=True)

    # 2) DIRECT seasons (show detail me seasons hain)
    t0 = time.time()
    try:
        req = urllib.request.Request(f"https://api.kartoons.me/api/shows/{sid}", headers=hdrs)
        with urllib.request.urlopen(req, timeout=25) as r:
            d = json.loads(r.read().decode())
        seas = d.get("data", {}).get("seasons") or []
        print(f"DIRECT seasons: {time.time()-t0:.1f}s -> {len(seas)} seasons", flush=True)
        if seas:
            seid = seas[0]["_id"]
            t0 = time.time()
            try:
                req2 = urllib.request.Request(f"https://api.kartoons.me/api/shows/{sid}/season/{seid}/all-episodes", headers=hdrs)
                with urllib.request.urlopen(req2, timeout=25) as r:
                    d2 = json.loads(r.read().decode())
                eps = d2.get("data") or []
                print(f"DIRECT eps: {time.time()-t0:.1f}s -> {len(eps)} eps", flush=True)
            except Exception as e:
                print(f"DIRECT eps: EXC {str(e)[:60]}", flush=True)
    except Exception as e:
        print(f"DIRECT seasons: EXC {str(e)[:80]}", flush=True)

    # 3) WORKER RELAY
    t0 = time.time()
    try:
        q = urllib.parse.urlencode([("path", "/shows/" + sid), ("h_Authorization", "Bearer " + tok)])
        req = urllib.request.Request("https://kts-url.gobinog.workers.dev/relay?" + q,
            headers={"X-KTS-Key": "ktsrelay2026", "User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=25) as r:
            b = r.read().decode()
        print(f"WORKER relay: {time.time()-t0:.1f}s -> {r.status} {'OK' if '\"success\":true' in b else 'BAD:'+b[:60]}", flush=True)
    except urllib.error.HTTPError as e:
        print(f"WORKER relay: {time.time()-t0:.1f}s -> HTTP {e.code} {e.read().decode()[:60]}", flush=True)
    except Exception as e:
        print(f"WORKER relay: {time.time()-t0:.1f}s -> EXC {str(e)[:80]}", flush=True)

    print("[done]", flush=True)

main()
