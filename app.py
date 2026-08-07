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
    from telethon import TelegramClient, utils as _tlu
    from telethon.sessions import StringSession
    _HAS_TT=True
except ImportError:
    try:
        _s.check_call([_y.executable,"-m","pip","install","-q","telethon"])
        from telethon import TelegramClient, utils as _tlu
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

_K3ENV=K3
_K3SRC="env"
def _sb_get_token():
    if not (_SBURL and _SBKEY):
        return None
    try:
        url=f"{_SBURL}/rest/v1/progress?select=state&id=eq.token&limit=1"
        req=_q.Request(url,headers={"apikey":_SBKEY,"Authorization":f"Bearer {_SBKEY}"})
        with _q.urlopen(req,timeout=15) as r:
            arr=_j.loads(r.read().decode())
            if arr and arr[0].get("state",{}).get("token"):
                return arr[0]["state"]["token"]
    except Exception:
        pass
    return None
def _sb_save_token():
    if not (_SBURL and _SBKEY):
        return
    try:
        row={"id":"token","state":{"token":K3,"at":int(_t.time())}}
        url=f"{_SBURL}/rest/v1/progress"
        req=_q.Request(url,data=_j.dumps(row).encode(),method="POST",
                       headers={"apikey":_SBKEY,"Authorization":f"Bearer {_SBKEY}",
                                "Content-Type":"application/json",
                                "Prefer":"resolution=merge-duplicates"})
        with _q.urlopen(req,timeout=20) as r:
            _p(f"[ok] token synced ({r.status})")
    except Exception as ex:
        _p(f"[!] token sync fail: {str(ex)[:50]}")
try:
    _tk=_sb_get_token()
    if _tk:
        K3=_tk
        _K3SRC="sb"
        _p("[ok] token: sb")
except Exception:
    pass
if _K3SRC=="env":
    _p("[ok] token: env")
def _k3_fallback():
    """Supabase token fail ho to env wala try karo (ek baar)."""
    global K3,_K3SRC
    if _K3SRC=="sb" and _K3ENV:
        K3=_K3ENV
        _K3SRC="env"
        _p("[!] supabase token fail — env KEY_3 try")
        return True
    return False

def _sb_health(result,reason=""):
    if not (_SBURL and _SBKEY):
        return
    try:
        row={"id":"health","state":{"result":result,"at":int(_t.time()),"reason":reason[:200]}}
        url=f"{_SBURL}/rest/v1/progress"
        req=_q.Request(url,data=_j.dumps(row).encode(),method="POST",
                       headers={"apikey":_SBKEY,"Authorization":f"Bearer {_SBKEY}",
                                "Content-Type":"application/json",
                                "Prefer":"resolution=merge-duplicates"})
        with _q.urlopen(req,timeout=20) as r:
            pass
    except Exception:
        pass
def _sb_pick(eid,stage="link"):
    if not (_SBURL and _SBKEY):
        return
    try:
        row={"id":"pick","state":{"eid":eid,"stage":stage,"at":int(_t.time())}}
        url=f"{_SBURL}/rest/v1/progress"
        req=_q.Request(url,data=_j.dumps(row).encode(),method="POST",
                       headers={"apikey":_SBKEY,"Authorization":f"Bearer {_SBKEY}",
                                "Content-Type":"application/json",
                                "Prefer":"resolution=merge-duplicates"})
        with _q.urlopen(req,timeout=20) as r:
            pass
    except Exception:
        pass
def _sb_pick_clear():
    if not (_SBURL and _SBKEY):
        return
    try:
        row={"id":"pick","state":{"eid":"","stage":"","at":0}}
        url=f"{_SBURL}/rest/v1/progress"
        req=_q.Request(url,data=_j.dumps(row).encode(),method="POST",
                       headers={"apikey":_SBKEY,"Authorization":f"Bearer {_SBKEY}",
                                "Content-Type":"application/json",
                                "Prefer":"resolution=merge-duplicates"})
        with _q.urlopen(req,timeout=20) as r:
            pass
    except Exception:
        pass
def _sb_pick_stale():
    """Pichhla run upload ke beech crash hua? (pick stage=upload, 15 min+ purana)"""
    if not (_SBURL and _SBKEY):
        return None
    try:
        url=f"{_SBURL}/rest/v1/progress?select=state&id=eq.pick&limit=1"
        req=_q.Request(url,headers={"apikey":_SBKEY,"Authorization":f"Bearer {_SBKEY}"})
        with _q.urlopen(req,timeout=15) as r:
            arr=_j.loads(r.read().decode())
            st=arr[0].get("state",{}) if arr else {}
            eid=st.get("eid","")
            stage=st.get("stage","")
            at=st.get("at",0)
            if eid and at and int(_t.time())-at>900 and stage=="upload":
                return {"eid":eid,"at":at}
    except Exception:
        pass
    return None

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
_SPLITPART=1900*1024*1024
try:
    _spm=_o.environ.get("SPLIT_PART_MB","").strip()
    if _spm:
        _SPLITPART=int(_spm)*1024*1024
except Exception:
    pass
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
def _auth_me_ok(tok=None):
    """Token sach mein zinda hai? /auth/me Bearer 200 = alive"""
    tok=tok or K3
    try:
        st,body=_req_api("/auth/me",headers={"Authorization":f"Bearer {tok}"})
        return st==200
    except Exception:
        return False

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
def _sb_save(doc,status="done"):
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
            "status":status,"at":int(_t.time())}
        url=f"{_SBURL}/rest/v1/episodes"
        req=_q.Request(url,data=_j.dumps(row).encode(),method="POST",
                       headers={"apikey":_SBKEY,"Authorization":f"Bearer {_SBKEY}",
                                "Content-Type":"application/json",
                                "Prefer":"resolution=merge-duplicates"})
        with _q.urlopen(req,timeout=30) as r:
            _p(f"[ok] supabase save ({r.status})")
    except Exception as ex:
        _p(f"[!] supabase save fail: {str(ex)[:80]}")

def _relay_cleanup_old():
    """Purane GitHub releases delete (24h+ purane) — repo clean rahega."""
    try:
        repo=_o.environ.get("GITHUB_REPOSITORY","")
        if not repo: return
        now=int(_t.time()*1000)
        out=_s.run(["gh","release","list","--repo",repo,"--limit","30"],capture_output=True,text=True)
        for line in out.stdout.splitlines():
            tag=line.split("\t")[0].strip() if "\t" in line else line.split()[0].strip()
            if not tag.startswith("rel-"): continue
            try:
                ts=int(tag[4:])
            except Exception:
                continue
            if now-ts > 86400000:  # 24h
                _s.run(["gh","release","delete",tag,"--yes","--repo",repo],capture_output=True,text=True)
                _p(f"[*] cleanup: {tag} deleted (24h+ old)")
    except Exception as ex:
        _p(f"[!] cleanup fail: {str(ex)[:60]}")

def _store_has_show(show_title):
    """Kya is show ka koi episode pehle se done hai?"""
    if not show_title:
        return True
    if _store.mongo is not None:
        try:
            return _store.db.episodes.count_documents({"show": show_title}) > 0
        except Exception:
            pass
    return True

