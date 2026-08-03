import base64 as _b
import functools as _f
import hashlib as _h
import json as _j
import os as _o
import re as _r
import subprocess as _s
import sys as _y
import time as _t
import urllib.parse as _u
import urllib.request as _q
import urllib.error as _e
_p=_f.partial(print,flush=True)
try:
    from Crypto.Cipher import AES
except ImportError:
    _s.check_call([_y.executable,"-m","pip","install","-q","pycryptodome"])
    from Crypto.Cipher import AES
try:
    import requests as _req
except ImportError:
    _s.check_call([_y.executable,"-m","pip","install","-q","requests"])
    import requests as _req
_HM=False
try:
    import pymongo as _mg
    _HM=True
except ImportError:
    try:
        _s.check_call([_y.executable,"-m","pip","install","-q","pymongo[srv]"])
        import pymongo as _mg
        _HM=True
    except Exception:
        pass
_UA=("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")
K1=_o.environ.get("KEY_1","")
K2=_o.environ.get("KEY_2","")
K3=_o.environ.get("KEY_3","").strip()
K4=_o.environ.get("KEY_4","").rstrip("/")
K5=_o.environ.get("KEY_5","")
K6=_o.environ.get("KEY_6","")
K7=_o.environ.get("KEY_7","")
_A=_o.environ.get("KEY_8","")
_K=_o.environ.get("KEY_9","")
_G=_o.environ.get("KEY_10","")
_TB=_o.environ.get("KEY_11","")
_TT=_o.environ.get("KEY_12","")
_TG=_o.environ.get("KEY_13","")
_REF=_o.environ.get("KEY_14","")
_WEB=_o.environ.get("KEY_15","")
_p(f"[dbg] k1_len={len(K1)} k2_len={len(K2)} tg={_TG!r} ref={_REF!r} web={_WEB!r}")
_SPLIT=int(_o.environ.get("SPLIT_MB","1700"))*1024*1024
_DRY=_o.environ.get("DRY_RUN","").lower() in ("1","true","yes")
_ITEM=_o.environ.get("ITEM_ID","").strip()
_QUAL=_o.environ.get("QUALITY","").strip() or "best"
_TGT=_o.environ.get("TARGET","").strip()
_S0=_o.environ.get("S0_INCLUDE","").lower() in ("1","true","yes")
def _req_api(path,headers=None,data=None):
    url=_A+path if path.startswith("/") else path
    h={"User-Agent":_UA,"Accept":"application/json","Origin":_REF.rstrip("/"),"Referer":_REF}
    if headers:
        h.update(headers)
    body=None
    if data is not None:
        body=_j.dumps(data).encode()
        h["Content-Type"]="application/json"
    r=_q.Request(url,data=body,headers=h,method="POST" if body else "GET")
    try:
        with _q.urlopen(r,timeout=30) as resp:
            return resp.status,resp.read().decode("utf-8","replace")
    except _e.HTTPError as ex:
        return ex.code,ex.read().decode("utf-8","replace")
    except Exception as ex:
        return 0,str(ex)
def _challenge(content):
    st,body=_req_api("/challenge/pow?content="+_u.quote(content))
    if st!=200:
        return None
    d=(_j.loads(body).get("data") or {})
    if d.get("enabled") is False:
        return None
    return d
