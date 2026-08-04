import asyncio as _ac
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
try:
    from telethon import TelegramClient
    from telethon.sessions import StringSession
    _HAS_TT=True
except ImportError:
    try:
        _s.check_call([_y.executable,"-m","pip","install","-q","telethon"])
        from telethon import TelegramClient
        from telethon.sessions import StringSession
        _HAS_TT=True
    except Exception:
        _HAS_TT=False
try:
    from pyrogram import Client as _Pyro
    from pyrogram.enums import ParseMode as _PM
    _HAS_PY=True
except ImportError:
    try:
        _s.check_call([_y.executable,"-m","pip","install","-q","pyrogram TgCrypto"])
        from pyrogram import Client as _Pyro
        _HAS_PY=True
    except Exception:
        _HAS_PY=False
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
_TG=_o.environ.get("KEY_13","").rstrip("/")
_REF=_o.environ.get("KEY_14","")
_WEB=_o.environ.get("KEY_15","")
def _tg_base():
    cands=[]
    if _TG:
        cands.append(_TG.rstrip("/"))
        if not _TG.rstrip("/").endswith("/bot"):
            cands.append(_TG.rstrip("/")+"/bot")
    cands.append("https://api.telegram.org/bot")
    for b in cands:
        try:
            gm=_q.urlopen(f"{b}{K1}/getMe",timeout=25)
            gj=_j.loads(gm.read().decode())
            if gj.get("ok"):
                _p(f"[dbg] tg_base_ok={b[-12:]}")
                return b
        except Exception as ex:
            _p(f"[dbg] base_try {b[-16:]} fail: {str(ex)[:60]}")
    _p(f"[dbg] tg_base_all_fail; trying {cands[0][-12:]}")
    return cands[0]
_TBASE=_tg_base()
_p(f"[dbg] k1_len={len(K1)} k1_tail={K1[-4:] if K1 else ''} k2_len={len(K2)} tg={_TG!r} ref={_REF!r} web={_WEB!r}")
_KID=_o.environ.get("KEY_16","").strip()
_KHASH=_o.environ.get("KEY_17","").strip()
_KSESS=_o.environ.get("KEY_18","").strip()
_PSESS=_o.environ.get("KEY_19","").strip()
_SBURL=_o.environ.get("KEY_20","").strip().rstrip("/")
_SBKEY=_o.environ.get("KEY_21","").strip()
_RELAY=_o.environ.get("RELAY_MODE","")=="relay-task"
_RELAYID=_o.environ.get("RELAY_ID","").strip()
_NOFB=_o.environ.get("NO_FALLBACK","").lower() in ("1","true","yes")
_MODE=_o.environ.get("MODE","ordered").strip().lower() or "ordered"
_LANGM=_o.environ.get("LANG_MODE","hindi_only").strip().lower() or "hindi_only"
_PRIO=[x.strip() for x in _o.environ.get("PRIORITY","").split(",") if x.strip()]
_CC=100
try:
    _ccs=_o.environ.get("CONCURRENCY","").strip()
    if _ccs:
        _CC=min(int(_ccs),100)
except Exception:
    _CC=100
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
def _sb_save(doc):
    """Upload metadata ko Supabase me bhi save (dashboard data)."""
    if not (_SBURL and _SBKEY):
        return
    try:
        row={
            "id":doc.get("id",""),"show":doc.get("show",""),"franchise":doc.get("franchise",""),
            "season":doc.get("season"),"episode":doc.get("episode"),
            "title":doc.get("title",""),"quality":doc.get("quality",""),
            "qualities":doc.get("qualities") or [],"lang":doc.get("lang",""),
            "category":doc.get("category",""),"type":doc.get("type",""),
            "thumb":doc.get("thumb",""),"fid":doc.get("fid",""),"bot_fid":doc.get("bot_fid",""),
            "mid":doc.get("mid"),"turl":doc.get("turl",""),"perm":doc.get("perm",""),
            "web":doc.get("web",""),"size":doc.get("size",0),
            "status":"done","at":int(_t.time())}
        url=f"{_SBURL}/rest/v1/episodes"
        req=_q.Request(url,data=_j.dumps(row).encode(),method="POST",
                       headers={"apikey":_SBKEY,"Authorization":f"Bearer {_SBKEY}",
                                "Content-Type":"application/json",
                                "Prefer":"resolution=merge-duplicates"})
        with _q.urlopen(req,timeout=30) as r:
            _p(f"[ok] supabase save ({r.status})")
    except Exception as ex:
        _p(f"[!] supabase save fail: {str(ex)[:80]}")

