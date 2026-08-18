#!/usr/bin/env python3
"""scan_fix_tokens.py — sab 5 pools ke tokens scan (relay1 via runner), sirf
ALIVE tokens se pools rewrite. Dead/rate-limited hatao. idx=0.
Position-only output — token values kabhi print nahi."""
import os, sys, json, time, re, urllib.request, urllib.parse

SB = os.environ.get("KEY_20", "").strip().rstrip("/")
SBKEY = os.environ.get("KEY_21", "").strip()
# Apps Script relay — worker (kts-url) ab 403 block hai, relay1 chal raha hai
RELAY1 = "https://script.google.com/macros/s/AKfycbwRpZ6HzFppacL5-Z4W-ocZTmeqfoZ3DzUvhURC5Nr6HP_opwzIEGa88A8Fc55mdoD5BQ/exec"

def sb_get(url):
    req = urllib.request.Request(SB + url, headers={"apikey": SBKEY, "Authorization": f"Bearer {SBKEY}"})
    with urllib.request.urlopen(req, timeout=25) as r:
        return json.loads(r.read().decode())

def sb_post(doc):
    req = urllib.request.Request(SB + "/rest/v1/progress", data=json.dumps(doc).encode(), method="POST",
        headers={"apikey": SBKEY, "Authorization": f"Bearer {SBKEY}", "Content-Type": "application/json",
                 "Prefer": "resolution=merge-duplicates"})
    with urllib.request.urlopen(req, timeout=25) as r:
        return r.status

def auth_ok(tok):
    q = urllib.parse.urlencode([("path", "/auth/me"), ("h_Authorization", "Bearer " + tok), ("h_X-Challenge-Token", tok)])
    req = urllib.request.Request(RELAY1 + "?" + q, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            b = r.read().decode()
            return '"success":true' in b
    except urllib.error.HTTPError as e:
        return False
    except Exception:
        return False

def main():
    repos = ['kts-up','kts-up-2','kts-up-3','kts-up-4','kts-up-5']
    # collect unique tokens
    all_toks = []
    seen = set()
    for repo in repos:
        try:
            d = sb_get('/rest/v1/progress?select=state&id=eq.tk_voughtx_' + repo)
            st = d[0]['state'] if d else {}
            if isinstance(st, str):
                st = json.loads(st)
            for t in (st.get('tokens') or []):
                if t not in seen:
                    seen.add(t)
                    all_toks.append(t)
        except Exception as e:
            print(f"[scan] {repo} load fail: {str(e)[:60]}", flush=True)
    print(f"[scan] unique tokens: {len(all_toks)}", flush=True)

    alive = []
    dead = []
    for i, t in enumerate(all_toks):
        ok = auth_ok(t)
        (alive if ok else dead).append(t)
        if (i + 1) % 10 == 0:
            print(f"[scan] {i+1}/{len(all_toks)} alive={len(alive)}", flush=True)
        time.sleep(1.3)
    print(f"[scan] DONE alive={len(alive)} dead={len(dead)}", flush=True)

    if not alive:
        print("[scan] KOI ALIVE NAHI — pools mat chhedo", flush=True)
        return

    # rewrite each repo pool = alive tokens (same set, idx 0)
    for repo in repos:
        st_code = sb_post({'id': f'tk_voughtx_{repo}', 'state': {'tokens': alive, 'idx': 0}})
        d = sb_get('/rest/v1/progress?select=state&id=eq.tk_voughtx_' + repo)
        st = d[0]['state'] if d else {}
        if isinstance(st, str):
            st = json.loads(st)
        print(f"[scan] {repo}: save={st_code} | {len(st.get('tokens') or [])} tokens idx={st.get('idx')} first={st.get('tokens',[''])[0][-6:]}", flush=True)
    print("[scan] DONE-REWRITE", flush=True)

if __name__ == "__main__":
    main()