def _pow(nonce,bits):
    zeros="0"*(bits//4)
    extra=bits%4
    s=0
    while True:
        hh=_h.sha256(f"{nonce}:{s}".encode()).hexdigest()
        if hh.startswith(zeros):
            if extra:
                if int(hh[len(zeros)],16)<(1<<(4-extra)):
                    return str(s)
            else:
                return str(s)
        s+=1
def _b64u(s):
    b=s.replace("-","+").replace("_","/")
    b+="="*((4-len(b)%4)%4)
    return _b.b64decode(b)
def _dec_cbc(url):
    try:
        raw=_b64u(url)
        iv,ct=raw[:16],raw[16:]
        c=AES.new(_K.encode()[:32],AES.MODE_CBC,iv)
        pt=c.decrypt(ct)
        pad=pt[-1]
        if 1<=pad<=16 and pt[-pad:]==bytes([pad])*pad:
            pt=pt[:-pad]
        return pt.decode("utf-8","replace")
    except Exception:
        return url
def _dec_gcm(enc):
    s=enc[5:] if enc.startswith("enc2:") else enc
    raw=_b64u(s)
    iv,body=raw[:12],raw[12:]
    key=_h.sha256(_G.encode()).digest()
    ct,tag=body[:-16],body[-16:]
    try:
        c=AES.new(key,AES.MODE_GCM,nonce=iv)
        return c.decrypt_and_verify(ct,tag).decode("utf-8","replace")
    except Exception:
        try:
            c=AES.new(key,AES.MODE_GCM,nonce=bytes(12))
            return c.decrypt_and_verify(ct,tag).decode("utf-8","replace")
        except Exception:
            return enc
def _dec_url(url):
    if not url:
        return url
    if url.startswith("enc2:"):
        return _dec_gcm(url)
    if url.startswith("http"):
        return url
    if _r.fullmatch(r"[A-Za-z0-9_\-+/=]+",url or ""):
        dec=_dec_cbc(url)
        if dec!=url and dec.startswith("http"):
            return dec
    return url
def _parse_master(text,base):
    variants=[]
    lines=text.splitlines()
    i=0
    while i<len(lines):
        line=lines[i].strip()
        if line.startswith("#EXT-X-STREAM-INF"):
            res,bw="?","?"
            m=_r.search(r"RESOLUTION=(\d+)x(\d+)",line)
            if m:
                res=f"{m.group(1)}x{m.group(2)}"
            m=_r.search(r"BANDWIDTH=(\d+)",line)
            if m:
                bw=str(int(int(m.group(1))/1000))+"k"
            j=i+1
            while j<len(lines) and (not lines[j].strip() or lines[j].strip().startswith("#")):
                j+=1
            uri=lines[j].strip() if j<len(lines) else ""
            url=_dec_url(uri)
            if not url.startswith("http"):
                url=_u.urljoin(base,url)
            variants.append({"resolution":res,"bandwidth":bw,"url":url})
            i=j
        else:
            i+=1
    return variants
def _rval(res_str):
    m=_r.match(r"(\d+)x(\d+)",res_str or "")
    if m:
        return int(m.group(2))
    m2=_r.search(r"(\d+)p",res_str or "")
    return int(m2.group(1)) if m2 else 0
def _rlab(res_str):
    m=_r.match(r"(\d+)x(\d+)",res_str or "")
    return m.group(2)+"p" if m else (res_str or "?")
def _esc(s):
    return str(s or "").replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
def _json(path):
    st,body=_req_api(path)
    if st!=200:
        return None
    try:
        return _j.loads(body)
    except Exception:
        return None
def _mk_link(url,title,q_label,filename=None):
    fname=filename or f"{title} {q_label}"
    body=_j.dumps({"pageUrl":url,"url":url,"type":"hls","referer":_REF,"origin":_REF.rstrip("/"),"cookie":"","userAgent":_UA,"filename":fname}).encode()
    _p(f"\n[*] converting ({fname}.mp4)...")
    r=_q.Request(_TB+"/api/convert",data=body,method="POST",headers={"User-Agent":_UA,"X-API-Token":_TT,"Content-Type":"application/json"})
    try:
        with _q.urlopen(r,timeout=30) as resp:
            j=_j.loads(resp.read().decode())
    except _e.HTTPError as ex:
        _p(f"[x] convert HTTP {ex.code}: {ex.read().decode()[:200]}")
        return None,None,0
    job=j.get("id")
    if not job:
        return None,None,0
    for i in range(120):
        _t.sleep(5)
        try:
            r=_q.Request(_TB+f"/api/jobs/{job}",headers={"User-Agent":_UA,"X-API-Token":_TT})
            with _q.urlopen(r,timeout=20) as resp:
                j2=_j.loads(resp.read().decode())
            state=j2.get("state")
            if state in ("running","probing","downloading","reencoding"):
                _p(f"   [{i*5}s] {state} {j2.get('progress',0)}%",flush=True)
            if state=="done":
                link=f"{_TB}/api/download/{job}"
                actual=j2.get("filename") or fname+".mp4"
                size=int(j2.get("size") or 0)
                _p(f"\n   [ok] {actual} | {size} B")
                return link,actual,size
            if state=="error":
                _p(f"[x] error: {str(j2.get('error'))[:200]}")
                return None,None,0
        except Exception as ex:
            _p(f"   (poll {str(ex)[:60]})",flush=True)
    _p("[x] timeout.")
    return None,None,0
def _del_job(job_id):
    try:
        r=_q.Request(_TB+f"/api/jobs/{job_id}",method="DELETE",headers={"User-Agent":_UA,"X-API-Token":_TT})
        with _q.urlopen(r,timeout=20) as resp:
            _p(f"[ok] job {job_id} removed")
            return True
    except Exception as ex:
        _p(f"[x] remove fail: {str(ex)[:80]}")
        return False
class _Store:
    def __init__(self):
        self.mongo=None
        self.state={"i0":0,"i1":0,"i2":0}
        if K7 and _HM:
            try:
                self.mongo=_mg.MongoClient(K7,serverSelectionTimeoutMS=8000)
                self.db=self.mongo.get_database("kts")
                self._load()
                _p("[ok] db connected")
                return
            except Exception as ex:
                _p(f"[!] db fail ({str(ex)[:50]})")
        self._load()
        _p("[ok] local storage")
    def _load(self):
        try:
            with open("state.json") as f:
                self.state.update(_j.load(f))
        except Exception:
            pass
    def _save(self):
        if self.mongo is not None:
            try:
                self.db.progress.replace_one({"_id":"main"},self.state,upsert=True)
            except Exception:
                pass
        try:
            with open("state.json","w") as f:
                _j.dump(self.state,f,indent=1)
        except Exception:
            pass
    def done_ids(self):
        ids=set()
        if self.mongo is not None:
            try:
                for d in self.db.episodes.find({},{"id":1}):
                    ids.add(d.get("id"))
                return ids
            except Exception:
                pass
        try:
            with open("done.json") as f:
                return set(_j.load(f))
        except Exception:
            return ids
    def save_item(self,doc):
        if self.mongo is not None:
            try:
                self.db.episodes.replace_one({"id":doc["id"]},doc,upsert=True)
                return
            except Exception:
                pass
        try:
            with open("done.json") as f:
                lst=_j.load(f)
        except Exception:
            lst=[]
        lst=[d for d in lst if d.get("id")!=doc["id"]]
        lst.append(doc)
        with open("done.json","w") as f:
            _j.dump(lst,f,indent=1)
    def mark_done(self,idx):
        lst=self.state.get("done",[])
        if idx not in lst:
            lst.append(idx)
            self.state["done"]=lst
            self._save()
_store=_Store()
def _shows(terms):
    out=[]
    for term in [t.strip() for t in terms.split(",") if t.strip()]:
        j=_json(f"/shows?search={term}")
        if not j or not j.get("data"):
            _p(f"[!] '{term}' not found")
            continue
        out.append(j["data"][0])
    return out
def _seasons(sid):
    j=_json(f"/shows/{sid}")
    if not j:
        return []
    seasons=[s for s in (j.get("data",{}).get("seasons") or []) if s.get("_id")]
    seasons.sort(key=lambda s:s.get("seasonNumber") or 0)
    return seasons
def _eps(sid,seid):
    j=_json(f"/shows/{sid}/season/{seid}/all-episodes")
    if not j:
        return []
    eps=[e for e in (j.get("data") or []) if e.get("_id")]
    eps.sort(key=lambda e:e.get("episodeNumber") or 0)
    return eps
def _meta(eid):
    j=_json(f"/shows/episode/{eid}")
    if not j:
        return {}
    d=j.get("data") or {}
    stitle,snum="",d.get("seasonNumber") or d.get("season_number")
    sid=d.get("seasonId") or {}
    if isinstance(sid,dict):
        if snum is None:
            snum=sid.get("seasonNumber")
        sh=sid.get("showId") or {}
        if isinstance(sh,dict):
            stitle=sh.get("title") or ""
    return {"title":d.get("title") or "","image":d.get("image") or "","season":snum,"episode":d.get("episodeNumber") or d.get("episode_number"),"show_title":stitle}
def _pick(shows,done):
    if _ITEM:
        m=_meta(_ITEM)
        return {"id":_ITEM,"meta":m,"ovr":True}
    idx=_store.state.get("i0",0)
    done_shows=_store.state.get("done",[])
    for off in range(len(shows)):
        si=(idx+off)%len(shows)
        if si in done_shows:
            continue
        show=shows[si]
        seasons=_seasons(show["_id"])
        if not _S0:
            seasons=[s for s in seasons if (s.get("seasonNumber") or 0)!=0]
        if not seasons:
            _store.mark_done(si)
            continue
        s_idx=_store.state.get("i1",0) if si==_store.state.get("i0",0) else 0
        for so in range(len(seasons)):
            ss=(s_idx+so)%len(seasons)
            season=seasons[ss]
            eps=_eps(show["_id"],season["_id"])
            if not eps:
                continue
            e_idx=_store.state.get("i2",0) if (si==_store.state.get("i0",0) and ss==s_idx) else 0
            for eo in range(len(eps)):
                ep=eps[(e_idx+eo)%len(eps)]
                if ep["_id"] in done:
                    continue
                m=_meta(ep["_id"])
                if not m.get("title"):
                    m["title"]=ep.get("title") or "Episode"
                return {"id":ep["_id"],"show":show,"season":season,"ep":ep,"meta":m,"ovr":False,"seasons":seasons,"si":ss,"ei":(e_idx+eo)%len(eps),"eps":eps}
        _store.mark_done(si)
        _store.state["i1"]=0
        _store.state["i2"]=0
    return None
def _advance(pick):
    if pick.get("ovr"):
        return
    seasons,si,ei=pick["seasons"],pick["si"],pick["ei"]
    eps=pick["eps"]
    if ei+1<len(eps):
        _store.state["i2"]=ei+1
    elif si+1<len(seasons):
        _store.state["i1"]=si+1
        _store.state["i2"]=0
    else:
        _store.mark_done(_store.state.get("i0",0))
        shows=_shows(K6)
        if shows:
            _store.state["i0"]=(_store.state.get("i0",0)+1)%len(shows)
        _store.state["i1"]=0
        _store.state["i2"]=0
    _store._save()
def _make_item_link(eid,title,se_tag):
    content=f"episode:{eid}"
    ch=_challenge(content)
    ph={}
    if ch and ch.get("nonce"):
        sol=_pow(ch["nonce"],ch.get("bits",16))
        ph={"X-Pow-Nonce":ch["nonce"],"X-Pow-Solution":sol}
    hdrs={"X-Challenge-Token":K3,"X-Challenge-Retry":"true"}
    hdrs.update(ph)
    st,body=_req_api(f"/shows/episode/{eid}/links",headers=hdrs)
    if st!=200:
        _p(f"[x] links HTTP {st}")
        return None,None,0,""
    data=_j.loads(body).get("data") or {}
    variants=[]
    for ln in (data.get("links") or []):
        if not isinstance(ln,dict) or not ln.get("url"):
            continue
        url=_dec_url(ln["url"])
        if not _r.search(r"(playlist|\.m3u8)",url,_r.I):
            continue
        st2,body2=_req_api(url)
        if st2!=200:
            continue
        variants+=_parse_master(body2,url)
    if not variants:
        _p("[x] no variants")
        return None,None,0,""
    variants.sort(key=lambda v:_rval(v["resolution"]),reverse=True)
    if _QUAL and _QUAL!="best":
        want=int(_r.sub(r"\D","",_QUAL) or 0)
        if want:
            for v in variants:
                if _rval(v["resolution"])==want:
                    variants=[v]
                    break
    target=variants[0]
    q_label=_rlab(target["resolution"])
    fname=f"{title}{se_tag} {q_label}"
    link,name,size=_mk_link(target["url"],title,q_label,filename=fname)
    return link,name,size,q_label
def _push(url,caption,thumb=None,fname=None):
    tmp=None
    if str(url).startswith("http"):
        tmp="/tmp/push.mp4"
        _p("[*] fetching media...")
        with _q.urlopen(_q.Request(url,headers={"User-Agent":_UA}),timeout=1800) as resp:
            done=0
            with open(tmp,"wb") as f:
                while True:
                    c=resp.read(1<<20)
                    if not c:
                        break
                    f.write(c)
                    done+=len(c)
        _p(f"   {done/(1024*1024):.0f} MB")
        fname=fname or "video.mp4"
    else:
        tmp=str(url)
        fname=fname or _o.path.basename(tmp)
    api=f"{_TG}/{K1}/sendVideo"
    with open(tmp,"rb") as f:
        data={"chat_id":K2,"caption":caption,"parse_mode":"HTML","supports_streaming":"true"}
        if thumb:
            data["thumbnail"]=thumb
        r=_req.post(api,data=data,files={"video":(fname,f,"video/mp4")},timeout=1800)
    if tmp.startswith("/tmp/"):
        try:
            _o.remove(tmp)
        except Exception:
            pass
    j=r.json()
    if not j.get("ok"):
        return None,f"{j.get('error_code')} {j.get('description','error')}"
    msg=j["result"]
    fid=""
    if msg.get("video"):
        fid=msg["video"].get("file_id","")
    elif msg.get("document"):
        fid=msg["document"].get("file_id","")
    return msg,None
def _turl(mid):
    cid=str(K2)
    if cid.startswith("-100"):
        cid=cid[4:]
    return f"https://t.me/c/{cid}/{mid}"
def _caption(meta,q,target,web):
    lines=[]
    if meta.get("title"):
        lines.append(f"\U0001F3AC <b>{_esc(meta['title'])}</b>")
    se=[]
    if meta.get("show_title"):
        se.append(_esc(meta["show_title"]))
    if meta.get("season") is not None and meta.get("episode") is not None:
        se.append(f"S{meta['season']}-E{meta['episode']}")
    if se:
        lines.append("\U0001F4FA "+" \u00B7 ".join(se))
    if q:
        lines.append(f"\u2699\uFE0F Quality: {_esc(q)}")
    if target:
        lines.append(f"\U0001F3AF Target: {_esc(target)}")
    if web:
        lines.append(f"\U0001F517 Web: {_esc(web)}")
    return "\n".join(lines)
def _split_send(link,base,cap,thumb):
    tmp="/tmp/big.mp4"
    _p("\n[*] large item — download + split...")
    with _q.urlopen(_q.Request(link,headers={"User-Agent":_UA}),timeout=1800) as resp:
        with open(tmp,"wb") as f:
            while True:
                c=resp.read(1<<20)
                if not c:
                    break
                f.write(c)
    _p(f"   {_o.path.getsize(tmp)/(1024*1024):.0f} MB")
    outd="/tmp/parts"
    _o.makedirs(outd,exist_ok=True)
    for x in _o.listdir(outd):
        try:
            _o.remove(outd+"/"+x)
        except Exception:
            pass
    _s.run(["ffmpeg","-y","-i",tmp,"-c","copy","-map","0","-f","segment","-segment_time","1800","-reset_timestamps","1",f"{outd}/part_%03d.mp4"],check=False,capture_output=True)
    parts=sorted(_o.listdir(outd))
    _p(f"   {len(parts)} parts")
    results=[]
    for i,p in enumerate(parts,1):
        msg,err=_push(f"{outd}/{p}",f"{cap}\n\U0001F9F9 Part {i}/{len(parts)}",thumb,fname=f"{base}.{i:03d}.mp4")
        if msg:
            fid=""
            if msg.get("video"):
                fid=msg["video"].get("file_id","")
            results.append({"part":i,"fid":fid,"mid":msg.get("message_id")})
            _p(f"   part {i} ok")
        else:
            _p(f"   part {i} FAIL: {err}")
    _o.remove(tmp)
    return results
def main():
    if not K1 or not K2:
        _p("missing KEY_1/KEY_2")
        _y.exit(1)
    if not K3:
        _p("missing KEY_3")
        _y.exit(1)
    shows=_shows(K6)
    if not shows:
        _p("no targets")
        _y.exit(1)
    _p(f"[*] targets: {[s.get('title') for s in shows]}")
    pick=_pick(shows,_store.done_ids())
    if not pick:
        _p("[*] all done.")
        _y.exit(0)
    eid=pick["id"]
    meta=pick["meta"]
    se_tag=""
    if meta.get("season") is not None and meta.get("episode") is not None:
        se_tag=f" S{meta['season']}E{meta['episode']}"
    web=f"{_WEB}episodeId={eid}"
    _p(f"\n> next: {meta.get('show_title','')} {se_tag.strip()} — {meta.get('title')}")
    _p(f"   id: {eid}")
    if _DRY:
        _p("\n[dry] preview only.")
        return
    _p("[*] building link...")
    link,name,size,q=_make_item_link(eid,meta.get("title","item"),se_tag)
    if not link:
        _p("[x] link failed (KEY_3 stale?)")
        _y.exit(1)
    job=link.rstrip("/").split("/")[-1]
    _p(f"   ready | {size/(1024*1024):.0f} MB | {q}")
    cap=_caption(meta,q,_TGT or K5,web)
    thumb=meta.get("image") or None
    if size and size>_SPLIT:
        _p(f"[!] {size/(1024*1024):.0f} MB > limit — split")
        base=(name or "item").replace(".mp4","")
        results=_split_send(link,base,cap,thumb)
        if not results:
            _p("[x] split fail")
            _del_job(job)
            _y.exit(1)
        _store.save_item({"id":eid,"show":meta.get("show_title",""),"season":meta.get("season"),"episode":meta.get("episode"),"title":meta.get("title",""),"quality":q,"parts":results,"web":web,"at":int(_t.time()),"size":size})
        _del_job(job)
        _p("\n[ok] done (split). saved.")
        return
    _p("[*] pushing...")
    msg,err=_push(link,cap,thumb,fname=name or "video.mp4")
    if not msg:
        _p(f"[x] push fail: {err}")
        _del_job(job)
        _y.exit(1)
    fid=""
    if msg.get("video"):
        fid=msg["video"].get("file_id","")
    mid=msg.get("message_id")
    perm=f"{K4}/v/{fid}" if K4 and fid else ""
    if perm:
        try:
            _req.post(f"{_TG}/{K1}/editMessageCaption",data={"chat_id":K2,"message_id":mid,"caption":cap+f"\n\U0001F4BE Permanent: {perm}","parse_mode":"HTML"},timeout=60)
        except Exception:
            pass
    _store.save_item({"id":eid,"show":meta.get("show_title",""),"season":meta.get("season"),"episode":meta.get("episode"),"title":meta.get("title",""),"quality":q,"fid":fid,"mid":mid,"turl":_turl(mid) if mid else "","perm":perm,"web":web,"size":size,"at":int(_t.time())})
    _del_job(job)
    _p("\n"+"="*50)
    _p(" [ok] DONE")
    _p("="*50)
    _p(f"   {meta.get('title')}")
    _p(f"   {meta.get('show_title','')} S{meta.get('season')}-E{meta.get('episode')}")
    _p(f"   {q or '?'}")
    _p(f"   {_turl(mid) if mid else ''}")
    if perm:
        _p(f"   {perm}")
    _p("   saved + cleaned")
    _advance(pick)
if __name__=="__main__":
    try:
        main()
    except KeyboardInterrupt:
        _p("\n[stop]")
