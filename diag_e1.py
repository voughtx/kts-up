#!/usr/bin/env python3
import os, sys, json, re, urllib.request

K3 = os.environ.get("KEY_3", "").strip()
BASE = os.environ.get("KEY_8", "https://api.kartoons.me/api").strip()
SB = os.environ.get("KEY_20", "").strip().rstrip("/")
SBK = os.environ.get("KEY_21", "").strip()
SID = "6992b11d1f6494bacadcbd74"  # Infinity Nado

def api(path):
    req = urllib.request.Request(BASE + path, headers={
        "User-Agent": "Mozilla/5.0", "Accept": "application/json",
        "Origin": "https://kartoons.me/", "Referer": "https://kartoons.me/",
        "Authorization": "Bearer " + K3})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())

def sb_q(p):
    req = urllib.request.Request(SB + "/rest/v1/episodes?" + p,
        headers={"apikey": SBK, "Authorization": "Bearer " + SBK, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())

print("[e1] start", flush=True)
try:
    j = api(f"/shows/{SID}")
    seasons = j.get("data", {}).get("seasons") or []
    print(f"[e1] seasons: {[s.get('seasonNumber') for s in seasons]}", flush=True)
    for s in seasons:
        if (s.get("seasonNumber") or 0) != 1:
            continue
        seid = s["_id"]
        eps = api(f"/shows/{SID}/season/{seid}/all-episodes")
        print(f"[e1] S1 eps count: {len(eps)}", flush=True)
        for e in eps:
            print(f"[e1] ep {e.get('episodeNumber')} id={e.get('_id')}", flush=True)
except Exception as ex:
    print(f"[e1] API ERR: {type(ex).__name__} {str(ex)[:120]}", flush=True)

try:
    rows = sb_q("select=show,season,episode,mid,id&show=eq.Infinity%20Nado&order=episode")
    print(f"[e1] sb rows: {len(rows)}", flush=True)
    for r in rows:
        print(f"[e1] sb S{r['season']}E{r['episode']} mid={r['mid']} id={r['id']}", flush=True)
except Exception as ex:
    print(f"[e1] SB ERR: {type(ex).__name__} {str(ex)[:100]}", flush=True)
print("[e1] done", flush=True)
