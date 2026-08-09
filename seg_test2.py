#!/usr/bin/env python3
# seg_test2.py — fresh segment download test (CDN block check)
import os, sys, json, urllib.request as q, urllib.parse as u, hashlib, re, time, base64
from Crypto.Cipher import AES

def log(*a): print("[st2]", *a, flush=True)

API="https://api.kartoons.me/api"
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0.0.0 Safari/537.36"
REF="https://kartoons.me/"
KEY9=os.environ.get("KEY_9","")
KEY10=os.environ.get("KEY_10","")
SBURL=os.environ.get("KEY_20","").rstrip("/")
SBKEY=os.environ.get("KEY_21","")
EID="681d0ca15edd6fa782ea65c9"  # BLUE LOCK S2E12 Flowers (overridden in main)

def b64u(s):
    b=s.replace("-","+").replace("_","/"); b+="="*((4-len(b)%4)%4)
    return base64.b64decode(b)

def dec_cbc(url):
    try:
        raw=b64u(url); iv,ct=raw[:16],raw[16:]
        c=AES.new(KEY9.encode()[:32],AES.MODE_CBC,iv)
        pt=c.decrypt(ct); pad=pt[-1]
        if 1<=pad<=16 and pt[-pad:]==bytes([pad])*pad: pt=pt[:-pad]
        return pt.decode("utf-8","replace")
    except Exception:
        return url

def dec_gcm(enc):
    try:
        s=enc[5:] if enc.startswith("enc2:") else enc
        raw=b64u(s); iv,body=raw[:12],raw[12:]
        key=hashlib.sha256(KEY10.encode()).digest()
        ct,tag=body[:-16],body[-16:]
        c=AES.new(key,AES.MODE_GCM,nonce=iv)
        return c.decrypt_and_verify(ct,tag).decode("utf-8","replace")
    except Exception as ex:
        return enc

def get_relays():
    try:
        req=q.Request(SBURL+"/rest/v1/progress?select=state&id=eq.relay&limit=1", headers={"apikey":SBKEY,"Authorization":"Bearer "+SBKEY})
        with q.urlopen(req,timeout=20) as r:
            st=json.loads(r.read().decode())[0]["state"]
        return [x for x in (st.get("urls") or []) if isinstance(x,dict) and x.get("url")]
    except Exception as ex:
        log("relay doc fail:", str(ex)[:60]); return []

def fetch_bin(path, headers=None):
    h={"User-Agent":UA,"Accept":"*/*","Origin":REF.rstrip("/"),"Referer":REF}
    if headers: h.update(headers)
    params=[("path",path)]+[("h_"+k,v) for k,v in h.items()]
    for x in get_relays():
        base=x["url"].rstrip("/")
        try:
            if x.get("type")=="prefix":
                rurl=base+path
            else:
                rurl=base+"?"+u.urlencode(params)
            r=q.Request(rurl, headers={"X-KTS-Key":"ktsrelay2026"})
            with q.urlopen(r,timeout=45) as resp:
                b=resp.read()
            if b[:1]==b"{":
                try:
                    jb=json.loads(b)
                    if jb.get("error"): continue
                except Exception: pass
            return resp.status, b
        except Exception as ex:
            code=getattr(ex,"code","?")
            log(f"  relay {x.get('name')}: {code}")
    try:
        r=q.Request(path, headers={"User-Agent":UA,"Referer":REF,"Accept":"*/*"})
        with q.urlopen(r,timeout=45) as resp:
            return resp.status, resp.read()
    except Exception as ex:
        return getattr(ex,"code","?"), b""

def fetch_text(path, headers=None):
    st,b=fetch_bin(path, headers)
    return st, b.decode("utf-8","replace")

EIDS_TEST = [
    ("BL2-E12","681d0ca15edd6fa782ea65c9"),
    ("BL2-E11","681cfa6d5edd6fa782ea65c8"),
    ("BEY-S3E52","6989e260ea728ea14cc267d4"),
]

def test_one(eid, label):
    global EID
    EID=eid
    log(f"===== TEST {label} =====")
    _main()
    log(f"===== END {label} =====\n")

def _main():
    log("KEY9:", len(KEY9), "KEY10:", len(KEY10))
    for lbl, eid in EIDS_TEST:
        test_one(eid, lbl)
    log("ALL DONE")
    # token from pool
    try:
        req=q.Request(SBURL+"/rest/v1/progress?select=state&id=eq.tk_voughtx_kts-up&limit=1", headers={"apikey":SBKEY,"Authorization":"Bearer "+SBKEY})
        with q.urlopen(req,timeout=20) as r:
            st=json.loads(r.read().decode())[0]["state"]
        toks=(st.get("tokens") or [])
    except Exception as ex:
        log("pool fail:", str(ex)[:60]); toks=[os.environ.get("KEY_3","")]
    tok=toks[0]
    content=f"episode:{EID}"
    st,body=fetch_text(f"{API}/challenge/pow?content={u.quote(content)}", {"Authorization":f"Bearer {tok}"})
    log("challenge:", st)
    if st!=200: return
    d=json.loads(body).get("data") or {}
    nonce=d.get("nonce",""); bits=d.get("bits",16)
    zeros="0"*(bits//4); extra=bits%4; s=0
    while True:
        hh=hashlib.sha256(f"{nonce}:{s}".encode()).hexdigest()
        if hh.startswith(zeros):
            if extra:
                if int(hh[len(zeros)],16)<(1<<(4-extra)): break
            else: break
        s+=1
    hdrs={"X-Challenge-Token":tok,"Authorization":f"Bearer {tok}","X-Challenge-Retry":"true",
          "X-Pow-Nonce":nonce,"X-Pow-Solution":str(s)}
    st,body=fetch_text(f"{API}/shows/episode/{EID}/links", hdrs)
    log("links:", st)
    if st!=200: return
    d3=json.loads(body).get("data") or {}
    master=None
    for ln in (d3.get("links") or []):
        dec=dec_cbc(str(ln.get("url") or ""))
        if dec.startswith("http"): master=dec; break
    log("master:", (master or "")[:60])
    st,mb=fetch_text(master)
    log("master fetch:", st, len(mb))
    if st!=200 or "#EXTM3U" not in mb: return
    lines=mb.splitlines()
    variant=None
    for i,ln in enumerate(lines):
        if "#EXT-X-STREAM-INF" in ln:
            for j in range(i+1,min(i+4,len(lines))):
                u2=lines[j].strip()
                if u2 and not u2.startswith("#"):
                    variant=u2; break
            break
    vurl=dec_gcm(variant) if (variant or "").startswith("enc2:") else variant
    log("variant url:", (vurl or "")[:60])
    st,vb=fetch_text(vurl)
    log("variant fetch:", st, len(vb))
    if st!=200 or "#EXTM3U" not in vb: return
    segs=[l.strip() for l in vb.splitlines() if l.strip().startswith("http")]
    log("segments:", len(segs))
    if segs:
        seg0=segs[0]
        log("seg0:", seg0[:70])
        st,sb=fetch_bin(seg0)
        log(f"SEGMENT RESULT: HTTP {st} bytes={len(sb)}")
        if st==200 and len(sb)>10000:
            log(">>> SEGMENT DOWNLOAD WORKS!")
    log("DONE")

main()
sys.exit(0)