def _show_poster(pick):
    """Naye show ka poster channel me bhejo + pin (dashboard/directory ke liye)."""
    if not (_HAS_PY and _KID and _KHASH and _PSESS):
        return
    show=pick.get("show") or {}
    title=show.get("title") or pick.get("meta",{}).get("show_title","")
    if title=="Doraemon":
        title="Doraemon (HUNGAMA)"
    img=show.get("image") or ""
    seasons=pick.get("seasons") or []
    tot_eps=0
    for s in seasons:
        try:
            eps=_eps(show.get("_id",""),s.get("_id",""))
            tot_eps+=len(eps)
        except Exception:
            pass
    n_seasons=len([s for s in seasons if (s.get("seasonNumber") or 0)!=0]) or len(seasons)
    if not img:
        _p("[!] poster: no image")
        return
    _p(f"[*] poster: {title} (S{n_seasons} | Ep{tot_eps})")
    tmp="/tmp/poster.jpg"
    try:
        with _q.urlopen(_q.Request(img,headers={"User-Agent":_UA}),timeout=60) as resp:
            with open(tmp,"wb") as f:
                f.write(resp.read())
    except Exception as ex:
        _p(f"[!] poster download fail: {str(ex)[:80]}")
        return
    cap=f"<b>{_esc(title)}</b>\nTotal \u2022 S{n_seasons} | Ep{tot_eps}"
    async def _do():
        app=_Pyro(":memory:",api_id=int(_KID),api_hash=_KHASH,session_string=_PSESS,
                  max_concurrent_transmissions=_CC)
        try:
            await app.start()
            ent=None
            try:
                ent=await app.get_chat(int(K2))
            except Exception:
                async for d in app.get_dialogs():
                    if d.chat and d.chat.id==int(K2):
                        ent=d.chat
                        break
            if ent is None:
                return
            msg=await app.send_photo(ent.id if hasattr(ent,"id") else ent,tmp,caption=cap,parse_mode=_PM.HTML)
            try:
                await app.pin_chat_message(ent.id,msg.id)
            except Exception:
                pass
            _p("[ok] poster sent + pinned")
        except Exception as ex:
            _p(f"[!] poster fail: {str(ex)[:80]}")
        finally:
            try:
                await app.stop()
            except Exception:
                pass
    try:
        _ac.get_event_loop().run_until_complete(_do())
    except RuntimeError:
        import nest_asyncio
        try:
            nest_asyncio.apply()
        except Exception:
            pass
        try:
            _ac.get_event_loop().run_until_complete(_do())
        except Exception:
            pass

def _movie_poster(meta):
    """Movie ka poster send karo + pin (title + release year) — docs se PEHLE."""
    if not (_HAS_PY and _KID and _KHASH and _PSESS):
        return
    title=meta.get("title") or ""
    img=meta.get("image") or ""
    year=meta.get("releaseYear") or 0
    if not img:
        _p("[!] movie poster: no image")
        return
    cap=f"\U0001F3AC <b>{_esc(title)}</b>"
    if year:
        cap+=f"\n\U0001F4C5 <b>{year}</b>"
    _p(f"[*] movie poster: {title} ({year})")
    tmp="/tmp/mposter.jpg"
    try:
        with _q.urlopen(_q.Request(img,headers={"User-Agent":_UA}),timeout=60) as resp:
            with open(tmp,"wb") as f:
                f.write(resp.read())
    except Exception as ex:
        _p(f"[!] movie poster download fail: {str(ex)[:80]}")
        return
    async def _do():
        app=_Pyro(":memory:",api_id=int(_KID),api_hash=_KHASH,session_string=_PSESS,
                  max_concurrent_transmissions=_CC)
        try:
            await app.start()
            ent=None
            try:
                ent=await app.get_chat(int(K2))
            except Exception:
                async for d in app.get_dialogs():
                    if d.chat and d.chat.id==int(K2):
                        ent=d.chat
                        break
            if ent is None:
                return
            msg=await app.send_photo(ent.id if hasattr(ent,"id") else ent,tmp,caption=cap,parse_mode=_PM.HTML)
            try:
                await app.pin_chat_message(ent.id if hasattr(ent,"id") else ent,msg.id)
                _p("[ok] movie poster sent + pinned")
            except Exception:
                _p("[ok] movie poster sent (pin fail)")
        except Exception as ex:
            _p(f"[!] movie poster fail: {str(ex)[:80]}")
        finally:
            try:
                await app.stop()
            except Exception:
                pass
    try:
        _ac.get_event_loop().run_until_complete(_do())
    except RuntimeError:
        import nest_asyncio
        try:
            nest_asyncio.apply()
        except Exception:
            pass
        try:
            _ac.get_event_loop().run_until_complete(_do())
        except Exception:
            pass

def _relay_episode(ep_id):
    """Dashboard 'Get Link' → TG se download → public link (GitHub Release/litterbox).
    Link + expiry Supabase me save. Split parts merge hokar ek file."""
    _relay_cleanup_old()
    if not (_PSESS and _KID and _KHASH):
        _p("[x] relay: pyrogram session missing (KEY_19)")
        return
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
            msg1=msgs[0] if isinstance(msgs,list) and msgs else msgs
            if not msg1:
                return None,"no message"
            try:
                path=await msg1.download()
            except TypeError:
                path=await msg1.download(file_path="/tmp/relay_dl.bin")
            if isinstance(path,list):
                path=path[0] if path else None
            if not path:
                return None,"no media"
            fsz=_o.path.getsize(path)
            _p(f"[*] relay: downloaded {fsz/(1024*1024):.0f} MB")
            fname=_o.path.basename(path) or ((rec.get("title") or "video")[:60]+".mp4")
            fname=_r.sub(r'[^A-Za-z0-9._-]+',"_",fname) or "video.mp4"
            repo=_o.environ.get("GITHUB_REPOSITORY","")
            link=None
            if repo:
                tag="rel-"+str(int(_t.time()*1000))
                r1=_s.run(["gh","release","create",tag,"--repo",repo,"--title",tag,"--notes","temp"],capture_output=True,text=True)
                if r1.returncode!=0:
                    _p(f"[!] gh create fail: {r1.stderr.strip()[:200]}")
                r2=_s.run(["gh","release","upload",tag,path,"--repo",repo,"--clobber"],capture_output=True,text=True)
                if r2.returncode!=0:
                    _p(f"[!] gh upload fail: {r2.stderr.strip()[:200]}")
                if r1.returncode==0 and r2.returncode==0:
                    link=f"https://github.com/{repo}/releases/download/{tag}/{fname}"
                    _p(f"[*] relay: github release ok")
            if not link:
                resp=_s.run(["curl","-s","--max-time","900","-F","reqtype=fileupload","-F","time=24h","-F",f"fileToUpload=@{path}","https://litterbox.catbox.moe/resources/internals/api.php"],capture_output=True,text=True,timeout=950)
                lb=resp.stdout.strip()
                if lb.startswith("http"):
                    link=lb
                    _p(f"[*] relay: litterbox ok")
                else:
                    _p(f"[!] litterbox fail: {lb[:100]}")
                    for _try in range(2):
                        _t.sleep(5)
                        resp=_s.run(["curl","-s","--max-time","900","-F","reqtype=fileupload","-F","time=24h","-F",f"fileToUpload=@{path}","https://litterbox.catbox.moe/resources/internals/api.php"],capture_output=True,text=True,timeout=950)
                        lb=resp.stdout.strip()
                        if lb.startswith("http"):
                            link=lb
                            _p(f"[*] relay: litterbox ok (retry {_try+1})")
                            break
                        _p(f"[!] litterbox retry {_try+1} fail: {lb[:80]}")
            try:
                _o.remove(path)
            except Exception:
                pass
            if not link:
                return None,"upload fail"
            expires=int(_t.time())+86400  # 24h
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
    is_mv=eid.startswith("movie:")
    eid2=eid[6:] if is_mv else eid
    if is_mv:
        j=_json(f"/movies/{eid2}")
        if not j:
            return {}
        d=j.get("data") or {}
        ttl=d.get("title") or ""
        return {"title":ttl,"image":d.get("image") or "","season":None,"episode":None,
                "show_title":_clean_title(ttl),"franchise":_franchise(ttl),
                "duration":int(d.get("durationMinutes") or 0),
                "category":d.get("category") or "","type":d.get("type") or "movie",
                "lang":_detect_lang(ttl),"releaseYear":d.get("releaseYear") or 0}
    j=_json(f"/shows/episode/{eid2}")
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