def _relay_episode(ep_id):
    """Dashboard 'Get Link' → TG se download → public link (GitHub Release/litterbox).
    Link + expiry Supabase me save. Split parts merge hokar ek file."""
    if not (_PSESS and _KID and _KHASH):
        _p("[x] relay: pyrogram session missing (KEY_19)")
        return
    # Supabase se episode metadata (mid, bot_fid, title, size)
    rec=None
    try:
        if _SBURL and _SBKEY:
            url=f"{_SBURL}/rest/v1/episodes?select=*&id=eq.{_u.quote(ep_id)}&limit=1"
            req=_q.Request(url,headers={"apikey":_SBKEY,"Authorization":f"Bearer {_SBKEY}"})
            with _q.urlopen(req,timeout=30) as r:
                arr=_j.loads(r.read().decode())
                rec=arr[0] if arr else None
    except Exception as ex:
        _p(f"[!] relay: sb fetch fail {str(ex)[:60]}")
    if not rec:
        _p("[x] relay: episode Supabase me nahi mila — pehle upload karo")
        return
    mid=rec.get("mid")
    if not mid:
        _p("[x] relay: mid missing")
        return
    async def _do():
        app=_Pyro(":memory:",api_id=int(_KID),api_hash=_KHASH,
                  session_string=_PSESS,max_concurrent_transmissions=_CC)
        try:
            await app.start()
            ent_id=None
            try:
                ent=await app.get_chat(int(K2))
                ent_id=ent.id
            except Exception:
                _p("[!] relay: get_chat fail — dialogs me dhund raha hoon...")
                async for d in app.get_dialogs():
                    if str(d.chat.id)==str(int(K2)):
                        ent_id=d.chat.id
                        break
            if not ent_id:
                return None,"relay: peer id invalid (account channel ka member/admin nahi?)"
            _p(f"[*] relay: target resolved (id={ent_id})")
            _p(f"[*] relay: downloading msg {mid} from TG...")
            msgs=await app.get_messages(ent_id,mid)
            if not msgs:
                return None,"no message"
            dpath="/tmp/relay_dl.bin"
            path=await msgs.download_media(file=dpath)
            if not path:
                return None,"no media"
            fsz=_o.path.getsize(path)
            _p(f"[*] relay: downloaded {fsz/(1024*1024):.0f} MB")
            # split parts hain? (episode me parts saved the to mid list me)
            # upload — GitHub Release (2GB) prefer, litterbox (<1GB) fallback
            fname=(rec.get("title") or "video")[:60]+".mp4"
            fname=_r.sub(r'[^A-Za-z0-9._-]+',"_",fname) or "video.mp4"
            repo=_o.environ.get("GITHUB_REPOSITORY","")
            link=None
            if repo:
                tag="rel-"+str(int(_t.time()*1000))
                r1=_s.run(["gh","release","create",tag,"--repo",repo,"--title",tag,"--notes","temp"],capture_output=True,text=True)
                r2=_s.run(["gh","release","upload",tag,path,"--repo",repo,"--clobber","--name="+fname],capture_output=True,text=True)
                if r1.returncode==0 and r2.returncode==0:
                    link=f"https://github.com/{repo}/releases/download/{tag}/{fname}"
                    _p(f"[*] relay: github release ok")
            if not link:
                resp=_s.run(["curl","-s","--max-time","900","-F","reqtype=fileupload","-F","time=24h","-F",f"fileToUpload=@{path}","https://litterbox.catbox.moe/resources/internals/api.php"],capture_output=True,text=True,timeout=950)
                lb=resp.stdout.strip()
                if lb.startswith("http"):
                    link=lb
                    _p(f"[*] relay: litterbox ok")
            try:
                _o.remove(path)
            except Exception:
                pass
            if not link:
                return None,"upload fail"
            expires=int(_t.time())+86400  # 24h
            # save link to Supabase links table
            try:
                if _SBURL and _SBKEY:
                    row={"id":ep_id,"url":link,"expires_at":expires,"created_at":int(_t.time())}
                    url2=f"{_SBURL}/rest/v1/links"
                    req=_q.Request(url2,data=_j.dumps(row).encode(),method="POST",
                                   headers={"apikey":_SBKEY,"Authorization":f"Bearer {_SBKEY}",
                                            "Content-Type":"application/json",
                                            "Prefer":"resolution=merge-duplicates"})
                    with _q.urlopen(req,timeout=30) as r:
                        _p(f"[ok] relay link saved ({r.status})")
            except Exception as ex:
                _p(f"[!] relay link save fail: {str(ex)[:60]}")
            _p(f"[*] RELAY LINK: {link}")
            _p(f"[*] expires: {expires}")
            return link,None
        except Exception as ex:
            return None,f"relay fail: {str(ex)[:200]}"
        finally:
            try:
                await app.stop()
            except Exception:
                pass
    try:
        r=_ac.get_event_loop().run_until_complete(_do())
        if r and r[0]:
            _p("[ok] relay DONE")
        else:
            _p(f"[x] relay result: {r}")
    except RuntimeError:
        import nest_asyncio
        try:
            nest_asyncio.apply()
        except Exception:
            pass
        r=_ac.get_event_loop().run_until_complete(_do())
        if r and r[0]:
            _p("[ok] relay DONE")
        else:
            _p(f"[x] relay result: {r}")

def _shows(terms):
    """SHOW_SEARCH me ya to naam (search) ya exact show ID (24-char hex) do.
    ID se exact show milta hai — search order se depend nahi karna padta."""
    out=[]
    for term in [t.strip() for t in terms.split(",") if t.strip()]:
        if _r.fullmatch(r"[a-f0-9]{24}",term.lower()):
            j=_json(f"/shows/{term}")
            if j and j.get("data"):
                out.append(j["data"])
                continue
            _p(f"[!] show id '{term}' not found")
            continue
        j=_json(f"/shows?search={term}")
        if not j or not j.get("data"):
            _p(f"[!] '{term}' not found")
            continue
        # pehla result lo — par agar exact title match ho to wo prefer karo
        best=j["data"][0]
        for cand in j["data"]:
            if (cand.get("title") or "").lower()==term.lower():
                best=cand
                break
        out.append(best)
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
_LANG_PREFIXES={
    "(english)":"English","(tamil)":"Tamil","(telugu)":"Telugu",
    "(hindi)":"Hindi","[sub]":"Japanese","(jpn)":"Japanese",
    "(hungama)":"Hindi","(fandub)":"Hindi","(cam)":"Hindi",
    "(cn)":"Chinese","(punjabi)":"Punjabi"}
