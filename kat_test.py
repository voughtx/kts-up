#!/usr/bin/env python3
"""katfile convert test — job start + first polls"""
import os, json, urllib.request, urllib.error, time

BASE = os.environ.get("KEY_11", "").strip()
TOK = os.environ.get("KEY_12", "").strip()
URL = "https://toonstream-stream.omagr2007.workers.dev/ep/69abdaf48e6fa2e92fd8e7fc"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0"

print("base:", BASE[:40], "tok len:", len(TOK), flush=True)

body = json.dumps({"pageUrl": URL, "url": URL, "type": "hls",
                   "referer": "https://kartoons.me/", "origin": "https://kartoons.me/",
                   "cookie": "", "userAgent": UA, "filename": "test_ep"}).encode()
req = urllib.request.Request(BASE + "/api/convert", data=body, method="POST",
                             headers={"User-Agent": UA, "X-API-Token": TOK,
                                      "Content-Type": "application/json"})
t0 = time.time()
try:
    with urllib.request.urlopen(req, timeout=40) as r:
        j = json.loads(r.read().decode())
    print("convert resp:", json.dumps(j)[:200], "in", round(time.time()-t0,1), "s", flush=True)
except Exception as e:
    print("convert ERR:", type(e).__name__, str(e)[:150], flush=True)
    raise SystemExit

job = j.get("id")
if not job:
    print("NO JOB ID", flush=True)
    raise SystemExit
print("job:", job, flush=True)

for i in range(6):
    time.sleep(5)
    try:
        req2 = urllib.request.Request(BASE + f"/api/jobs/{job}",
                                      headers={"User-Agent": UA, "X-API-Token": TOK})
        with urllib.request.urlopen(req2, timeout=20) as r:
            j2 = json.loads(r.read().decode())
        print(f"poll {i}: state={j2.get('state')} progress={j2.get('progress')} err={str(j2.get('error'))[:60]}", flush=True)
    except Exception as e:
        print(f"poll {i} ERR:", str(e)[:80], flush=True)
print("done", flush=True)
