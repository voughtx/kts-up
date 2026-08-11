#!/usr/bin/env python3
"""runner_rt.py — runner se worker /relay test (UA ke saath)."""
import urllib.request

def test(url, hdrs=None):
    try:
        req = urllib.request.Request(url, headers=hdrs or {})
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, resp.read()[:120]
    except urllib.error.HTTPError as e:
        return e.code, e.read()[:150]
    except Exception as e:
        return 0, str(e)[:150]

H = {"X-KTS-Key": "ktsrelay2026", "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0"}
print("== worker /relay public (Mozilla UA) ==")
for i in range(3):
    st, b = test("https://kts-url.gobinog.workers.dev/relay?path=%2Fshows%2F68615fe7d437587dc8876773", H)
    print(f"  {i+1}: {st} {b[:60]}")

print("== worker /health ==")
st, b = test("https://kts-url.gobinog.workers.dev/health")
print(f"  {st} {b[:60]}")

print("[done]")
