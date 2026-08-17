#!/usr/bin/env python3
"""diag_stuck.py — KTS stuck-state diagnostic (POSITION ONLY, no titles/captions).
1) cands full list + each unique eid ka show_id (via relay, sirf _id extract)
2) showlist positions of those shows + #47..#52 known ids
3) mongo done counts for key shows
4) postctl/claims/deny snapshot
"""
import os, json, time, urllib.request, urllib.parse, collections

KEY = os.environ.get("KEY_21", "").strip()
SBU = os.environ.get("KEY_20", "").strip().rstrip("/")
RELAY = "https://kts-url.gobinog.workers.dev/relay"

def sbget(url):
    req = urllib.request.Request(url, headers={"apikey": KEY, "Authorization": f"Bearer {KEY}"})
    with urllib.request.urlopen(req, timeout=25) as r:
        return json.loads(r.read().decode())

def relay_show_of(eid):
    """episode -> show_id (sirf _id; title kabhi print nahi)."""
    q = urllib.parse.urlencode([("path", "/shows/episode/" + eid)])
    req = urllib.request.Request(RELAY + "?" + q, headers={"X-KTS-Key": "ktsrelay2026", "User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            d = json.loads(r.read().decode())
        dd = d.get("data") or {}
        sid = dd.get("seasonId") or {}
        if isinstance(sid, dict):
            sh = sid.get("showId") or {}
            if isinstance(sh, dict):
                return str(sh.get("_id") or sh.get("id") or "")
            return str(sid.get("show_id") or sid.get("showId") or "")
        return ""
    except Exception as e:
        return "ERR:" + str(e)[:40]

def main():
    from pymongo import MongoClient
    cli = MongoClient(os.environ.get("KEY_7", "").strip(), serverSelectionTimeoutMS=20000)
    db = cli["kts"]

    # ---- cands ----
    cands = []
    try:
        d = sbget(f"{SBU}/rest/v1/progress?select=state&id=eq.cands&limit=1")
        if d:
            st = d[0].get("state") or {}
            if isinstance(st, str): st = json.loads(st)
            cands = st.get("eids") or []
    except Exception as e:
        print("cands fetch ERR", str(e)[:60], flush=True)
    print("cands len:", len(cands), flush=True)

    # show of each unique cands eid (relay, id-only)
    show_of = {}
    for eid in cands:
        s = relay_show_of(eid)
        show_of.setdefault(s, []).append(eid)
    print("cands -> shows (by show_id):", flush=True)
    for sid, eids in show_of.items():
        print("   show", sid[-8:], "| eps:", len(eids), "| sample:", eids[0][-8:], flush=True)

    # ---- showlist positions ----
    shows = []
    try:
        d = sbget(f"{SBU}/rest/v1/progress?select=state&id=eq.showlist&limit=1")
        if d:
            st = d[0].get("state") or {}
            if isinstance(st, str): st = json.loads(st)
            shows = st.get("shows") or []
    except Exception as e:
        print("showlist ERR", str(e)[:60], flush=True)
    ids = [s.get("id") for s in shows]
    print("showlist len:", len(ids), flush=True)
    def pos(sid):
        try: return ids.index(sid) + 1
        except ValueError: return -1
    KEY_SHOWS = ["d34e2e0e", "68456c07333e6d02d74c2228", "68d981c9c05a53cb918fab5a",
                 "68354cfb2d3fded2dcca04e1", "683554362454037aca2590f1", "683d47473fb4a3d6f197c6f8",
                 "6992b1f5594d7233250ffe96", "688c932afef9b1290056ea0b"]
    for k in KEY_SHOWS:
        print("   id", k[-8:], "-> showlist #", pos(k), flush=True)
    for sid, eids in show_of.items():
        if sid.startswith("ERR"): continue
        print("   cands-show", sid[-8:], "-> showlist #", pos(sid), flush=True)

    # ---- mongo done counts ----
    print("mongo done counts (by show id):", flush=True)
    for k in KEY_SHOWS:
        n = db.episodes.count_documents({"show": k, "status": "done"})
        n2 = db.episodes.count_documents({"id": {"$regex": "^" + k}})
        print("   show", k[-8:], "| status=done:", n, "| id-prefix rows:", n2, flush=True)

    # ---- postctl / claims / deny ----
    pc = db.postctl.find_one({"_id": "post"})
    print("postctl:", ("next_seq=%s lock=%r lock_at=%s age=%ss" % (
        pc.get("next_seq"), str(pc.get("lock") or "")[:10], pc.get("lock_at"),
        int(time.time() - (pc.get("lock_at") or 0)))) if pc else "NONE", flush=True)
    claims = list(db.claims.find())
    print("claims:", len(claims), flush=True)
    for c in sorted(claims, key=lambda x: -x.get("at", 0))[:10]:
        print("   claim", c["_id"][-8:], "age", int(time.time() - c.get("at", 0)), "s", flush=True)
    try:
        d = sbget(f"{SBU}/rest/v1/progress?select=state&id=eq.deny&limit=1")
        deny = (d[0].get("state") or {}).get("eids") or [] if d else []
        print("deny:", len(deny), flush=True)
    except Exception as e:
        print("deny ERR", str(e)[:50], flush=True)
    cli.close()
    print("[done]", flush=True)

if __name__ == "__main__":
    main()
