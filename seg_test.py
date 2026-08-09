#!/usr/bin/env python3
# seg_test.py — full pipeline test: links -> master -> variant -> segment download
import os, sys, json, urllib.request as q, urllib.parse as u, hashlib, re, time, base64
from Crypto.Cipher import AES

def log(*a): print("[st]", *a, flush=True)

API="https://api.kartoons.me/api"
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0.0.0 Safari/537.36"
REF="https://kartoons.me/"
KEY9=os.environ.get("KEY_9","")
KEY10=os.environ.get("KEY_10","")
SBURL=os.environ.get("KEY_20","").rstrip("/")
SBKEY=os.environ.get("KEY_21","")
EID="681d0ca15edd6fa782ea65c9"  # BLUE LOCK S2E12 Flowers

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

def relay_url(path, headers=None):
    h={"User-Agent":UA,"Accept":"*/*","Origin":REF.rstrip("/"),"Referer":REF}
    if headers: h.update(headers)
    params=[("path",path)]+[("h_"+k,v) for k,v in h.items()]
    # load relay doc
    try:
        req=q.Request(SBURL+"/rest/v1/progress?select=state&id=eq.relay&limit=1", headers={"apikey":SBKEY,"Authorization":"Bearer "+SBKEY})
        with q.urlopen(req,timeout=20) as r:
            st=json.loads(r.read().decode())[0]["state"]
        urls=[x for x in st.get("urls") or [] if isinstance(x,dict) and x.get("url")]
        for x in urls:
            base=x["url"].rstrip("/")
            if x.get("type")=="prefix":
                yield base+path, {"X-KTS-Key":"ktsrelay2026"}
            else:
                yield base+"?"+u.urlencode(params), {"X-KTS-Key":"ktsrelay2026"}
    except Exception as ex:
        log("relay doc fail:", str(ex)[:80])

def fetch_bin(path, headers=None):
    for rurl, rh in relay_url(path, headers):
        try:
            r=q.Request(rurl, headers=rh)
            with q.urlopen(r,timeout=45) as resp:
                b=resp.read()
            if b[:1]==b"{":
                try:
                    jb=json.loads(b)
                    if jb.get("error"):
                        log(f"  relay bad body: {rurl[:45]}... -> {str(jb)[:50]}")
                        continue
                except Exception:
                    pass
            return resp.status, b
        except Exception as ex:
            code=getattr(ex,"code","?")
            bodyb=b""
            try: bodyb=ex.read()[:120]
            except Exception: pass
            log(f"  relay try: {rurl[:45]}... -> HTTP {code} body={bodyb.decode('utf-8','replace')[:90]}")
    # direct
    try:
        r=q.Request(path, headers={"User-Agent":UA,"Referer":REF})
        with q.urlopen(r,timeout=45) as resp:
            return resp.status, resp.read()
    except Exception as ex:
        return getattr(ex,"code","?"), b""

def fetch_text(path, headers=None):
    st,b=fetch_bin(path, headers)
    return st, b.decode("utf-8","replace")

