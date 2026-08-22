#!/usr/bin/env python3
import os, sys, json, re, urllib.request, urllib.parse

K3 = os.environ.get("KEY_3", "").strip()
SB = os.environ.get("KEY_20", "").strip().rstrip("/")
SBK = os.environ.get("KEY_21", "").strip()
SID = "6992b11d1f6494bacadcbd74"

# relay doc se urls
def sb_progress(doc):
    req = urllib.request.Request(SB + f"/rest/v1/progress?select=state&id=eq.{doc}&limit=1",
        headers={"apikey": SBK, "Authorization": "Bearer " + SBK, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=20) as r:
        d = json.loads(r.read().decode())
    return d[0].get("state") or {} if d else {}

def relay_call(relay_url, path, timeout=40):
    h = {"User-Agent": "Mozilla/5.0", "Accept": "application/json",
         "Origin": "https://kartoons.me/", "Referer": "https://kartoons.me/",
         "Authorization": "Bearer " + K3}
    params = [("path", path)] + [("h_" + k, v) for k, v in h.items()]
    rurl = relay_url + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(rurl, headers={"X-KTS-Key": "ktsrelay2026", "User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, r.read().decode()

print(f"[e1] K3 tail: {K3[-8:] if K3 else 'none'} len={len(K3)}", flush=True)
try:
    st = sb_progress("relay")
    urls = [x["url"] for x in st.get("urls", [])]
    print(f"[e1] relay urls: {len(urls)}", flush=True)
except Exception as ex:
    print(f"[e1] relay doc fail: {str(ex)[:80]}", flush=True)
    urls = []

done = False
for u in urls:
    try:
        stc, body = relay_call(u, f"/shows/{SID}")
        print(f"[e1] relay {u[-30:]} -> {stc} | {body[:90]}", flush=True)
        if stc == 200 and '"success":true' in body:
            j = json.loads(body)
            d = j.get("data") or j
            seasons = d.get("seasons") or []
            print(f"[e1] seasons: {[(s.get('seasonNumber'), s.get('_id')) for s in seasons]}", flush=True)
            for s in seasons:
                if (s.get("seasonNumber") or 0) == 1:
                    stc2, body2 = relay_call(u, f"/shows/{SID}/season/{s['_id']}/all-episodes")
                    j2 = json.loads(body2)
                    ed = j2.get("data") or j2
                    print(f"[e1] S1 eps: {len(ed)}", flush=True)
                    for e in ed[:6]:
                        print(f"[e1] ep {e.get('episodeNumber')} id={e.get('_id')}", flush=True)
            done = True
            break
    except Exception as ex:
        print(f"[e1] relay ERR {u[-20:]}: {type(ex).__name__} {str(ex)[:80]}", flush=True)

if not done:
    print("[e1] all relays failed", flush=True)
print("[e1] done", flush=True)
