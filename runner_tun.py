#!/usr/bin/env python3
"""runner_tun.py — runner se sandbox tunnel DNS + relay test (fresh tunnel)."""
import socket, urllib.request, json

HOSTS = ["becomes-jack-ethical-hello.trycloudflare.com"]
for host in HOSTS:
    try:
        print(f"DNS {host} -> {socket.gethostbyname(host)}", flush=True)
    except Exception as e:
        print(f"DNS {host} -> FAIL {str(e)[:80]}", flush=True)

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0 Safari/537.36"
print("== tunnel relay test ==", flush=True)
try:
    req = urllib.request.Request(
        "https://becomes-jack-ethical-hello.trycloudflare.com/?path=%2Fshows%2F68615fe7d437587dc8876773",
        headers={"X-KTS-Key": "ktsrelay2026", "User-Agent": UA})
    with urllib.request.urlopen(req, timeout=25) as resp:
        print("  tunnel:", resp.status, resp.read()[:60], flush=True)
except Exception as e:
    print("  tunnel fail:", str(e)[:100], flush=True)
print("[done]", flush=True)
