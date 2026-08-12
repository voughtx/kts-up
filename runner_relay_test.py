import urllib.request, urllib.parse, json
UA='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0.0.0 Safari/537.36'
print("1. tunnel /health:", flush=True)
try:
    r=urllib.request.Request("https://terrorist-firewire-for-circles.trycloudflare.com/health", headers={"User-Agent":UA})
    with urllib.request.urlopen(r, timeout=20) as resp:
        print("  status:", resp.status, resp.read().decode()[:80], flush=True)
except Exception as e:
    print("  FAIL:", str(e)[:100], flush=True)
print("2. tunnel relay shows:", flush=True)
try:
    h={"User-Agent":UA,"Accept":"application/json","Origin":"https://kartoons.me/","Referer":"https://kartoons.me/"}
    q=urllib.parse.urlencode([("path","/shows?limit=1")]+[("h_"+k,v) for k,v in h.items()])
    r=urllib.request.Request("https://terrorist-firewire-for-circles.trycloudflare.com/?"+q, headers={"X-KTS-Key":"ktsrelay2026","User-Agent":UA})
    with urllib.request.urlopen(r, timeout=25) as resp:
        b=resp.read().decode()
        print("  status:", resp.status, "| len:", len(b), "| success:", '"success"' in b, flush=True)
except Exception as e:
    print("  FAIL:", str(e)[:120], flush=True)
print("3. direct kartoons:", flush=True)
try:
    r=urllib.request.Request("https://api.kartoons.me/api/shows?limit=1", headers=h)
    with urllib.request.urlopen(r, timeout=20) as resp:
        b=resp.read().decode()
        print("  status:", resp.status, "| success:", '"success"' in b, flush=True)
except Exception as e:
    print("  FAIL:", str(e)[:100], flush=True)
