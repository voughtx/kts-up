#!/usr/bin/env python3
# relay_pool_test.py — GH runner se relay pool (appscript/corssh) full links flow
import os, sys, json, urllib.request as q, urllib.parse as u, hashlib, time, re
def log(*a): print("[rpt]", *a, flush=True)
def pow_solve(nonce,bits):
    zeros="0"*(bits//4); extra=bits%4; s=0
    while True:
        hh=hashlib.sha256(f"{nonce}:{s}".encode()).hexdigest()
        if hh.startswith(zeros):
            if extra:
                if int(hh[len(zeros)],16)<(1<<(4-extra)): return str(s)
            else: return str(s)
        s+=1
def main():
    SBURL=os.environ.get("KEY_20","").rstrip("/"); SBKEY=os.environ.get("KEY_21","")
    toks=[]
    try:
        r0=q.Request(f"{SBURL}/rest/v1/progress?select=state&id=eq.tk_voughtx_kts-up&limit=1",
                     headers={"apikey":SBKEY,"Authorization":"Bearer "+SBKEY})
        arr=json.loads(q.urlopen(r0,timeout=20).read().decode())
        toks=[t for t in ((arr[0].get("state") or {}).get("tokens") or []) if t]
    except Exception as ex: log("token load fail:", str(ex)[:60])
    if not toks: toks=[os.environ.get("KEY_3","")]
    log("tokens:", len(toks))
    # relay pool from supabase
    r1=q.Request(f"{SBURL}/rest/v1/progress?select=state&id=eq.relay&limit=1",
                 headers={"apikey":SBKEY,"Authorization":"Bearer "+SBKEY})
    arr1=json.loads(q.urlopen(r1,timeout=20).read().decode())
    st0=(arr1[0].get("state") or {}) if arr1 else {}
    relays=[(x.get("name"),x.get("url").rstrip("/"),x.get("type")) for x in (st0.get("urls") or []) if x.get("url")]
    log("relays:", relays)
    EID="686e8ab552b2d65b4faafa6f"
    tok=toks[0]
    UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126.0.0.0"
    # DIRECT first
    def direct(path, headers):
        h={"User-Agent":UA,"Accept":"application/json","Origin":"https://kartoons.me/","Referer":"https://kartoons.me/",**headers}
        r=q.Request("https://api.kartoons.me/api"+path,headers=h)
        try:
            with q.urlopen(r,timeout=25) as resp: return resp.status, resp.read().decode()
        except Exception as ex:
            try: return ex.code, ex.read().decode()
            except Exception: return 0, str(ex)[:100]
    def relay_call(name, url, typ, path, headers):
        h={"User-Agent":UA,"Accept":"application/json","Origin":"https://kartoons.me/","Referer":"https://kartoons.me/",**headers}
        if typ=="h":
            params=[("path",path)]+[("h_"+k,v) for k,v in h.items()]
            r=q.Request(url+"?"+u.urlencode(params),headers={"X-KTS-Key":"ktsrelay2026"})
        elif typ=="prefix":
            r=q.Request(url+"/https://api.kartoons.me/api"+path,headers=h)
        else:
            return 0,"badtype"
        try:
            with q.urlopen(r,timeout=50) as resp: return resp.status, resp.read().decode()
        except Exception as ex:
            try: return ex.code, ex.read().decode()
            except Exception: return 0, str(ex)[:100]
    content=f"episode:{EID}"
    force=os.environ.get("FORCE_RELAY","0")=="1"
    st,body=0,""
    d={}
    if not force:
        st,body=direct(f"/challenge/pow?content={u.quote(content)}",{})
        log("direct challenge:", st)
        if st==200:
            d=json.loads(body).get("data") or {}
            if d.get("enabled") is not False:
                sol=pow_solve(d["nonce"],d.get("bits",16))
                hdrs={"X-Challenge-Token":tok,"Authorization":f"Bearer {tok}","X-Challenge-Retry":"true","X-Pow-Nonce":d["nonce"],"X-Pow-Solution":sol}
                st2,b2=direct(f"/shows/episode/{EID}/links",hdrs)
                log("direct links:", st2, b2[:60])
    if force or st!=200 or 'st2' not in dir() or st2!=200:
        for name,url,typ in relays:
            st3,b3=relay_call(name,url,typ,f"/challenge/pow?content={u.quote(content)}",{})
            if st3!=200: log(f"relay {name} challenge:", st3); continue
            d2=json.loads(b3).get("data") or {}
            if d2.get("enabled") is False:
                hdrs2={"X-Challenge-Token":tok,"Authorization":f"Bearer {tok}","X-Challenge-Retry":"true"}
            else:
                sol2=pow_solve(d2["nonce"],d2.get("bits",16))
                hdrs2={"X-Challenge-Token":tok,"Authorization":f"Bearer {tok}","X-Challenge-Retry":"true","X-Pow-Nonce":d2["nonce"],"X-Pow-Solution":sol2}
            st4,b4=relay_call(name,url,typ,f"/shows/episode/{EID}/links",hdrs2)
            log(f"relay {name} links:", st4, b4[:60])
            if st4==200:
                log(f">>> RELAY {name} WORKS FROM GH RUNNER!")
                break
    log("DONE")
main()
sys.exit(0)