def _all_ordered_candidates(shows):
    """MULTI-REPO: full ordered episode list (done/claimed included) — seq mapping stable."""
    out=[]
    for show in shows:
        sid=show["_id"]
        seasons=_seasons(sid)
        if not _S0:
            seasons=[s for s in seasons if (s.get("seasonNumber") or 0)!=0]
        for season in seasons:
            eps=_eps(sid,season["_id"])
            for ep in eps:
                out.append(ep["_id"])
    return out

def _claim_next(cands, done):
    """MULTI-REPO: mongo atomic unique claim — har run ko alag episode.
    claims collection {_id: eid, at} — unique _id = lock (duplicate insert fail)."""
    try:
        from pymongo.errors import DuplicateKeyError as _DKE
        # stale claims cleanup (>30 min — crash recovery)
        try:
            _store.db.claims.delete_many({"at":{"$lt":int(_t.time())-1800}})
        except Exception:
            pass
        now=int(_t.time())
        for cid in cands:
            if cid in done:
                continue
            try:
                _store.db.claims.insert_one({"_id":cid,"at":now})
                return cid, (cands.index(cid)+1)  # seq = global ordered position
            except _DKE:
                continue  # kisi aur ne claim kiya — agli try
        return None, None
    except Exception as ex:
        _p(f"[!] claim fail ({str(ex)[:60]}) — fallback sequential")
        return None, None

def _pick(shows,done):
    """Agli item pick karo — modes: ordered/random/popular.
    Ek show complete tabhi hota hai jab uske saare episodes uploaded hain.
    Language filter bhi lagta hai (hindi_only/all)."""
    if _ITEM:
        m=_meta(_ITEM)
        return {"id":_ITEM,"meta":m,"ovr":True}
    if _o.environ.get("MULTI_REPO","1").strip()=="1":
        cands=_all_ordered_candidates(shows)
        cid,seq=_claim_next(cands,done)
        if cid is None:
            _p("[*] sab claimed/done.")
            return None
        m=_meta(cid)
        if not m.get("title"):
            m["title"]="Episode"
        if not _lang_ok(m):
            _p(f"[!] claimed lang fail — skip {cid}")
            try:
                _store.db.claims.delete_one({"_id":cid})
            except Exception:
                pass
            return None
        return {"id":cid,"meta":m,"ovr":True,"seq":seq}
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
    if str(pick.get("id","")).startswith("movie:"):
        midx=pick["id"][6:]
        md=list(_store.state.get("md",[]))
        if midx not in md:
            md.append(midx)
            _store.state["md"]=md
    _store._save()
    try:
        if _SBURL and _SBKEY:
            row={"id":"main","state":_store.state}
            url2=f"{_SBURL}/rest/v1/progress"
            req=_q.Request(url2,data=_j.dumps(row).encode(),method="POST",
                           headers={"apikey":_SBKEY,"Authorization":f"Bearer {_SBKEY}",
                                    "Content-Type":"application/json",
                                    "Prefer":"resolution=merge-duplicates"})
            with _q.urlopen(req,timeout=20) as r:
                _p(f"[ok] progress saved ({r.status})")
    except Exception as ex:
        _p(f"[!] progress save fail: {str(ex)[:60]}")