def _detect_lang(title):
    t=(title or "").lower()
    for pat,lang in _LANG_PREFIXES.items():
        if t.startswith(pat):
            return lang
    return "Hindi"
def _clean_title(title):
    t=title or ""
    low=t.lower()
    for pat in _LANG_PREFIXES:
        if low.startswith(pat):
            t=t[len(pat):].strip()
            break
    return t
def _franchise(title):
    """Show/movie title se franchise name nikalta hai (pehla word, clean)."""
    t=_clean_title(title or "").lower()
    w=t.split()[0] if t.split() else t
    w=_r.sub(r"[^a-z0-9]", "", w)
    return w or "unknown"

def _movies_for(franchise):
    """Franchise naam se movies dhundta hai (release year asc = old first)."""
    j=_json(f"/movies?search={franchise}&limit=50")
    if not j:
        return []
    ms=[m for m in (j.get("data") or []) if m.get("_id")]
    def _yr(m):
        try:
            return int(m.get("releaseYear") or 0)
        except Exception:
            return 0
    ms.sort(key=_yr)
    return ms

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
    dur=d.get("durationMinutes") or d.get("duration") or 0
    try:
        dur=int(dur)
    except Exception:
        dur=0
    category=d.get("category") or ""
    mtype=d.get("type") or ("movie" if "/movies/" in eid else "show")
    # episode/show ke liye category show-detail se lo (episode API me nahi hoti)
    sid2=d.get("seasonId") or {}
    shid=None
    if isinstance(sid2,dict):
        sh2=sid2.get("showId") or {}
        if isinstance(sh2,dict):
            shid=sh2.get("_id")
    if not category and shid:
        j2=_json(f"/shows/{shid}")
        if j2:
            category=(j2.get("data") or {}).get("category") or ""
    return {"title":d.get("title") or "","image":d.get("image") or "","season":snum,
            "episode":d.get("episodeNumber") or d.get("episode_number"),
            "show_title":_clean_title(stitle),"duration":dur,
            "category":category,"type":mtype,"lang":_detect_lang(stitle),
            "franchise":_franchise(stitle)}
def _lang_ok(meta):
    """Language filter: hindi_only me non-Hindi ignore."""
    if _LANGM=="all":
        return True
    return (meta.get("lang") or "Hindi")=="Hindi"

def _pick(shows,done):
    """Agli item pick karo — modes: ordered/random/popular.
    Ek show complete tabhi hota hai jab uske saare episodes uploaded hain.
    Language filter bhi lagta hai (hindi_only/all)."""
    if _ITEM:
        m=_meta(_ITEM)
        return {"id":_ITEM,"meta":m,"ovr":True}
    # mode se order decide
    idx=_store.state.get("i0",0)
    order=list(range(len(shows)))
    if _MODE=="random":
        import random as _rd
        _rd.shuffle(order)
    elif _MODE=="popular":
        order=sorted(order,key=lambda i:-(shows[i].get("rating") or 0))
    else:
        order=list(range(idx,len(shows)))+list(range(0,idx))
    for off in range(len(order)):
        si=order[off]
        show=shows[si]
        seasons=_seasons(show["_id"])
        if not _S0:
            seasons=[s for s in seasons if (s.get("seasonNumber") or 0)!=0]
        if not seasons:
            continue
        all_done=True
        first_pick=None
        for so in range(len(seasons)):
            season=seasons[so]
            eps=_eps(show["_id"],season["_id"])
            if not eps:
                continue
            for eo in range(len(eps)):
                ep=eps[eo]
                if ep["_id"] in done:
                    continue
                all_done=False
                if first_pick is None:
                    m=_meta(ep["_id"])
                    if not m.get("title"):
                        m["title"]=ep.get("title") or "Episode"
                    if not _lang_ok(m):
                        continue  # language filter — ise skip (par show complete nahi)
                    first_pick={"id":ep["_id"],"show":show,"season":season,"ep":ep,
                                "meta":m,"ovr":False,"seasons":seasons,"si":so,"ei":eo,"eps":eps}
        if all_done:
            continue
        if first_pick:
            _store.state["i0"]=si
            _store.state["i1"]=first_pick["si"]
            _store.state["i2"]=first_pick["ei"]+1
            _store._save()
            return first_pick
    # ---- Movies fallback: kisi bhi show ke episodes pending nahi →
    #      franchise ki movies jo abhi tak upload nahi hui, old-first
    md=set(_store.state.get("md",[]))
    for si in range(len(shows)):
        show=shows[si]
        fr=_franchise(show.get("title") or "")
        for mv in _movies_for(fr):
            if mv["_id"] in done or mv["_id"] in md:
                continue
            if not _lang_ok({"lang":_detect_lang(mv.get("title") or "")}):
                continue
            mm={"title":mv.get("title") or "","image":mv.get("image") or "",
                "season":None,"episode":None,"show_title":_clean_title(mv.get("title") or ""),
                "duration":int(mv.get("durationMinutes") or mv.get("durationSeconds") or 0)//60 if (mv.get("durationMinutes") or 0)==0 else int(mv.get("durationMinutes") or 0),
                "category":mv.get("category") or "","type":mv.get("type") or "movie",
                "lang":_detect_lang(mv.get("title") or ""),"franchise":fr}
            _store.state["i0"]=si
            _store._save()
            return {"id":"movie:"+mv["_id"],"meta":mm,"ovr":False,
                    "seasons":[],"si":0,"ei":0,"eps":[]}
    return None
