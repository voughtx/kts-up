#!/usr/bin/env python3
"""runner_cf_test.py — runner se CF domains reachability test (curl vs python)."""
import subprocess, urllib.request

print("== curl: worker /health ==")
r = subprocess.run(["curl", "-s", "-m", "20", "-o", "/dev/null", "-w", "%{http_code}", "https://kts-url.gobinog.workers.dev/health"], capture_output=True, text=True)
print("  curl:", r.stdout)

print("== python urllib: worker /health ==")
try:
    req = urllib.request.Request("https://kts-url.gobinog.workers.dev/health")
    with urllib.request.urlopen(req, timeout=20) as resp:
        print("  python:", resp.status, resp.read()[:100])
except urllib.error.HTTPError as e:
    print("  python HTTP:", e.code, e.read()[:150])
except Exception as e:
    print("  python fail:", str(e)[:150])

print("== curl: pages dashboard ==")
r = subprocess.run(["curl", "-s", "-m", "20", "-o", "/dev/null", "-w", "%{http_code}", "https://kts-dash.pages.dev/"], capture_output=True, text=True)
print("  curl pages:", r.stdout)

print("== python: pages dashboard ==")
try:
    req = urllib.request.Request("https://kts-dash.pages.dev/")
    with urllib.request.urlopen(req, timeout=20) as resp:
        print("  python pages:", resp.status)
except urllib.error.HTTPError as e:
    print("  python pages HTTP:", e.code, e.read()[:150])
except Exception as e:
    print("  python pages fail:", str(e)[:150])

print("== curl: workers.dev generic (kproxy admin) ==")
r = subprocess.run(["curl", "-s", "-m", "20", "-o", "/dev/null", "-w", "%{http_code}", "https://kts-url.gobinog.workers.dev/api/status"], capture_output=True, text=True)
print("  curl kproxy-noauth:", r.stdout)

print("== python: relay with UA override ==")
try:
    req = urllib.request.Request("https://kts-url.gobinog.workers.dev/relay?path=%2Fshows%2F68615fe7d437587dc8876773",
        headers={"X-KTS-Key": "ktsrelay2026", "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126.0"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        print("  python UA:", resp.status, resp.read()[:80])
except urllib.error.HTTPError as e:
    print("  python UA HTTP:", e.code, e.read()[:150])
except Exception as e:
    print("  python UA fail:", str(e)[:150])

print("[done]")