def _make_item_link(eid,title,se_tag):
    """Movie/episode link banao. Return: (link,name,size,q_label,qualities)"""
    is_movie=eid.startswith("movie:")
    eid2=eid[6:] if is_movie else eid
    content=f"movie:{eid2}" if is_movie else f"episode:{eid2}"
    # JWT RESILIENCE: 403/401 pe pehle fresh PoW retries (PoW expiry race hai) —
    # turant token_expired flag mat karo. Sirf /auth/me bhi fail ho to token dead.
    for _att in range(4):
        ch=_challenge(content)
        ph={}
        if ch and ch.get("nonce"):
            sol=_pow(ch["nonce"],ch.get("bits",16))
            ph={"X-Pow-Nonce":ch["nonce"],"X-Pow-Solution":sol}
        hdrs={"X-Challenge-Token":K3,"Authorization":f"Bearer {K3}","X-Challenge-Retry":"true"}
        hdrs.update(ph)
        path=f"/movies/{eid2}/links" if is_movie else f"/shows/episode/{eid2}/links"
        st,body=_req_api(path,headers=hdrs)
        if st==200:
            break
        if st in (401,403) and _att<2:
            _p(f"[x] links HTTP {st} (att {_att+1}) — fresh PoW retry...")
            _t.sleep(2)
            continue
        if st in (401,403):
            # token sach mein dead? /auth/me check
            _alive=_auth_me_ok()
            if not _alive and _att==2 and _k3_fallback():
                _p("[*] token dead — env fallback try...")
                continue
            if _alive:
                _sb_health("error",f"links HTTP {st} (transient)")
            else:
                _sb_health("token_expired",f"links HTTP {st} + auth/me dead")
            _p(f"[x] links HTTP {st} (alive={_alive})")
        else:
            _sb_health("error",f"links HTTP {st}")
        return None,None,0,"",[]
    try:
        _sb_save_token()  # jo token kaam kiya usse Supabase me sync (dashboard/latest)
    except Exception:
        pass
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
    if repo:
        tag="rel-"+str(int(_t.time()*1000))
        r1=_s.run(["gh","release","create",tag,"--repo",repo,"--title",tag,"--notes","temp"],capture_output=True,text=True)
        r2=_s.run(["gh","release","upload",tag,tmp,"--repo",repo,"--clobber","--name="+name],capture_output=True,text=True)
        if r1.returncode==0 and r2.returncode==0:
            _p(f"[*] relay: github release {tag} ok")
            return f"https://github.com/{repo}/releases/download/{tag}/{name}",tag
        _p(f"[!] gh release fail ({r1.returncode}/{r2.returncode}) — litterbox try")
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
            _p("[*] telethon: uploading (FastTelethon parallel)...")
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
                    _p(f"   upload {pct}% ({c/(1024*1024):.0f}/{t/(1024*1024):.0f} MB) | speed {spd:.1f} MB/s",flush=True)
            # FastTelethon parallel upload (multiple connections — 3-5x fast)
            try:
                from FastTelethon import upload_file as _ft_upload
                from telethon.tl.types import DocumentAttributeFilename as _DAF
                with open(path,"rb") as _fh:
                    up=await _ft_upload(client,_fh,progress_callback=_prog)
                up=_tlu.get_input_media(up,force_document=True,attributes=[_DAF(file_name=name or "video.mp4")])
            except Exception as _ex:
                _p(f"[!] FastTelethon fail ({str(_ex)[:60]}) — normal upload fallback")
                up=await client.upload_file(path,part_size_kb=1024,file_name=name,
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

def _bot_file_id(dc_id,media_id,access_hash,file_reference):
    """MTProto document -> Bot API file_id (pyrogram FileId v4 format, roundtrip verified)"""
    try:
        import struct as _st, base64 as _b64
        FILE_REFERENCE_FLAG=1<<25
        ft=5|FILE_REFERENCE_FLAG
        buf=_st.pack("<ii",ft,dc_id)
        fr=file_reference or b""
        if len(fr)<=253:
            buf+=bytes([len(fr)])+fr+b"\x00"*(-(len(fr)+1)%4)
        else:
            buf+=bytes([254])+len(fr).to_bytes(3,"little")+fr+b"\x00"*(-len(fr)%4)
        buf+=_st.pack("<qq",media_id,access_hash)
        buf+=_st.pack("<ii",30,4)+_st.pack("<bb",30,4)
        # rle (pyrogram-exact)
        r=[];n=0
        for b in buf:
            if not b:
                n+=1
            else:
                if n:
                    r.extend((0,n));n=0
                r.append(b)
        if n:
            r.extend((0,n))
        return _b64.urlsafe_b64encode(bytes(r)).decode().strip("=")
    except Exception:
        return ""

def _push_multibot(path,caption,thumb=None,name="video.mp4"):
    """MULTI-SESSION bot upload — same bot ke N auth-key sessions, file parts
    RANGE-wise split, har session apne pipelined senders se upload (FastTelethon.
    upload_file_multi — proven: 2 sessions ~12-16 MB/s vs single ~4-8).
    Sessions Supabase se aati hain (make_bot_sessions.py ne banayi).
    Fallback: caller _push_telethon use karega."""
    if not (_KID and _KHASH and _SBURL and _SBKEY):
        return None,"multibot config missing"
    try:
        from telethon import TelegramClient as _TLC
        from telethon.sessions import StringSession as _TSS
        from telethon.tl.types import DocumentAttributeFilename as _DAF
        from FastTelethon import upload_file_multi as _ft_multi
    except Exception as ex:
        return None,f"multibot imports fail: {str(ex)[:60]}"
    # Supabase se sessions load
    try:
        url=f"{_SBURL}/rest/v1/progress?select=state&id=eq.bot_sessions&limit=1"
        req=_q.Request(url,headers={"apikey":_SBKEY,"Authorization":f"Bearer {_SBKEY}"})
        with _q.urlopen(req,timeout=30) as r:
            docs=_j.loads(r.read().decode())
        st=(docs[0].get("state") or {}) if docs else {}
    except Exception as ex:
        return None,f"multibot sb fail: {str(ex)[:60]}"
    bots={k:v for k,v in st.items() if isinstance(v,list) and len(v)>=2}
    if not bots:
        return None,"multibot: no bot with >=2 sessions"
    # round-robin: filename hash se bot pick
    keys=sorted(bots.keys())
    bot=keys[sum(ord(c) for c in (name or "x")+_o.environ.get("GITHUB_REPOSITORY",""))%len(keys)]
    sesses=bots[bot][:4]  # max 4 sessions
    n=len(sesses)
    fsz=_o.path.getsize(path)
    _p(f"[*] multibot: {bot} x{n} sessions | {fsz/(1024*1024):.0f} MB")
    # thumb download
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
    async def _do():
        clients=[]
        try:
            for ss in sesses:
                c=_TLC(_TSS(ss),int(_KID),_KHASH,connection_retries=2)
                await c.connect()
                clients.append(c)
            ent=await clients[0].get_entity(int(K2))
            _st=[_t.time(),0,0]
            def _prog(c,t):
                now=_t.time()
                if now-_st[0]>=10 or c>=t:
                    dt=now-_st[0]
                    spd=((c-_st[1])/(1024*1024)/dt) if dt>0 else 0
                    _st[0]=now;_st[1]=c
                    _p(f"   upload {c*100//t}% ({c/(1024*1024):.0f}/{t/(1024*1024):.0f} MB) | {spd:.1f} MB/s",flush=True)
            conns=15 if n>=3 else 20
            pkb=1024 if fsz>900*1024*1024 else None  # bade files: 1MB parts (part count < 4000)
            with open(path,"rb") as fh:
                up=await _ft_multi(clients,fh,progress_callback=_prog,
                                   conns_per_client=conns,part_size_kb=pkb)
            msg=await clients[0].send_file(ent,up,force_document=True,thumb=thumb_path or None,
                                           attributes=[_DAF(file_name=name or "video.mp4")],
                                           caption=caption,parse_mode="html")
            fid=""
            bfid=""
            if getattr(msg,"video",None) is not None:
                fid=str(msg.video.id)
                dv=getattr(msg,"video",None)
                if getattr(dv,"access_hash",None):
                    bfid=_bot_file_id(getattr(dv,"dc_id",0) or 0,dv.id,dv.access_hash,getattr(dv,"file_reference",b""))
            elif getattr(msg,"document",None) is not None:
                doc=getattr(msg,"document",None)
                fid=str(doc.id)
                if getattr(doc,"access_hash",None):
                    bfid=_bot_file_id(getattr(doc,"dc_id",0) or 0,doc.id,doc.access_hash,getattr(doc,"file_reference",b""))
            return {"message_id":msg.id,"video":{"file_id":fid},"bot":bot,"bot_fid":bfid},None
        except Exception as ex:
            return None,f"multibot fail: {str(ex)[:200]}"
        finally:
            for c in clients:
                try:
                    await c.disconnect()
                except Exception:
                    pass
    try:
        return _ac.get_event_loop().run_until_complete(_do())
    except RuntimeError:
        try:
            import nest_asyncio
            nest_asyncio.apply()
        except Exception:
            pass
        return _ac.get_event_loop().run_until_complete(_do())

def _sb_config():
    """config doc: {stage_ch: -100xxx} — Supabase se"""
    try:
        url=f"{_SBURL}/rest/v1/progress?select=state&id=eq.config&limit=1"
        req=_q.Request(url,headers={"apikey":_SBKEY,"Authorization":f"Bearer {_SBKEY}"})
        with _q.urlopen(req,timeout=20) as r:
            docs=_j.loads(r.read().decode())
        return (docs[0].get("state") or {}) if docs else {}
    except Exception:
        return {}

def _queue_add(entry):
    """queue entry push — progress id=queue {entries:[...]}"""
    try:
        url=f"{_SBURL}/rest/v1/progress?select=state&id=eq.queue&limit=1"
        req=_q.Request(url,headers={"apikey":_SBKEY,"Authorization":f"Bearer {_SBKEY}"})
        with _q.urlopen(req,timeout=20) as r:
            docs=_j.loads(r.read().decode())
        entries=(docs[0].get("state") or {}).get("entries",[]) if docs else []
        entries=[e for e in entries if e.get("seq")!=entry.get("seq")]
        entries.append(entry)
        row={"id":"queue","state":{"entries":entries}}
        url2=f"{_SBURL}/rest/v1/progress"
        req2=_q.Request(url2,data=_j.dumps(row).encode(),method="POST",
                       headers={"apikey":_SBKEY,"Authorization":f"Bearer {_SBKEY}",
                                "Content-Type":"application/json",
                                "Prefer":"resolution=merge-duplicates"})
        with _q.urlopen(req2,timeout=20) as r2:
            return r2.status
    except Exception:
        return 0

def _queue_entries():
    try:
        url=f"{_SBURL}/rest/v1/progress?select=state&id=eq.queue&limit=1"
        req=_q.Request(url,headers={"apikey":_SBKEY,"Authorization":f"Bearer {_SBKEY}"})
        with _q.urlopen(req,timeout=20) as r:
            docs=_j.loads(r.read().decode())
        return (docs[0].get("state") or {}).get("entries",[]) if docs else []
    except Exception:
        return []

def _queue_update(entries):
    try:
        row={"id":"queue","state":{"entries":entries}}
        url=f"{_SBURL}/rest/v1/progress"
        req=_q.Request(url,data=_j.dumps(row).encode(),method="POST",
                       headers={"apikey":_SBKEY,"Authorization":f"Bearer {_SBKEY}",
                                "Content-Type":"application/json",
                                "Prefer":"resolution=merge-duplicates"})
        with _q.urlopen(req,timeout=20) as r:
            return r.status
    except Exception:
        return 0

def _claim_release(cid):
    """fail hua claim wapas chhodo — agli run use kar sake"""
    try:
        _store.db.claims.delete_one({"_id":cid})
    except Exception:
        pass

def _poster_post(entry):
    """REAL channel pe post — user session se location-copy (instant, no re-upload)"""
    if not (_KSESS and _KID and _KHASH):
        return None,"poster: KEY_18 missing"
    try:
        from telethon import TelegramClient as _TLC
        from telethon.sessions import StringSession as _TSS
        from telethon.tl.types import InputDocumentFileLocation as _IDFL, DocumentAttributeFilename as _DAF
        import base64 as _bb
    except Exception as ex:
        return None,f"poster imports: {str(ex)[:60]}"
    fr=_bb.b64decode(entry.get("fr","")) if entry.get("fr") else b""
    async def _do():
        client=_TLC(_TSS(_KSESS),int(_KID),_KHASH)
        try:
            await client.connect()
            ent=await client.get_entity(int(K2))
            loc=_IDFL(id=int(entry["did"]),access_hash=int(entry["ah"]),file_reference=fr)
            # thumb bhi attach (URL se download)
            th=None
            if entry.get("thumb") and str(entry["thumb"]).startswith("http"):
                try:
                    tp="/tmp/pthumb.jpg"
                    with _q.urlopen(_q.Request(entry["thumb"],headers={"User-Agent":_UA}),timeout=60) as resp:
                        with open(tp,"wb") as f:
                            while True:
                                c=resp.read(1<<20)
                                if not c:
                                    break
                                f.write(c)
                    if _o.path.getsize(tp)>=1000:
                        th=tp
                except Exception:
                    th=None
            media=_tlu.get_input_media(loc,force_document=True,
                                       attributes=[_DAF(file_name=entry.get("name") or "video.mp4")])
            msg=await client.send_file(ent,media,force_document=True,thumb=th or None,
                                       caption=entry.get("caption") or "",parse_mode="html")
            fid=""
            if getattr(msg,"video",None) is not None:
                fid=str(msg.video.id)
            elif getattr(msg,"document",None) is not None:
                fid=str(msg.document.id)
            return {"message_id":msg.id,"video":{"file_id":fid}},None
        except Exception as ex:
            return None,f"poster fail: {str(ex)[:150]}"
        finally:
            try:
                await client.disconnect()
            except Exception:
                pass
    try:
        return _ac.get_event_loop().run_until_complete(_do())
    except RuntimeError:
        try:
            import nest_asyncio
            nest_asyncio.apply()
        except Exception:
            pass
        return _ac.get_event_loop().run_until_complete(_do())

def _flush_poster(my_seq, eid):
    """ORDERED POSTING: jab tak previous posted nahi, wait; phir location-copy post.
    Lock = mongo postctl (atomic) — koi bhi runner pending next post kar sakta hai (crash recovery)."""
    try:
        from pymongo import ReturnDocument as _RD
    except Exception:
        _RD=None
    run_id=_o.environ.get("GITHUB_RUN_ID",str(_o.getpid()))
    deadline=_t.time()+900  # 15 min max wait
    while _t.time()<deadline:
        try:
            pc=_store.db.postctl.find_one({"_id":"post"}) or {"next_seq":1,"lock":"","lock_at":0}
        except Exception:
            _t.sleep(15)
            continue
        now=int(_t.time())
        # lock acquire / takeover
        try:
            if pc.get("lock") and pc.get("lock_at") and now-pc["lock_at"]>=240:
                _store.db.postctl.update_one({"_id":"post","lock":pc["lock"]},
                                             {"$set":{"lock":run_id,"lock_at":now}})
            elif not pc.get("lock"):
                _store.db.postctl.update_one({"_id":"post","lock":""},
                                             {"$set":{"lock":run_id,"lock_at":now}})
            pc=_store.db.postctl.find_one({"_id":"post"}) or {}
            if pc.get("lock")!=run_id:
                _t.sleep(15)
                continue
        except Exception:
            _t.sleep(15)
            continue
        # next_seq ka entry dhoondo
        nxt=int(pc.get("next_seq") or 1)
        entries=_queue_entries()
        entry=next((e for e in entries if int(e.get("seq") or 0)==nxt and e.get("status")=="staged"),None)
        if entry:
            msg,err=_poster_post(entry)
            if not msg:
                _p(f"[!] poster post fail seq={nxt}: {err}")
                try:
                    _store.db.postctl.update_one({"_id":"post","lock":run_id},{"$set":{"lock":"","lock_at":0}})
                except Exception:
                    pass
                _t.sleep(30)
                continue
            # save episode record (real channel mid)
            meta=entry.get("meta") or {}
            _doc={"id":entry.get("eid"),"show":meta.get("show_title",""),"franchise":meta.get("franchise",""),
                  "season":meta.get("season"),"episode":meta.get("episode"),"title":meta.get("title",""),
                  "quality":entry.get("q",""),"qualities":entry.get("quals",[]),
                  "lang":meta.get("lang",""),"category":meta.get("category",""),
                  "thumb":entry.get("thumb") or "","fid":(msg.get("video") or {}).get("file_id",""),
                  "bot_fid":"","mid":msg.get("message_id"),
                  "turl":_turl(msg.get("message_id")) if msg.get("message_id") else "",
                  "perm":"","web":entry.get("web",""),"size":entry.get("size",0),"at":int(_t.time())}
            try:
                _store.save_item(_doc)
            except Exception:
                pass
            try:
                _sb_save(_doc)
            except Exception:
                pass
            _p(f"[ok] ORDERED POST seq={nxt} mid={msg.get('message_id')}")
            # entry posted mark
            for e in entries:
                if int(e.get("seq") or 0)==nxt:
                    e["status"]="posted"
            _queue_update(entries)
            try:
                _store.db.postctl.update_one({"_id":"post","lock":run_id},
                                             {"$set":{"next_seq":nxt+1,"lock":"","lock_at":0}})
            except Exception:
                pass
            if nxt==my_seq:
                return msg,None  # hamara ho gaya
            continue
        else:
            # entry nahi — wo episode pehle se posted? (purana) to skip
            try:
                cands=_all_ordered_candidates(_shows(_o.environ.get("KEY_6","").strip()))
                if nxt-1 < len(cands):
                    cid=cands[nxt-1]
                    if cid in _store.done_ids():
                        _store.db.postctl.update_one({"_id":"post","lock":run_id},
                                                     {"$set":{"next_seq":nxt+1,"lock":"","lock_at":0}})
                        continue
            except Exception:
                pass
            try:
                _store.db.postctl.update_one({"_id":"post","lock":run_id},{"$set":{"lock":"","lock_at":0}})
            except Exception:
                pass
            _t.sleep(15)
    return None,"flush timeout (15 min)"

def _push_multibot_staged(path,caption,thumb=None,name="video.mp4",meta=None,eid="",seq=0,web="",size=0,q="",quals=None):
    """MULTI-REPO STAGED UPLOAD:
    1) stage channel pe multibot upload (parallel, fast)
    2) queue entry save
    3) ordered poster — real channel pe jab baari aaye (instant location-copy)
    Isse order 100% preserved + uploads parallel."""
    cfg=_sb_config()
    stage_ch=cfg.get("stage_ch") or ""
    if not stage_ch:
        return None,"multibot staged: stage_ch config nahi hai (stage_setup.py chalao)"
    try:
        from telethon import TelegramClient as _TLC
        from telethon.sessions import StringSession as _TSS
        from telethon.tl.types import DocumentAttributeFilename as _DAF
        from FastTelethon import upload_file_multi as _ft_multi
        import base64 as _bb
    except Exception as ex:
        return None,f"staged imports: {str(ex)[:60]}"
    # sessions
    try:
        url=f"{_SBURL}/rest/v1/progress?select=state&id=eq.bot_sessions&limit=1"
        req=_q.Request(url,headers={"apikey":_SBKEY,"Authorization":f"Bearer {_SBKEY}"})
        with _q.urlopen(req,timeout=30) as r:
            docs=_j.loads(r.read().decode())
        st=(docs[0].get("state") or {}) if docs else {}
    except Exception as ex:
        return None,f"staged sb: {str(ex)[:60]}"
    bots={k:v for k,v in st.items() if isinstance(v,list) and len(v)>=2}
    if not bots:
        return None,"staged: no sessions"
    keys=sorted(bots.keys())
    bot=keys[sum(ord(c) for c in (name or "x")+_o.environ.get("GITHUB_REPOSITORY",""))%len(keys)]
    sesses=bots[bot][:4]
    n=len(sesses)
    fsz=_o.path.getsize(path)
    _p(f"[*] STAGED upload: {bot} x{n} | {fsz/(1024*1024):.0f} MB -> stage")
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
    async def _do():
        clients=[]
        try:
            for ss in sesses:
                c=_TLC(_TSS(ss),int(_KID),_KHASH,connection_retries=2)
                await c.connect()
                clients.append(c)
            # stage channel resolve — access_hash se (bots ke session mein entity nahi hoti)
            try:
                from telethon.tl.functions.channels import GetChannelsRequest as _GCR
                from telethon.tl.types import InputChannel as _IC
                _sid=str(stage_ch)
                _ic_id=int(_sid[4:]) if _sid.startswith("-100") else int(_sid)  # raw id (bina -100)
                res=await clients[0](_GCR([_IC(_ic_id, int(cfg.get("stage_hash") or 0))]))
                ent=res.chats[0]
                _p(f"[*] stage resolved: {getattr(ent,'title',_sid)}")
            except Exception as _e:
                _p(f"[!] stage getchannels fail: {str(_e)[:80]} — try get_entity")
                ent=await clients[0].get_entity(int(stage_ch))
            _st=[_t.time(),0,0]
            def _prog(c,t):
                now=_t.time()
                if now-_st[0]>=10 or c>=t:
                    dt=now-_st[0]
                    spd=((c-_st[1])/(1024*1024)/dt) if dt>0 else 0
                    _st[0]=now;_st[1]=c
                    _p(f"   upload {c*100//t}% ({c/(1024*1024):.0f}/{t/(1024*1024):.0f} MB) | {spd:.1f} MB/s",flush=True)
            conns=15 if n>=3 else 20
            pkb=1024 if fsz>900*1024*1024 else None
            with open(path,"rb") as fh:
                up=await _ft_multi(clients,fh,progress_callback=_prog,
                                   conns_per_client=conns,part_size_kb=pkb)
            msg=await clients[0].send_file(ent,up,force_document=True,thumb=thumb_path or None,
                                           attributes=[_DAF(file_name=name or "video.mp4")],
                                           caption=f"STAGE seq={seq} {name}")
            # location capture
            doc=None
            if getattr(msg,"video",None) is not None:
                doc=getattr(msg,"video",None)
            elif getattr(msg,"document",None) is not None:
                doc=getattr(msg,"document",None)
            if doc is None or not getattr(doc,"access_hash",None):
                return None,"staged: location capture fail"
            entry={"seq":int(seq),"eid":eid,"status":"staged","at":int(_t.time()),
                   "did":str(doc.id),"ah":str(doc.access_hash),
                   "fr":_bb.b64encode(doc.file_reference or b"").decode(),
                   "dc":int(getattr(doc,"dc_id",0) or 0),
                   "name":name or "video.mp4","thumb":thumb or "","caption":caption,
                   "meta":meta or {},"web":web or "","size":int(size or fsz),
                   "q":q,"quals":quals or []}
            _queue_add(entry)
            _p(f"[*] staged seq={seq} — poster wait")
            return True,None
        except Exception as ex:
            return None,f"staged upload fail: {str(ex)[:200]}"
        finally:
            for c in clients:
                try:
                    await c.disconnect()
                except Exception:
                    pass
    try:
        r=_ac.get_event_loop().run_until_complete(_do())
    except RuntimeError:
        try:
            import nest_asyncio
            nest_asyncio.apply()
        except Exception:
            pass
        r=_ac.get_event_loop().run_until_complete(_do())
    if not r or not r[0]:
        return None, r[1] if r else "staged fail"
    # ab flush — ordered poster
    _p("[*] flush: ordered posting...")
    msg,err=_flush_poster(int(seq), eid)
    if not msg:
        return None, err
    fid=(msg.get("video") or {}).get("file_id","")
    bfid=""
    try:
        if fid:
            bfid=_bot_file_id(0,int(fid),0,b"") if False else ""
    except Exception:
        pass
    return {"message_id":msg.get("message_id"),"video":{"file_id":fid},"bot":bot,"bot_fid":bfid},None

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
    """Badi file ko TRUE byte-split karke media-group me upload karo (NO encoding).
    Parts: {filename}.001, .002 ... (jaise 7-Zip/RAR volumes) — player inhe join karta hai.
    Caption sirf last part par. Returns: list of {part, fid, mid} ya []"""
    if not (_HAS_PY and _KID and _KHASH and _PSESS):
        return []
    # thumbnail download (sab parts par lagega) — JPEG chahiye, ffmpeg se 320x scale
    thumb_path=None
    if thumb and str(thumb).startswith("http"):
        try:
            tp="/tmp/thumb.jpg"
            with _q.urlopen(_q.Request(thumb,headers={"User-Agent":_UA}),timeout=60) as resp:
                with open(tp,"wb") as f:
                    f.write(resp.read())
            _s.run(["ffmpeg","-y","-i",tp,"-vf","scale=320:-2","-q:v","5",tp+".s.jpg"],
                   check=False,capture_output=True)
            if _o.path.exists(tp+".s.jpg"):
                thumb_path=tp+".s.jpg"
            else:
                thumb_path=tp
            _p(f"[*] thumb ready ({_o.path.getsize(thumb_path)/(1024):.0f} KB)")
        except Exception:
            thumb_path=None
    tmp="/tmp/big.mp4"
    _p("\n[*] split: downloading (aria2 parallel x8)...")
    try:
        _o.remove(tmp)
    except Exception:
        pass
    _s.run(["aria2c","-x","8","-s","8","-k","4M","-d","/tmp","-o","big.mp4",link],
           check=False)  # output stream hota hai log mein = live progress
    if not _o.path.exists(tmp) or _o.path.getsize(tmp)<1000:
        _p("[!] aria2 fail — urllib fallback")
        with _q.urlopen(_q.Request(link,headers={"User-Agent":_UA}),timeout=1800) as resp:
            with open(tmp,"wb") as f:
                while True:
                    c=resp.read(1<<20)
                    if not c:
                        break
                    f.write(c)
    sz=_o.path.getsize(tmp)
    _p(f"   {sz/(1024*1024):.0f} MB")
    outd="/tmp/parts"
    _o.makedirs(outd,exist_ok=True)
    for x in _o.listdir(outd):
        try:
            _o.remove(outd+"/"+x)
        except Exception:
            pass
    fname=(name or "video.mp4").replace("/","_")
    prefix=f"{outd}/{fname}."
    _s.run(["split","-b",str(_SPLITPART),"-d","-a","3","--numeric-suffixes=1",tmp,prefix],
           check=False,capture_output=True)
    parts=sorted(_o.listdir(outd))
    if not parts:
        _p("[x] split fail — no parts")
        return []
    _p(f"   {len(parts)} parts ({fname}.001 ...)")
    async def _do():
        app=_Pyro(":memory:",api_id=int(_KID),api_hash=_KHASH,
                  session_string=_PSESS,max_concurrent_transmissions=_CC)
        try:
            await app.start()
            me=await app.get_me()
            _p(f"[*] pyrogram: connected as {me.first_name}")
            ent=None
            try:
                ent=await app.get_chat(int(K2))
            except Exception:
                _p("[!] get_chat fail — dialogs me dhund raha hoon...")
                async for d in app.get_dialogs():
                    if d.chat and d.chat.id==int(K2):
                        ent=d.chat
                        break
            if ent is None:
                _p("[x] channel resolve fail")
                return []
            cid=ent.id if hasattr(ent,"id") else ent
            results=[]
            from pyrogram.types import InputMediaDocument
            # FAST: parallel upload (send_document + progress) -> media group (file_ids se instant)
            _p(f"[*] uploading {len(parts)} parts (parallel x{min(3,len(parts))})...")
            sem=_ac.Semaphore(min(3,len(parts)))
            async def _up_one(idx,p):
                async with sem:
                    path=f"{outd}/{p}"
                    tsz=_o.path.getsize(path)
                    t0=_t.time()
                    _last=[0]; _lt=[t0]
                    def _prog(cur,tot):
                        now=_t.time()
                        if now-_lt[0]>=10 and tot>0:
                            sp=(cur-_last[0])/(now-_lt[0])/(1024*1024)
                            _p(f"   [up] part {idx+1}/{len(parts)}: {cur/(1024*1024):.0f}/{tot/(1024*1024):.0f} MB ({cur*100//tot}%) | {sp:.1f} MB/s")
                            _last[0]=cur; _lt[0]=now
                    m=await app.send_document(cid,path,disable_notification=True,progress=_prog)
                    fid=m.document.file_id or ""
                    _p(f"   [ok] part {idx+1}/{len(parts)} uploaded ({tsz/(1024*1024):.0f} MB)")
                    return idx,fid,m.id
            ups=await _ac.gather(*[_up_one(i,p) for i,p in enumerate(parts)])
            ups.sort(key=lambda x:x[0])
            # temp messages delete
            try:
                await app.delete_messages(cid,[m_id for _,_,m_id in ups])
            except Exception:
                pass
            # media group (files already uploaded — instant)
            for ci in range(0,len(ups),10):
                chunk=ups[ci:ci+10]
                media=[]
                for idx,fid,_ in chunk:
                    is_last=(idx==len(parts)-1)
                    media.append(InputMediaDocument(fid,thumb=thumb_path,
                                                    caption=cap if is_last else None,
                                                    parse_mode=_PM.HTML if is_last else None))
                msgs=await app.send_media_group(cid,media)
                for pi,msg in enumerate(msgs):
                    fid2=""
                    if msg.document:
                        fid2=msg.document.file_id or ""
                    results.append({"part":ci+pi+1,"fid":fid2,"mid":msg.id})
                _p(f"   [ok] block {ci//10+1} sent ({len(msgs)} parts)")
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

def _auto_continue():
    """Speed mode: run complete hone ke ~60s baad agli run dispatch kar deta hai
    (agar pause nahi). Cron 5-min ka wait nahi karna padta. AUTO_CONTINUE=0 se off."""
    if _o.environ.get("AUTO_CONTINUE","1").strip()!="1":
        return
    _p("[*] auto-continue: 60s mein agli run dispatch...")
    _t.sleep(60)
    # pause check (Supabase)
    paused=False
    try:
        url=f"{_SBURL}/rest/v1/progress?select=state&id=eq.pause&limit=1"
        req=_q.Request(url,headers={"apikey":_SBKEY,"Authorization":f"Bearer {_SBKEY}"})
        with _q.urlopen(req,timeout=20) as r:
            docs=_j.loads(r.read().decode())
        if docs and (docs[0].get("state") or {}).get("paused"):
            paused=True
    except Exception:
        pass
    if paused:
        _p("[*] paused — auto-continue skip (cron resume pe dekh lega)")
        return
    gh=_o.environ.get("GITHUB_TOKEN","").strip()
    repo=_o.environ.get("GITHUB_REPOSITORY","").strip()
    my_sha=_o.environ.get("GITHUB_SHA","").strip()  # apna commit — khud ko active na samjhe
    if not gh or not repo:
        _p("[!] auto-continue: GITHUB_TOKEN/REPOSITORY missing")
        return
    # koi AUR run active to mat dispatch karo (same commit wala = khud, exclude)
    try:
        req=_q.Request(f"https://api.github.com/repos/{repo}/actions/runs?per_page=10",
                       headers={"Authorization":f"Bearer {gh}","Accept":"application/vnd.github+json"})
        with _q.urlopen(req,timeout=20) as r:
            runs=_j.loads(r.read().decode()).get("workflow_runs",[])
        active=[x for x in runs if x.get("status") in ("in_progress","queued")
                and x.get("head_sha","")!=my_sha]
        if active:
            _p(f"[*] run already active ({active[0].get('id')}) — skip")
            return
    except Exception as ex:
        _p(f"[!] gh runs check fail: {str(ex)[:60]}")
    try:
        body=_j.dumps({"event_type":"run-task"}).encode()
        req=_q.Request(f"https://api.github.com/repos/{repo}/dispatches",data=body,method="POST",
                       headers={"Authorization":f"Bearer {gh}","Accept":"application/vnd.github+json",
                                "Content-Type":"application/json"})
        with _q.urlopen(req,timeout=20) as r:
            _p(f"[ok] auto-continue: next run dispatched ({r.status})")
    except Exception as ex:
        _p(f"[!] auto-continue dispatch fail: {str(ex)[:80]}")

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
    showname=meta.get("show_title") or ""
    if showname=="Doraemon":
        showname="Doraemon (HUNGAMA)"
    is_movie=(meta.get("type") or "").startswith("movie")
    if meta.get("title"):
        lines.append(f"\U0001F3AC <b><code>{_esc(meta['title'])}</code></b>")
    if showname and not is_movie:
        se=[]
        se.append(_esc(showname))
        if meta.get("season") is not None and meta.get("episode") is not None:
            se.append(f"S{meta['season']}-E{meta['episode']}")
        lines.append("\U0001F4C0 <b><code>"+" \u00B7 ".join(se)+"</code></b>")
    lines.append(_SEP)
    if q:
        lines.append(f"\u2699\uFE0F Quality: <b>{_esc(q)}</b>")
    lines.append(f"\U0001F4AC Language: <b>{_esc(meta.get('lang') or 'Hindi')}</b>")
    sz=""
    if size:
        mb=size/(1024*1024)
        if mb>=1024:
            sz=f"{mb/1024:.1f} GB"
        else:
            sz=f"{int(round(mb))} MB"
    if duration:
        if sz:
            sz=f"{sz} \u2022 {int(duration)} min"
        else:
            sz=f"{int(duration)} min"
    if sz:
        lines.append(f"\U0001F4C2 Size: <b>{sz}</b>")
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
    # PAUSE CHECK — har repo ke runs respect karein (worker + direct cron dono)
    try:
        url=f"{_SBURL}/rest/v1/progress?select=state&id=eq.pause&limit=1"
        req=_q.Request(url,headers={"apikey":_SBKEY,"Authorization":f"Bearer {_SBKEY}"})
        with _q.urlopen(req,timeout=20) as r:
            _pd=_j.loads(r.read().decode())
        if _pd and (_pd[0].get("state") or {}).get("paused"):
            _p("[*] paused — run skip (dashboard se resume karo)")
            _y.exit(0)
    except Exception:
        pass
    try:
        gm=_q.urlopen(f"{_TBASE}{K1}/getMe",timeout=30)
        gj=_j.loads(gm.read().decode())
        _p(f"[dbg] getMe ok={gj.get('ok')} err={gj.get('description','')}")
    except Exception as ex:
        _p(f"[dbg] getMe call fail: {str(ex)[:120]}")
    stale=_sb_pick_stale()
    if stale:
        _p(f"[!] prev run died mid-upload ({stale['eid']}) — skip + alert")
        try:
            _q.urlopen(_q.Request(f"{_TBASE}{K1}/sendMessage",data=_u.urlencode({
                "chat_id":K2,"text":f"\u26A0\ufe0f Episode {stale['eid']} ka run upload ke beech crash hua tha — channel check karo. System aage badh raha hai."}).encode(),method="POST"),timeout=30)
        except Exception:
            pass
        _dead={"id":stale["eid"],"show":"","franchise":"","season":None,"episode":None,
               "title":"[died]","quality":"","qualities":[],"lang":"","category":"",
               "type":"episode","thumb":"","fid":"","bot_fid":"","mid":0,"turl":"",
               "perm":"","web":"","size":0,"at":int(_t.time())}
        _store.save_item(_dead)
        _sb_save(_dead,status="died")
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
    is_mv=eid.startswith("movie:")
    # naya show start ho raha hai? (us show ka koi episode abhi tak done nahi)
    if not is_mv:
        try:
            if not _store_has_show(meta.get("show_title","")):
                _show_poster(pick)
        except Exception:
            pass
    else:
        # movie: poster + release year + pin, docs se PEHLE
        try:
            _movie_poster(meta)
        except Exception:
            pass
    se_tag=""
    if meta.get("season") is not None and meta.get("episode") is not None:
        se_tag=f" S{meta['season']}E{meta['episode']}"
    web=f"{_WEB}movieId={eid[6:]}" if is_mv else f"{_WEB}episodeId={eid}"
    _p(f"\n> next: {meta.get('show_title','')} {se_tag.strip()} — {meta.get('title')}")
    _p(f"   id: {eid}")
    if _DRY:
        _p("\n[dry] preview only.")
        return
    _sb_pick(eid,"link")
    _p("[*] building link...")
    link,name,size,q,quals=_make_item_link(eid,meta.get("title","item"),se_tag)
    if not link:
        _sb_pick_clear()
        try:
            if _o.environ.get("MULTI_REPO","1").strip()=="1":
                _claim_release(eid)
        except Exception:
            pass
        _p("[x] link failed (KEY_3 stale?)")
        _y.exit(1)
    job=link.rstrip("/").split("/")[-1]
    _p(f"   ready | {size/(1024*1024):.0f} MB | {q} | qualities: {quals}")
    thumb=meta.get("image") or None
    cap=_caption(meta,q,_TGT or K5,web,thumb or "",size or 0,meta.get("duration") or 0)
    _sb_pick(eid,"upload")
    if size and size>_SPLIT:
        _p(f"[!] {size/(1024*1024):.0f} MB > limit — split (media group)")
        base=(name or "item").replace(".mp4","")
        results=_split_media_group(link,base,cap,thumb,name=name or "video.mp4")
        if not results:
            _p("[x] split fail")
            _del_job(job)
            try:
                if _o.environ.get("MULTI_REPO","1").strip()=="1":
                    _claim_release(eid)
            except Exception:
                pass
            _y.exit(1)
        _p1=results[0]
        _turl1=f"https://t.me/c/{str(K2).replace('-100','')}/{_p1.get('mid',0)}"
        _sd={"id":eid,"show":meta.get("show_title",""),"franchise":meta.get("franchise",""),
             "season":meta.get("season"),"episode":meta.get("episode"),
             "title":meta.get("title",""),"quality":q,"qualities":quals,
             "lang":meta.get("lang",""),"category":meta.get("category",""),
             "thumb":thumb or "","fid":_p1.get("fid",""),"bot_fid":"","mid":_p1.get("mid"),
             "turl":_turl1,"perm":"","web":web,"size":size,"at":int(_t.time())}
        _store.save_item(_sd)
        _sb_save(_sd)
        _del_job(job)
        _sb_pick_clear()
        _sb_health("ok","split")
        _advance(pick)
        _p("\n[ok] done (split). saved.")
        try:
            _auto_continue()
        except Exception as _ex:
            _p(f"[!] auto-continue err: {str(_ex)[:80]}")
        return
    # STATUS MESSAGE: default OFF — channel mein extra messages nahi chahiye
    # (STATUS_MSG=1 env se on kar sakte ho agar kabhi chahiye)
    st_mid=None
    st_msg=""
    if _o.environ.get("STATUS_MSG","").strip()=="1":
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
        try:
            resp=_q.urlopen(_q.Request(f"{_TBASE}{K1}/sendMessage",data=_u.urlencode({"chat_id":K2,"text":st_msg}).encode(),method="POST"),timeout=30)
            jm=_j.loads(resp.read().decode())
            if jm.get("ok"):
                st_mid=jm["result"].get("message_id")
                _p("[dbg] status message sent")
        except Exception as ex:
            _p(f"[dbg] status msg fail: {str(ex)[:120]}")

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
            # MULTI-REPO STAGED (parallel + ordered) ya normal multibot
            if _o.environ.get("MULTI_REPO","1").strip()=="1":
                msg,err=_push_multibot_staged(tmp,cap,thumb,name=name or "video.mp4",
                                              meta=meta,eid=eid,seq=int(pick.get("seq") or 0),
                                              web=web,size=size or 0,q=q,quals=quals)
            elif _KSESS and _KID and _KHASH:
                msg,err=_push_multibot(tmp,cap,thumb,name=name or "video.mp4")
                if not msg:
                    _p(f"[!] multibot fail ({err}) — telethon fallback...")
                    msg,err=_push_telethon(tmp,cap,thumb,name=name or "video.mp4")
                if not msg and _PSESS and not _NOFB:
                    _p(f"[!] telethon fail ({err}) — pyrogram fallback...")
                    msg,err=_push_pyrogram(tmp,cap,thumb,name=name or "video.mp4")
            else:
                msg,err=_push_pyrogram(tmp,cap,thumb,name=name or "video.mp4")
                if not msg and _KSESS and not _NOFB:
                    _p(f"[!] pyrogram fail ({err}) — telethon fallback...")
                    msg,err=_push_telethon(tmp,cap,thumb,name=name or "video.mp4")
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
                try:
                    if _o.environ.get("MULTI_REPO","1").strip()=="1":
                        _claim_release(eid)
                except Exception:
                    pass
                _y.exit(1)
            continue
        break

    
    fid=""
    if msg.get("video"):
        fid=msg["video"].get("file_id","")
    bot_fid_cap=msg.get("bot_fid","")
    mid=msg.get("message_id")
    if st_mid and st_msg:
        try:
            _q.urlopen(_q.Request(f"{_TBASE}{K1}/editMessageText",
                data=_u.urlencode({"chat_id":K2,"message_id":st_mid,
                    "text":st_msg+"\n\u2705 Upload complete"}).encode(),method="POST"),timeout=30)
        except Exception:
            pass
    bot_fid=bot_fid_cap
    _cap_tok=K1
    try:
        # multibot se post hua to USI bot ka token use karo (uske getUpdates mein channel_post dikhega)
        if msg.get("bot") and _SBURL and _SBKEY:
            url=f"{_SBURL}/rest/v1/progress?select=state&id=eq.bot_sessions&limit=1"
            req=_q.Request(url,headers={"apikey":_SBKEY,"Authorization":f"Bearer {_SBKEY}"})
            with _q.urlopen(req,timeout=30) as r:
                docs=_j.loads(r.read().decode())
            st=(docs[0].get("state") or {}) if docs else {}
            tk=(st.get("tokens") or {}).get(msg["bot"]) or ""
            if tk:
                _cap_tok=tk
    except Exception:
        pass
    if not bot_fid:
        try:
            off=0
            for _u_att in range(12):
                resp=_q.urlopen(_q.Request(f"{_TBASE}{_cap_tok}/getUpdates?timeout=5&offset={off}",headers={"User-Agent":_UA}),timeout=35)
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
    perm = f"{K4}/v/{bot_fid}" if bot_fid else ""
    _rlink=""
    try:
        if _SBURL and _SBKEY:
            url2=f"{_SBURL}/rest/v1/links?select=url,expires_at&id=eq.{_u.quote(eid)}&limit=1"
            req2=_q.Request(url2,headers={"apikey":_SBKEY,"Authorization":f"Bearer {_SBKEY}"})
            with _q.urlopen(req2,timeout=20) as r2:
                arr=_j.loads(r2.read().decode())
                if arr and arr[0].get("url") and arr[0].get("expires_at",0)>int(_t.time()):
                    _rlink=arr[0]["url"]
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
    _sb_pick_clear()
    _sb_health("ok")
    _advance(pick)
    try:
        _auto_continue()
    except Exception as _ex:
        _p(f"[!] auto-continue err: {str(_ex)[:80]}")
if __name__=="__main__":
    try:
        main()
    except KeyboardInterrupt:
        _p("\n[stop]")
    except Exception as _e2:
        try:
            _sb_health("error",str(_e2)[:200])
        except Exception:
            pass
        raise