def _advance(pick):
    if pick.get("ovr"):
        return
    # movie ho to md (movies-done) me add
    if str(pick.get("id","")).startswith("movie:"):
        midx=pick["id"][6:]
        md=list(_store.state.get("md",[]))
        if midx not in md:
            md.append(midx)
            _store.state["md"]=md
    _store._save()
def _make_item_link(eid,title,se_tag):
    """Movie/episode link banao. Return: (link,name,size,q_label,qualities)"""
    is_movie=eid.startswith("movie:")
    eid2=eid[6:] if is_movie else eid
    content=f"movie:{eid2}" if is_movie else f"episode:{eid2}"
    ch=_challenge(content)
    ph={}
    if ch and ch.get("nonce"):
        sol=_pow(ch["nonce"],ch.get("bits",16))
        ph={"X-Pow-Nonce":ch["nonce"],"X-Pow-Solution":sol}
    hdrs={"X-Challenge-Token":K3,"X-Challenge-Retry":"true"}
    hdrs.update(ph)
    path=f"/movies/{eid2}/links" if is_movie else f"/shows/episode/{eid2}/links"
    st,body=_req_api(path,headers=hdrs)
    if st!=200:
        _p(f"[x] links HTTP {st}")
        return None,None,0,"",[]
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
        return None,None,0,"",[]
    variants.sort(key=lambda v:_rval(v["resolution"]),reverse=True)
    qualities=sorted({_rlab(v["resolution"]) for v in variants},
                     key=lambda x:-(int(_r.sub(r"\D","",x) or 0)))
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
    return link,name,size,q_label,qualities
def _relay(url_or_path,name=None):
    """katfile/local file ko public URL par relay karo jo Telegram fetch kar sake.
    Priority: GitHub Release (filename preserve) -> litterbox (verified).
    Returns: (public_url, cleanup_tag)"""
    tmp=None
    if str(url_or_path).startswith("http"):
        tmp="/tmp/relay_dl.mp4"
        _p("[*] relay: downloading media...")
        with _q.urlopen(_q.Request(url_or_path,headers={"User-Agent":_UA}),timeout=1800) as resp:
            with open(tmp,"wb") as f:
                while True:
                    c=resp.read(1<<20)
                    if not c:
                        break
                    f.write(c)
        _p(f"   {_o.path.getsize(tmp)/(1024*1024):.0f} MB")
        if not name:
            name="video.mp4"
    else:
        tmp=str(url_or_path)
        name=name or _o.path.basename(tmp)
    name=_r.sub(r'[^A-Za-z0-9._-]+',"_",name) or "video.mp4"
    repo=_o.environ.get("GITHUB_REPOSITORY","")
    # 1) GitHub Release
    if repo:
        tag="rel-"+str(int(_t.time()*1000))
        r1=_s.run(["gh","release","create",tag,"--repo",repo,"--title",tag,"--notes","temp"],capture_output=True,text=True)
        r2=_s.run(["gh","release","upload",tag,tmp,"--repo",repo,"--clobber","--name="+name],capture_output=True,text=True)
        if r1.returncode==0 and r2.returncode==0:
            _p(f"[*] relay: github release {tag} ok")
            return f"https://github.com/{repo}/releases/download/{tag}/{name}",tag
        _p(f"[!] gh release fail ({r1.returncode}/{r2.returncode}) — litterbox try")
    # 2) Litterbox
    try:
        resp=_s.run(["curl","-s","--max-time","900","-F","reqtype=fileupload","-F","time=24h","-F",f"fileToUpload=@{tmp}","https://litterbox.catbox.moe/resources/internals/api.php"],capture_output=True,text=True,timeout=950)
        lb=resp.stdout.strip()
        if lb.startswith("http"):
            _p("[*] relay: litterbox ok")
            return lb,None
        _p(f"[!] litterbox fail: {lb[:100]}")
    except Exception as ex:
        _p(f"[!] litterbox fail: {str(ex)[:80]}")
    return None,None
