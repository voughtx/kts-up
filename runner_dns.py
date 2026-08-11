#!/usr/bin/env python3
"""runner_dns.py — runner se worker/tunnel DNS + reachability test."""
import socket, urllib.request, subprocess

for host in ["kts-url.gobinog.workers.dev", "becomes-jack-ethical-hello.trycloudflare.com", "api.kartoons.me", "proxy.cors.sh"]:
    try:
        ip = socket.gethostbyname(host)
        print(f"DNS {host} -> {ip}", flush=True)
    except Exception as e:
        print(f"DNS {host} -> FAIL {str(e)[:80]}", flush=True)

print("== worker health via urllib ==", flush=True)
try:
    req = urllib.request.Request("https://kts-url.gobinog.workers.dev/health", headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        print("  urllib:", resp.status, resp.read()[:60], flush=True)
except Exception as e:
    print("  urllib fail:", str(e)[:100], flush=True)

print("== worker health via curl ==", flush=True)
r = subprocess.run(["curl", "-s", "-m", "20", "-o", "/dev/null", "-w", "%{http_code}", "https://kts-url.gobinog.workers.dev/health"], capture_output=True, text=True)
print("  curl:", r.stdout, flush=True)

print("== worker relay via urllib ==", flush=True)
try:
    req = urllib.request.Request("https://kts-url.gobinog.workers.dev/relay?path=%2Fshows%2F68615fe7d437587dc8876773",
        headers={"X-KTS-Key": "ktsrelay2026", "User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=25) as resp:
        print("  relay:", resp.status, resp.read()[:60], flush=True)
except Exception as e:
    print("  relay fail:", str(e)[:100], flush=True)
print("[done]", flush=True)
