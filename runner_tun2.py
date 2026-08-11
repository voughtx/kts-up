#!/usr/bin/env python3
"""runner_tun2.py — naye tunnel ka DNS + relay test runner pe."""
import socket, urllib.request

HOST = "regular-coat-soil-snapshot.trycloudflare.com"
try:
    print(f"DNS {HOST} -> {socket.gethostbyname(HOST)}", flush=True)
except Exception as e:
    print(f"DNS {HOST} -> FAIL {str(e)[:80]}", flush=True)

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0 Safari/537.36"
try:
    req = urllib.request.Request(
        f"https://{HOST}/?path=%2Fshows%2F68615fe7d437587dc8876773",
        headers={"X-KTS-Key": "ktsrelay2026", "User-Agent": UA})
    with urllib.request.urlopen(req, timeout=25) as resp:
        print("  tunnel relay:", resp.status, resp.read()[:60], flush=True)
except Exception as e:
    print("  tunnel relay fail:", str(e)[:100], flush=True)
print("[done]", flush=True)
