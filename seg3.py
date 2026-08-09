#!/usr/bin/env python3
# seg3.py — CLEAN multi-episode segment test
import os, sys, json, urllib.request as q, urllib.parse as u, hashlib, base64
from Crypto.Cipher import AES

def log(*a): print("[s3]", *a, flush=True)

API="https://api.kartoons.me/api"
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0.0.0 Safari/537.36"
REF="https://kartoons.me/"
KEY9=os.environ.get("KEY_9","")
KEY10=os.environ.get("KEY_10","")
SBURL=os.environ.get("KEY_20","").rstrip("/")
SBKEY=os.environ.get("KEY_21","")

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
    except Exception:
        return enc

def relays():
    try:
        req=q.Request(SBURL+"/rest/v1/progress?select=state&id=eq.relay&limit=1", headers={"apikey":SBKEY,"Authorization":"Bearer "+SBKEY})
        with q.urlopen(req,timeout=20) as r:
            st=json.loads(r.read().decode())[0]["state"]
        return [x for x in (st.get("urls") or []) if isinstance(x,dict) and x.get("url")]
    except Exception:
        return []

def fbin(path, headers=None):
    h={"User-Agent":UA,"Accept":"*/*","Origin":REF.rstrip("/"),"Referer":REF}
    if headers: h.update(headers)
    params=[("path",path)]+[("h_"+k,v) for k,v in h.items()]
    for x in relays():
        base=x["url"].rstrip("/")
        try:
            rurl=base+path if x.get("type")=="prefix" else base+"?"+u.urlencode(params)
            r=q.Request(rurl, headers={"X-KTS-Key":"ktsrelay2026"})
            with q.urlopen(r,timeout=45) as resp:
                b=resp.read()
            if b[:1]==b"{":
                try:
                    if json.loads(b).get("error"): continue
                except Exception: pass
            return resp.status, b
        except Exception:
            pass
    try:
        r=q.Request(path, headers={"User-Agent":UA,"Referer":REF,"Accept":"*/*"})
        with q.urlopen(r,timeout=45) as resp:
            return resp.status, resp.read()
    except Exception as ex:
        return getattr(ex,"code","?"), b""

def ftxt(path, headers=None):
    st,b=fbin(path, headers)
    return st, b.decode("utf-8","replace")

def test_ep(eid, label):
    log(f"===== {label} =====")
    # token
    try:
        req=q.Request(SBURL+"/rest/v1/progress?select=state&id=eq.tk_voughtx_kts-up&limit=1", headers={"apikey":SBKEY,"Authorization":"Bearer "+SBKEY})
        with q.urlopen(req,timeout=20) as r:
            toks=(json.loads(r.read().decode())[0].get("state") or {}).get("tokens") or []
    except Exception:
        toks=[os.environ.get("KEY_3","")]
    tok=toks[0]
    content=f"episode:{eid}"
    st,body=ftxt(f"{API}/challenge/pow?content={u.quote(content)}", {"Authorization":f"Bearer {tok}"})
    if st!=200:
        log("challenge fail:", st); return
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
    st,body=ftxt(f"{API}/shows/episode/{eid}/links", hdrs)
    if st!=200:
        log("links fail:", st); return
    d3=json.loads(body).get("data") or {}
    master=None
    for ln in (d3.get("links") or []):
        dec=dec_cbc(str(ln.get("url") or ""))
        if dec.startswith("http"): master=dec; break
    if not master:
        log("no master"); return
    st,mb=ftxt(master)
    if st!=200 or "#EXTM3U" not in mb:
        log("master fetch fail:", st); return
    variant=None
    lines=mb.splitlines()
    for i,ln in enumerate(lines):
        if "#EXT-X-STREAM-INF" in ln:
            for j in range(i+1,min(i+4,len(lines))):
                u2=lines[j].strip()
                if u2 and not u2.startswith("#"):
                    variant=u2; break
            break
    vurl=dec_gcm(variant) if (variant or "").startswith("enc2:") else variant
    st,vb=ftxt(vurl)
    if st!=200 or "#EXTM3U" not in vb:
        log("variant fail:", st); return
    segs=[l.strip() for l in vb.splitlines() if l.strip().startswith("http")]
    log(f"segments: {len(segs)}")
    if segs:
        st,sb=fbin(segs[0])
        log(f"SEG[0]: HTTP {st} bytes={len(sb)} {'<<< OK!' if st==200 and len(sb)>10000 else ''}")
    log(f"===== END {label} =====\n")

def main():
    log("KEY9:", len(KEY9), "KEY10:", len(KEY10))
    for lbl, eid in [
        ("BL2-E13", "681d0cf15edd6fa782ea65ca"),
        ("BL2-E14", "681d0d3d5edd6fa782ea65cb"),
    ]:
        try:
            test_ep(eid, lbl)
        except Exception as ex:
            log(f"{lbl} ERR: {str(ex)[:80]}")
    log("ALL DONE")

main()
sys.exit(0)