def _push_telethon(path,caption,thumb=None,name="video.mp4"):
    """User account se upload (2GB limit). Async properly handle karta hai."""
    if not (_HAS_TT and _KID and _KHASH and _KSESS):
        return None,"telethon config missing (KEY_16/17/18)"
    thumb_path=None
    if thumb and str(thumb).startswith("http"):
        try:
            thumb_path="/tmp/thumb.jpg"
            with _q.urlopen(_q.Request(thumb,headers={"User-Agent":_UA}),timeout=60) as resp:
                with open(thumb_path,"wb") as f:
                    while True:
                        c=resp.read(1<<20)
                        if not c:
                            break
                        f.write(c)
            if _o.path.getsize(thumb_path)<1000:
                thumb_path=None
            else:
                _p(f"[*] thumb downloaded ({_o.path.getsize(thumb_path)} B)")
        except Exception as ex:
            _p(f"[!] thumb dl fail: {str(ex)[:80]}")
            thumb_path=None
    elif thumb and _o.path.exists(str(thumb)):
        thumb_path=str(thumb)
    async def _do():
        client=TelegramClient(StringSession(_KSESS),int(_KID),_KHASH)
        try:
            await client.connect()
            me=await client.get_me()
            _p(f"[*] telethon: connected as {me.first_name} (bot={me.bot})")
            ent=await client.get_entity(int(K2))
            _p("[*] telethon: uploading (2GB limit)...")
            # document — asli file name ke saath, thumbnail attached, progress
            # (Telegram me photo+file ek message me nahi ho sakte — isliye
            #  sirf document, uske andar thumbnail lagta hai)
            fsz=_o.path.getsize(path)
            _st=[_t.time(),0,0]  # [last_print_time, last_bytes, chunk_kb]
            def _prog(c,t):
                now=_t.time()
                if now-_st[0]>=10 or c>=t:
                    dt=now-_st[0]
                    spd=((c-_st[1])/(1024*1024)/dt) if dt>0 else 0
                    _st[0]=now
                    _st[1]=c
                    pct=int(c*100/t) if t else 0
                    _p(f"   upload {pct}% ({c/(1024*1024):.0f}/{t/(1024*1024):.0f} MB) | speed {spd:.1f} MB/s | chunk {_st[2]}KB",flush=True)
            _st[2]=1024
            try:
                up=await client.upload_file(path,part_size_kb=1024,file_name=name,
                                            progress_callback=_prog)
            except Exception:
                _st[2]=512
                up=await client.upload_file(path,part_size_kb=512,file_name=name,
                                            progress_callback=_prog)
            msg=await client.send_file(ent,up,force_document=True,thumb=thumb_path or None,
                                       caption=caption,parse_mode="html")
            fid=""
            if getattr(msg,"video",None) is not None:
                fid=str(msg.video.id)
            elif getattr(msg,"document",None) is not None:
                fid=str(msg.document.id)
            has_thumb="yes" if getattr(msg,"media",None) and getattr(msg.media,"document",None) and getattr(msg.media.document,"thumbs",None) else "no"
            mid=getattr(msg,"id",None)
            _p(f"[*] telethon: done msg_id={mid} thumb={has_thumb}")
            return {"message_id":mid,"video":{"file_id":fid}},None
        except Exception as ex:
            return None,f"telethon fail: {str(ex)[:200]}"
        finally:
            try:
                await client.disconnect()
            except Exception:
                pass
    try:
        return _ac.get_event_loop().run_until_complete(_do())
    except RuntimeError:
        import nest_asyncio
        try:
            nest_asyncio.apply()
        except Exception:
            pass
        return _ac.get_event_loop().run_until_complete(_do())

def _push_pyrogram(path,caption,thumb=None,name="video.mp4"):
    """Pyrogram se concurrent upload (fast). 2GB limit."""
    if not (_HAS_PY and _KID and _KHASH and _PSESS):
        return None,"pyrogram config missing (KEY_16/17/19)"
    thumb_path=None
    if thumb and str(thumb).startswith("http"):
        try:
            thumb_path="/tmp/thumb.jpg"
            with _q.urlopen(_q.Request(thumb,headers={"User-Agent":_UA}),timeout=60) as resp:
                with open(thumb_path,"wb") as f:
                    while True:
                        c=resp.read(1<<20)
                        if not c:
                            break
                        f.write(c)
            if _o.path.getsize(thumb_path)<1000:
                thumb_path=None
        except Exception:
            thumb_path=None
    elif thumb and _o.path.exists(str(thumb)):
        thumb_path=str(thumb)
    async def _do():
        app=_Pyro(":memory:",api_id=int(_KID),api_hash=_KHASH,
                  session_string=_PSESS,max_concurrent_transmissions=_CC)
        try:
            await app.start()
            me=await app.get_me()
            _p(f"[*] pyrogram: connected as {me.first_name} (bot={me.is_bot})")
            # peer resolve: direct id -> dialogs search fallback
            ent_id=None
            try:
                ent=await app.get_chat(int(K2))
                ent_id=ent.id
            except Exception:
                _p("[!] get_chat fail — dialogs me dhund raha hoon...")
                async for d in app.get_dialogs():
                    if str(d.chat.id)==str(int(K2)):
                        ent_id=d.chat.id
                        break
            if not ent_id:
                return None,"peer id invalid (account channel ka member/admin nahi?)"
            _p(f"[*] pyrogram: target resolved (id={ent_id})")
            fsz=_o.path.getsize(path)
            _st=[_t.time(),0,0]
            def _prog(c,t):
                now=_t.time()
                if now-_st[0]>=10 or c>=t:
                    dt=now-_st[0]
                    spd=((c-_st[1])/(1024*1024)/dt) if dt>0 else 0
                    _st[0]=now
                    _st[1]=c
                    pct=int(c*100/t) if t else 0
                    _p(f"   upload {pct}% ({c/(1024*1024):.0f}/{t/(1024*1024):.0f} MB) | speed {spd:.1f} MB/s | {_CC}-parallel",flush=True)
            _p("[*] pyrogram: uploading (concurrent x4)...")
            msg=await app.send_document(ent_id,path,file_name=name,thumb=thumb_path or None,
                                        caption=caption,parse_mode=_PM.HTML,
                                        progress=_prog)
            fid=getattr(msg.document,"file_id","") if msg.document else ""
            mid=getattr(msg,"id",None)
            _p(f"[*] pyrogram: done msg_id={mid}")
            return {"message_id":mid,"video":{"file_id":fid}},None
        except Exception as ex:
            return None,f"pyrogram fail: {str(ex)[:200]}"
        finally:
            try:
                await app.stop()
            except Exception:
                pass
    try:
        return _ac.get_event_loop().run_until_complete(_do())
    except RuntimeError:
        import nest_asyncio
        try:
            nest_asyncio.apply()
        except Exception:
            pass
        return _ac.get_event_loop().run_until_complete(_do())

