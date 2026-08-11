#!/usr/bin/env python3
"""relay_runner_test.py — GH runner se worker /relay test (5 requests)."""
import urllib.request, time, json

def test(url, hdrs=None):
    try:
        req = urllib.request.Request(url, headers=hdrs or {})
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode("utf-8", "replace")
            return resp.status, body[:150]
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")[:150]
    except Exception as e:
        return 0, str(e)[:150]

TOK = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ5b2dvc28iLCJleHAiOjE3ODg2NjI3MTV9.v1NsLqQowOFpZUCojVEv_O2IHlpv8QC0gt2Y1XUsTjM"
R = "https://kts-url.gobinog.workers.dev/relay"
H = {"X-KTS-Key": "ktsrelay2026"}

print("== worker /relay public ==")
for i in range(3):
    st, b = test(f"{R}?path=%2Fshows%2F68615fe7d437587dc8876773", H)
    print(f"  {i+1}: {st} {b[:80]}")

print("== worker /relay challenge (auth) ==")
for i in range(3):
    st, b = test(f"{R}?path=%2Fchallenge%2Fpow%3Fcontent%3Depisode%253A6858e8493945f011d296c99f&h_Authorization=Bearer%20{TOK}&h_User-Agent=Mozilla%2F5.0&h_Origin=https%3A%2F%2Fkartoons.me&h_Referer=https%3A%2F%2Fkartoons.me%2F", H)
    print(f"  {i+1}: {st} {b[:80]}")

print("== cors.sh ==")
try:
    req = urllib.request.Request("https://proxy.cors.sh/https://api.kartoons.me/api/shows/68615fe7d437587dc8876773", headers={"Origin": "https://kartoons.me"})
    with urllib.request.urlopen(req, timeout=25) as resp:
        print("  cors.sh:", resp.status, resp.read()[:80])
except Exception as e:
    print("  cors.sh fail:", str(e)[:100])

print("== allorigins ==")
try:
    req = urllib.request.Request("https://api.allorigins.win/raw?url=https%3A%2F%2Fapi.kartoons.me%2Fapi%2Fshows%2F68615fe7d437587dc8876773")
    with urllib.request.urlopen(req, timeout=25) as resp:
        print("  allorigins:", resp.status, resp.read()[:80])
except Exception as e:
    print("  allorigins fail:", str(e)[:100])

print("[done]")