def main():
    log("KEY9 len:", len(KEY9), "| KEY10 len:", len(KEY10))
    # 1) links via API (direct — runner IP allowed for API? use relay)
    toks=os.environ.get("KEY_3","")
    # just use direct API for links? need auth... use relay path
    # load pool token
    try:
        req=q.Request(SBURL+"/rest/v1/progress?select=state&id=eq.tk_voughtx_kts-up&limit=1", headers={"apikey":SBKEY,"Authorization":"Bearer "+SBKEY})
        with q.urlopen(req,timeout=20) as r:
            st=json.loads(r.read().decode())[0]["state"]
        toks=(st.get("tokens") or [])
    except Exception as ex:
        log("pool load fail:", str(ex)[:80]); toks=[os.environ.get("KEY_3","")]
    tok=toks[0]
    content=f"episode:{EID}"
    # challenge via relay
    st,body=fetch_text(f"{API}/challenge/pow?content={u.quote(content)}", {"Authorization":f"Bearer {tok}"})
    log("challenge:", st)
    if st!=200: return
    d=json.loads(body).get("data") or {}
    nonce=d.get("nonce",""); bits=d.get("bits",16)
    # pow
    zeros="0"*(bits//4); extra=bits%4; s=0
    while True:
        hh=hashlib.sha256(f"{nonce}:{s}".encode()).hexdigest()
        if hh.startswith(zeros):
            if extra:
                if int(hh[len(zeros)],16)<(1<<(4-extra)): break
            else: break
        s+=1
    sol=str(s)
    hdrs={"X-Challenge-Token":tok,"Authorization":f"Bearer {tok}","X-Challenge-Retry":"true",
          "X-Pow-Nonce":nonce,"X-Pow-Solution":sol}
    st,body=fetch_text(f"{API}/shows/episode/{EID}/links", hdrs)
    log("links:", st)
    if st!=200: return
    d3=json.loads(body).get("data") or {}
    links=d3.get("links") or []
    log("links count:", len(links))
    master=None
    for ln in links:
        dec=dec_cbc(str(ln.get("url") or ""))
        if dec.startswith("http"): master=dec; break
    log("master:", (master or "")[:60])
    # 2) master fetch
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
    log("variant raw type:", "enc2" if (variant or "").startswith("enc2:") else "http")
    vurl=dec_gcm(variant) if variant.startswith("enc2:") else variant
    log("variant url:", (vurl or "")[:60])
    # 3) variant playlist
    st,vb=fetch_text(vurl)
    log("variant fetch:", st, len(vb))
    if st!=200 or "#EXTM3U" not in vb: return
    segs=[l.strip() for l in vb.splitlines() if l.strip().startswith("http")]
    log("segments:", len(segs))
    if segs:
        seg0=segs[0]
        log(f"seg[0]: {seg0[:80]}")
        # UPLOAD seg0 URL to supabase for immediate sandbox test
        try:
            import urllib.request as qu
            row={"id":"segtmp","state":{"url":seg0,"at":int(time.time())}}
            req=qu.Request(SBURL+"/rest/v1/progress", data=json.dumps(row).encode(),
                headers={"apikey":SBKEY,"Authorization":"Bearer "+SBKEY,"Content-Type":"application/json",
                         "Prefer":"resolution=merge-duplicates"}, method="POST")
            with qu.urlopen(req,timeout=20) as r:
                log("segtmp uploaded:", r.status)
        except Exception as ex:
            log("segtmp upload fail:", str(ex)[:80])
        # VARIATION A: default
        st,sb=fetch_bin(seg0)
        log(f"  A default -> HTTP {st} bytes={len(sb)}")
        # VARIATION B: Referer = variant url (same CDN domain)
        st,sb=fetch_bin(seg0, {"Referer": vurl, "Origin": "/".join(vurl.split("/")[:3])})
        log(f"  B referer=cdndomain -> HTTP {st} bytes={len(sb)}")
        # VARIATION C: no referer (empty)
        st,sb=fetch_bin(seg0, {"Referer": "", "Origin": ""})
        log(f"  C no-ref -> HTTP {st} bytes={len(sb)}")
        # VARIATION D: browser-ish accept
        st,sb=fetch_bin(seg0, {"Accept": "*/*", "Referer": REF})
        log(f"  D ref-page -> HTTP {st} bytes={len(sb)}")
        # VARIATION E: full browser sec-fetch headers
        st,sb=fetch_bin(seg0, {"Referer": REF, "Accept": "video/mp2t,*/*;q=0.8",
            "Sec-Fetch-Site": "same-origin", "Sec-Fetch-Mode": "no-cors", "Sec-Fetch-Dest": "video"})
        log(f"  E secfetch -> HTTP {st} bytes={len(sb)}")
        # VARIATION F: Range partial
        st,sb=fetch_bin(seg0, {"Referer": REF, "Accept": "*/*", "Range": "bytes=0-1023"})
        log(f"  F range -> HTTP {st} bytes={len(sb)}")
        if st==200 and len(sb)>10000:
            log("  >>> SEGMENT OK!")
    log("DONE")

main()
sys.exit(0)