def _split_media_group(link,base,cap,thumb,name="video.mp4"):
    """Badi file (>1.7GB) ko split karke media-group me upload karo.
    ≤10 parts ek block; >10 do blocks; caption sirf last part par.
    Returns: list of {part, fid, mid} ya []"""
    if not (_HAS_PY and _KID and _KHASH and _PSESS):
        return []
    tmp="/tmp/big.mp4"
    _p("\n[*] split: large file — downloading...")
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
    _s.run(["ffmpeg","-y","-i",tmp,"-c","copy","-map","0",
            "-f","segment","-segment_time","1700","-reset_timestamps","1",
            f"{outd}/part_%03d.mp4"],check=False,capture_output=True)
    parts=sorted(_o.listdir(outd))
    if not parts:
        _p("[x] split fail — no parts")
        return []
    _p(f"   {len(parts)} parts")
    async def _do():
        app=_Pyro(":memory:",api_id=int(_KID),api_hash=_KHASH,
                  session_string=_PSESS,max_concurrent_transmissions=_CC)
        try:
            await app.start()
            me=await app.get_me()
            _p(f"[*] pyrogram: connected as {me.first_name}")
            ent=await app.get_chat(int(K2))
            # saare parts upload karke media group me bhejo
            results=[]
            CHUNK=10
            for ci in range(0,len(parts),CHUNK):
                chunk=parts[ci:ci+CHUNK]
                from pyrogram.types import InputMediaDocument
                media=[]
                for pi,p in enumerate(chunk):
                    fpath=f"{outd}/{p}"
                    fname_p=f"{base}.{ci+pi+1:03d}.mp4"
                    _p(f"   uploading part {ci+pi+1}/{len(parts)}...")
                    up=await app.upload_document(fpath,file_name=fname_p)
                    is_last=(ci+pi+1==len(parts))
                    media.append(InputMediaDocument(up,caption=caption if is_last else None,
                                                    parse_mode="HTML" if is_last else None))
                msgs=await app.send_media_group(ent,media)
                for pi,msg in enumerate(msgs):
                    fid=""
                    if msg.document:
                        fid=msg.document.file_id or ""
                    results.append({"part":ci+pi+1,"fid":fid,"mid":msg.id})
                _p(f"   block {ci//CHUNK+1} sent ({len(msgs)} parts)")
            return results
        except Exception as ex:
            _p(f"[x] media group fail: {str(ex)[:200]}")
            return []
        finally:
            try:
                await app.stop()
            except Exception:
                pass
    try:
        r=_ac.get_event_loop().run_until_complete(_do())
    except RuntimeError:
        import nest_asyncio
        try:
            nest_asyncio.apply()
        except Exception:
            pass
        r=_ac.get_event_loop().run_until_complete(_do())
    try:
        _o.remove(tmp)
    except Exception:
        pass
    return r

def _relay_cleanup(tag):
    if not tag:
        return
    repo=_o.environ.get("GITHUB_REPOSITORY","")
    _s.run(["gh","release","delete",tag,"--yes","--repo",repo],capture_output=True,text=True)
    _p(f"[ok] relay release {tag} deleted")

