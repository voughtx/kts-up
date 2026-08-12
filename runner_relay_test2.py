import urllib.request, urllib.parse
UA='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0.0.0 Safari/537.36'
TUNNEL="https://terrorist-firewire-for-circles.trycloudflare.com"
# diag jaisa EXACT: path=/shows/{id}, Origin bina slash
h={"User-Agent":UA,"Accept":"application/json","Origin":"https://kartoons.me","Referer":"https://kartoons.me/"}
path="/shows/68615fe7d437587dc8876773"
q=urllib.parse.urlencode([("path",path)]+[("h_"+k,v) for k,v in h.items()])
rurl=TUNNEL+"?"+q
print("1. diag-exact (Origin no-slash):", flush=True)
try:
    r=urllib.request.Request(rurl, headers={"X-KTS-Key":"ktsrelay2026","User-Agent":UA})
    with urllib.request.urlopen(r, timeout=25) as resp:
        b=resp.read().decode()
        print("  status:", resp.status, "| len:", len(b), "| success:", '"success"' in b, flush=True)
except Exception as e:
    print("  FAIL:", str(e)[:120], flush=True)
# Origin slash ke saath
h2={"User-Agent":UA,"Accept":"application/json","Origin":"https://kartoons.me/","Referer":"https://kartoons.me/"}
q2=urllib.parse.urlencode([("path",path)]+[("h_"+k,v) for k,v in h2.items()])
print("2. Origin with-slash:", flush=True)
try:
    r=urllib.request.Request(TUNNEL+"?"+q2, headers={"X-KTS-Key":"ktsrelay2026","User-Agent":UA})
    with urllib.request.urlopen(r, timeout=25) as resp:
        b=resp.read().decode()
        print("  status:", resp.status, "| len:", len(b), "| success:", '"success"' in b, flush=True)
except Exception as e:
    print("  FAIL:", str(e)[:120], flush=True)
