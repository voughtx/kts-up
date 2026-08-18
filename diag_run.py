#!/usr/bin/env python3
"""diag_run.py — app startup steps ka step-by-step test (runner pe).
Har step ka result print karta hai — batata hai kahin atak raha hai."""
import os, sys, json, time, re, urllib.request, urllib.parse

def log(m):
    print(m, flush=True)

def main():
    KEY_20 = os.environ.get("KEY_20", "").strip()
    KEY_21 = os.environ.get("KEY_21", "").strip()
    SB = KEY_20.rstrip("/")
    log(f"[diag] SB url len={len(SB)} key len={len(KEY_21)}")

    # 1) supabase showlist fetch
    try:
        req = urllib.request.Request(SB + "/rest/v1/progress?select=state&id=eq.showlist&limit=1",
            headers={"apikey": KEY_21, "Authorization": "Bearer " + KEY_21})
        with urllib.request.urlopen(req, timeout=15) as r:
            d = json.loads(r.read().decode())
        st = d[0].get("state") or {}
        if isinstance(st, str):
            st = json.loads(st)
        shows = st.get("shows") or []
        log(f"[diag] 1) showlist OK: {len(shows)} shows")
    except Exception as e:
        log(f"[diag] 1) showlist FAIL: {str(e)[:100]}")
        return

    # 2) pool token + relay auth
    try:
        req = urllib.request.Request(SB + "/rest/v1/progress?select=state&id=eq.tk_voughtx_kts-up&limit=1",
            headers={"apikey": KEY_21, "Authorization": "Bearer " + KEY_21})
        with urllib.request.urlopen(req, timeout=15) as r:
            d = json.loads(r.read().decode())
        st = d[0].get("state") or {}
        if isinstance(st, str):
            st = json.loads(st)
        toks = st.get("tokens") or []
        idx = int(st.get("idx") or 0)
        tok = toks[idx % len(toks)] if toks else ""
        log(f"[diag] 2) pool: {len(toks)} tokens idx={idx} cur=...{tok[-6:] if tok else '-'}")
        # relay auth
        q = urllib.parse.urlencode([("path", "/auth/me"), ("h_Authorization", "Bearer " + tok)])
        req = urllib.request.Request("https://kts-url.gobinog.workers.dev/relay?" + q,
            headers={"X-KTS-Key": "ktsrelay2026", "User-Agent": "Mozilla/5.0"})
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                body = r.read().decode()
                ok = '"success":true' in body
                log(f"[diag] 2b) relay auth/me: {r.status} ok={ok}")
        except urllib.error.HTTPError as e:
            log(f"[diag] 2b) relay auth/me: HTTP {e.code}")
    except Exception as e:
        log(f"[diag] 2) pool FAIL: {str(e)[:100]}")

    # 3) cands fetch
    try:
        req = urllib.request.Request(SB + "/rest/v1/progress?select=state&id=eq.cands&limit=1",
            headers={"apikey": KEY_21, "Authorization": "Bearer " + KEY_21})
        with urllib.request.urlopen(req, timeout=15) as r:
            d = json.loads(r.read().decode())
        st = d[0].get("state") or {}
        if isinstance(st, str):
            st = json.loads(st)
        eids = st.get("eids") or []
        log(f"[diag] 3) cands OK: {len(eids)} eids | first: {eids[0][-8:] if eids else '-'}")
    except Exception as e:
        log(f"[diag] 3) cands FAIL: {str(e)[:100]}")

    # 4) mongo connect
    try:
        from pymongo import MongoClient
        uri = os.environ.get("KEY_7", "").strip()
        cli = MongoClient(uri, serverSelectionTimeoutMS=15000)
        db = cli["kts"]
        n = db.episodes.count_documents({})
        log(f"[diag] 4) mongo OK: {n} episodes | postctl: {db.postctl.count_documents({})}")
        cli.close()
    except Exception as e:
        log(f"[diag] 4) mongo FAIL: {str(e)[:100]}")

    # 5) first pickable ep meta via relay
    try:
        eid = None
        for e in eids[:60]:
            if not e.endswith("82ea65c9") and not e.endswith("74f8fea8"):
                eid = e
                break
        if eid:
            q = urllib.parse.urlencode([("path", "/shows/episode/" + eid), ("h_Authorization", "Bearer " + tok)])
            req = urllib.request.Request("https://kts-url.gobinog.workers.dev/relay?" + q,
                headers={"X-KTS-Key": "ktsrelay2026", "User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=25) as r:
                body = r.read().decode()
                dd = json.loads(body).get("data") or {}
                log(f"[diag] 5) ep meta {eid[-8:]}: {r.status} title={bool(dd.get('title'))} ep#={dd.get('episodeNumber')} sid_dict={isinstance(dd.get('seasonId'), dict)}")
        else:
            log("[diag] 5) no pickable eid")
    except urllib.error.HTTPError as e:
        log(f"[diag] 5) ep meta: HTTP {e.code}")
    except Exception as e:
        log(f"[diag] 5) ep meta FAIL: {str(e)[:100]}")

    log("[diag] DONE")

if __name__ == "__main__":
    main()