def _push(url,caption,thumb=None,fname=None):
    api=f"{_TBASE}{K1}/sendDocument"
    payload={"chat_id":K2,"document":url,"caption":caption,"parse_mode":"HTML"}
    if thumb:
        payload["thumbnail"]=thumb
    data=_u.urlencode(payload).encode()
    try:
        r=_q.urlopen(_q.Request(api,data=data,method="POST"),timeout=1800)
        j=_j.loads(r.read().decode())
    except _e.HTTPError as ex:
        return None,f"HTTP {ex.code}: {ex.read().decode()[:300]}"
    except Exception as ex:
        return None,f"call fail: {str(ex)[:120]}"
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
_SEP="\u25AC"*18
def _caption(meta,q,target,web,thumb_url="",size=0,duration=0):
    lines=[]
    if meta.get("title"):
        lines.append(f"\U0001F3AC <b><code>{_esc(meta['title'])}</code></b>")
    # 📀 show · Sx-Ey (movie ho to 📀 title)
    if meta.get("show_title"):
        se=[]
        se.append(_esc(meta["show_title"]))
        if meta.get("season") is not None and meta.get("episode") is not None:
            se.append(f"S{meta['season']}-E{meta['episode']}")
        lines.append("\U0001F4C0 <b><code>"+" \u00B7 ".join(se)+"</code></b>")
    elif (meta.get("type") or "").startswith("movie"):
        lines.append(f"\U0001F4C0 <b><code>{_esc(meta.get('title') or '')}</code></b>")
    lines.append(_SEP)
    if q:
        lines.append(f"\u2699\uFE0F Quality: <b>{_esc(q)}</b>")
    lines.append(f"\U0001F4AC Language: <b>{_esc(meta.get('lang') or 'Hindi')}</b>")
    if size:
        mb=size/(1024*1024)
        if mb>=1024:
            lines.append(f"\U0001F4C2 Size: <b>{int(round(mb/1024))} GB</b>")
        else:
            lines.append(f"\U0001F4C2 Size: <b>{int(round(mb))} MB</b>")
    if duration:
        lines.append(f"\U0001F4FC Duration: <b>{int(duration)} Min</b>")
    # 🗃️ Category: Show • Anime  (ya Movie • Cartoon)
    tlab="Movie" if (meta.get("type") or "").startswith("movie") else "Show"
    clab=meta.get("category") or ""
    lines.append(f"\U0001F5F3\uFE0F Category: <b>{_esc(tlab)} \u2022 {_esc(clab)}</b>")
    lines.append(_SEP)
    tgt=""
    if web:
        dom=web.split("//")[-1].split("/")[0]
        lab=dom.split(".")[0].capitalize() if "." in dom else dom
        tgt=f"<b><a href=\"{_esc(web)}\">{_esc(lab)}</a></b>"
    elif target:
        tgt=f"<b>{_esc(target)}</b>"
    if tgt and thumb_url:
        lines.append(f"\U0001F3AF {tgt} | <b><a href=\"{_esc(thumb_url)}\">Thumbnail</a></b>")
    elif tgt:
        lines.append(f"\U0001F3AF {tgt}")
    elif thumb_url:
        lines.append(f"\U0001F3AF <b><a href=\"{_esc(thumb_url)}\">Thumbnail</a></b>")
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
        asset=f"{base}.{i:03d}"
        rel_url,rel_tag=_relay(f"{outd}/{p}",asset+".mp4")
        if not rel_url:
            _p(f"   part {i} relay FAIL")
            continue
        msg,err=_push(rel_url,f"{cap}\n\U0001F9F9 Part {i}/{len(parts)}",thumb)
        if rel_tag:
            _relay_cleanup(rel_tag)
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
    if _RELAY:
        if not _RELAYID:
            _p("[x] relay: RELAY_ID missing")
            _y.exit(1)
        _relay_episode(_RELAYID)
        _y.exit(0)
    if not K1 or not K2:
        _p("missing KEY_1/KEY_2")
        _y.exit(1)
    if not K3:
        _p("missing KEY_3")
        _y.exit(1)
    try:
        gm=_q.urlopen(f"{_TBASE}{K1}/getMe",timeout=30)
        gj=_j.loads(gm.read().decode())
        _p(f"[dbg] getMe ok={gj.get('ok')} err={gj.get('description','')}")
    except Exception as ex:
        _p(f"[dbg] getMe call fail: {str(ex)[:120]}")
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
    is_mv=eid.startswith("movie:")
    web=f"{_WEB}movieId={eid[6:]}" if is_mv else f"{_WEB}episodeId={eid}"
    _p(f"\n> next: {meta.get('show_title','')} {se_tag.strip()} — {meta.get('title')}")
    _p(f"   id: {eid}")
    if _DRY:
        _p("\n[dry] preview only.")
        return
    _p("[*] building link...")
    link,name,size,q,quals=_make_item_link(eid,meta.get("title","item"),se_tag)
    if not link:
        _p("[x] link failed (KEY_3 stale?)")
        _y.exit(1)
    job=link.rstrip("/").split("/")[-1]
    _p(f"   ready | {size/(1024*1024):.0f} MB | {q} | qualities: {quals}")
    thumb=meta.get("image") or None
    cap=_caption(meta,q,_TGT or K5,web,thumb or "",size or 0,meta.get("duration") or 0)
    if size and size>_SPLIT:
        _p(f"[!] {size/(1024*1024):.0f} MB > limit — split (media group)")
        base=(name or "item").replace(".mp4","")
        results=_split_media_group(link,base,cap,thumb,name=name or "video.mp4")
        if not results:
            _p("[x] split fail")
            _del_job(job)
            _y.exit(1)
        _store.save_item({"id":eid,"show":meta.get("show_title",""),"franchise":meta.get("franchise",""),
                          "season":meta.get("season"),"episode":meta.get("episode"),
                          "title":meta.get("title",""),"quality":q,"qualities":quals,
                          "lang":meta.get("lang",""),"category":meta.get("category",""),
                          "thumb":thumb or "","parts":results,"web":web,
                          "at":int(_t.time()),"size":size})
        _del_job(job)
        _p("\n[ok] done (split). saved.")
        return
    # Status message — channel me dikhega kya ho raha hai
    st_msg=""
    try:
        sl=pick.get("seasons") or []
        el=pick.get("eps") or []
        csn=sl[pick["si"]].get("seasonNumber") if pick.get("si") is not None and sl else None
        cen=(pick.get("ep") or {}).get("episodeNumber")
        l1=f"\U0001F4C0 {meta.get('show_title') or ''}".strip()
        l2=""
        if csn is not None:
            l2+=f"S{csn} - {len(sl)}"
        if cen is not None:
            l2+=f" | E{cen} - {len(el)}"
        st_msg=l1+(f"\n\u21B3 {l2}" if l2 else "")
        if not st_msg:
            st_msg="\U0001F4C0 Processing..."
    except Exception:
        st_msg=f"\U0001F4C0 {meta.get('show_title') or 'Processing...'}"
    st_mid=None
    try:
        resp=_q.urlopen(_q.Request(f"{_TBASE}{K1}/sendMessage",data=_u.urlencode({"chat_id":K2,"text":st_msg}).encode(),method="POST"),timeout=30)
        jm=_j.loads(resp.read().decode())
        if jm.get("ok"):
            st_mid=jm["result"].get("message_id")
            _p("[dbg] status message sent")
    except _e.HTTPError as ex:
        _p(f"[dbg] status msg fail: HTTP {ex.code}: {ex.read().decode()[:150]}")
    except Exception as ex:
        _p(f"[dbg] status msg fail: {str(ex)[:120]}")

    # Retry loop: max 3 attempts, har attempt fresh link
    _ATT=3
    for _att in range(1,_ATT+1):
        if _att>1:
            _p(f"[!] retry {_att-1}/{_ATT} — fresh link bana raha hoon...")
            _del_job(job)
            _t.sleep(5*_att)
            link,name,size,q,quals=_make_item_link(eid,meta.get("title","item"),se_tag)
            if not link:
                _p("[x] link failed on retry")
                continue
            job=link.rstrip("/").split("/")[-1]
            _p(f"   ready | {size/(1024*1024):.0f} MB | {q}")
            cap=_caption(meta,q,_TGT or K5,web,thumb or "",size or 0,meta.get("duration") or 0)
        _p(f"[*] pushing... (attempt {_att})")
        # download + push (pyrogram -> telethon -> bot fallback)
        if _PSESS and _KID and _KHASH:
            tmp="/tmp/up.mp4"
            _p("[*] downloading from katfile (pyrogram path)...")
            with _q.urlopen(_q.Request(link,headers={"User-Agent":_UA}),timeout=1800) as resp:
                with open(tmp,"wb") as f:
                    while True:
                        c=resp.read(1<<20)
                        if not c:
                            break
                        f.write(c)
            _p(f"   {_o.path.getsize(tmp)/(1024*1024):.0f} MB")
            msg,err=_push_pyrogram(tmp,cap,thumb,name=name or "video.mp4")
            if not msg and _KSESS and not _NOFB:
                _p(f"[!] pyrogram fail ({err}) — telethon fallback...")
                msg,err=_push_telethon(tmp,cap,thumb,name=name or "video.mp4")
            elif not msg and _NOFB:
                _p(f"[!] pyrogram fail ({err}) — NO_FALLBACK on, telethon skip")
            try:
                _o.remove(tmp)
            except Exception:
                pass
        elif _KSESS and _KID and _KHASH:
            tmp="/tmp/up.mp4"
            _p("[*] downloading from katfile (telethon path)...")
            with _q.urlopen(_q.Request(link,headers={"User-Agent":_UA}),timeout=1800) as resp:
                with open(tmp,"wb") as f:
                    while True:
                        c=resp.read(1<<20)
                        if not c:
                            break
                        f.write(c)
            _p(f"   {_o.path.getsize(tmp)/(1024*1024):.0f} MB")
            msg,err=_push_telethon(tmp,cap,thumb,name=name or "video.mp4")
            try:
                _o.remove(tmp)
            except Exception:
                pass
        else:
            _p("[!] KEY_18 session nahi hai — bot URL path (sirf <20MB chalega)")
            rel_url,rel_tag=_relay(link,name or "video.mp4")
            if not rel_url:
                _p("[x] relay fail")
                _del_job(job)
                _y.exit(1)
            msg,err=_push(rel_url,cap,thumb,fname=name or "video.mp4")
            if not msg and thumb:
                msg,err=_push(rel_url,cap,None,fname=name or "video.mp4")
            if rel_tag:
                _relay_cleanup(rel_tag)
        if not msg:
            _p(f"[x] push fail (attempt {_att}): {err}")
            _del_job(job)
            if _att>=_ATT:
                _y.exit(1)
            continue
        break

    
    fid=""
    if msg.get("video"):
        fid=msg["video"].get("file_id","")
    mid=msg.get("message_id")
    if st_mid:
        try:
            _q.urlopen(_q.Request(f"{_TBASE}{K1}/editMessageText",
                data=_u.urlencode({"chat_id":K2,"message_id":st_mid,
                    "text":st_msg+"\n\u2705 Upload complete"}).encode(),method="POST"),timeout=30)
        except Exception:
            pass
    # Bot API file_id (AAM... se shuru) ho tabhi worker permanent URL kaam karega;
    # telethon ka numeric id bot se fetch nahi hota — turl hi kaafi hai
    # Bot API file_id capture — bot channel ka admin hai, to channel_post
    # update me Bot-format file_id milta hai (worker /v/ ke liye zaroori)
    bot_fid=""
    try:
        off=0
        for _u_att in range(12):
            resp=_q.urlopen(_q.Request(f"{_TBASE}{K1}/getUpdates?timeout=5&offset={off}",headers={"User-Agent":_UA}),timeout=35)
            upd=_j.loads(resp.read().decode())
            got=False
            for u in upd.get("result",[]):
                off=u.get("update_id",0)+1
                cp=u.get("channel_post") or {}
                if cp.get("message_id")==mid:
                    doc=cp.get("document") or {}
                    if doc.get("file_id"):
                        bot_fid=doc["file_id"]
                        got=True
                        break
            if bot_fid:
                break
            if not got:
                break
        if bot_fid:
            _p(f"[dbg] bot file_id captured ({bot_fid[:20]}...)")
        else:
            _p("[!] bot file_id nahi mila — permanent URL skip")
    except Exception as ex:
        _p(f"[!] bot file_id capture fail: {str(ex)[:80]}")
    perm=f"{K4}/v/{bot_fid}" if (K4 and bot_fid and (bot_fid.startswith("BQAC") or ":" in bot_fid)) else ""
    if perm:
        try:
            _q.urlopen(_q.Request(f"{_TBASE}{K1}/editMessageCaption",data=_u.urlencode({"chat_id":K2,"message_id":mid,"caption":cap+f"\n\U0001F4BE Permanent: {perm}","parse_mode":"HTML"}).encode(),method="POST"),timeout=60)
        except Exception:
            pass
    _doc={"id":eid,"show":meta.get("show_title",""),"franchise":meta.get("franchise",""),
          "season":meta.get("season"),"episode":meta.get("episode"),
          "title":meta.get("title",""),"quality":q,"qualities":quals,
          "lang":meta.get("lang",""),"category":meta.get("category",""),
          "type":meta.get("type",""),"thumb":thumb or "","fid":fid,"bot_fid":bot_fid,"mid":mid,
          "turl":_turl(mid) if mid else "","perm":perm,"web":web,
          "size":size,"at":int(_t.time())}
    _store.save_item(_doc)
    _sb_save(_doc)
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