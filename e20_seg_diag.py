#!/usr/bin/env python3
"""E20 segment-flow diagnostic — runner pe chalta hai (KEY_10 available).
Links -> master -> GCM variant decrypt -> media playlist -> segment fetch (direct+relay).
Output: exact point jahan fail hota hai. Diagnostic only, koi content print nahi."""
import os, sys, json, re, base64, hashlib, subprocess, urllib.request, urllib.parse
subprocess.run("pip install -q pycryptodome", shell=True, check=False)
from Crypto.Cipher import AES

API = "https://api.kartoons.me/api"
REF = "https://kartoons.me/"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0.0.0 Safari/537.36"
SB_URL = os.environ.get("KEY_20", "").strip().rstrip("/")
SB_KEY = os.environ.get("KEY_21", "").strip()
GCM = os.environ.get("KEY_10", "").strip()
KEY9 = "bca9e0df1a5abb32906ca3f63ac04cef"
RELAY_KEY = "ktsrelay2026"
TOKEN = os.environ.get("TOKEN", "").strip()
SHOW = "68615fe7d437587dc8876773"

print("[*] KEY_10 len:", len(GCM), flush=True)
print("[*] token len:", len(TOKEN), flush=True)

RELAYS = []
try:
    req = urllib.request.Request(f"{SB_URL}/rest/v1/progress?select=state&id=eq.relay&limit=1",
        headers={"apikey": SB_KEY, "Authorization": f"Bearer {SB_KEY}"})
    with urllib.request.urlopen(req, timeout=20) as r:
        arr = json.loads(r.read().decode())
    RELAYS = ((arr[0].get("state") or {}).get("urls")) or [] if arr else []
    print("[*] relays:", [x.get("url","")[:25] for x in RELAYS], flush=True)
except Exception as e:
    print("[!] relay fetch fail:", str(e)[:60], flush=True)

def b64u(s):
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))

def dec_cbc(url):
    try:
        raw = b64u(url); iv, ct = raw[:16], raw[16:]
        c = AES.new(KEY9.encode()[:32], AES.MODE_CBC, iv)
        pt = c.decrypt(ct); pad = pt[-1]
        if 1 <= pad <= 16 and pt[-pad:] == bytes([pad]) * pad:
            pt = pt[:-pad]
        return pt.decode("utf-8", "replace")
    except Exception:
        return url

def dec_gcm(s):
    s2 = s[5:] if s.startswith("enc2:") else s
    try:
        raw = b64u(s2); iv, body = raw[:12], raw[12:]
        key = hashlib.sha256(GCM.encode()).digest()
        ct, tag = body[:-16], body[-16:]
        c = AES.new(key, AES.MODE_GCM, nonce=iv)
        return c.decrypt_and_verify(ct, tag).decode("utf-8", "replace")
    except Exception as e:
        return "GCMFAIL:" + str(e)[:50]

def req(path, data=None, method="GET", headers=None):
    h = {"User-Agent": UA, "Accept": "application/json", "Origin": REF.rstrip("/"), "Referer": REF}
    if headers: h.update(headers)
    body = None
    if data is not None:
        body = json.dumps(data).encode(); h["Content-Type"] = "application/json"
    # relay-first (runner IP block se bachne ke liye)
    if RELAYS:
        for r2 in RELAYS:
            try:
                ru = r2["url"].rstrip("/") + "?" + urllib.parse.urlencode([("path", path)] + [("h_" + k, v) for k, v in h.items()])
                rh = {"X-KTS-Key": RELAY_KEY, "User-Agent": UA}
                rq = urllib.request.Request(ru, data=body, headers=rh, method=method)
                with urllib.request.urlopen(rq, timeout=25) as resp:
                    return resp.status, resp.read().decode("utf-8", "replace")
            except Exception as e:
                print("[!] relay try fail:", str(e)[:50], flush=True)
    r = urllib.request.Request(API + path, data=body, headers=h, method=method)
    try:
        with urllib.request.urlopen(r, timeout=25) as resp:
            return resp.status, resp.read().decode("utf-8", "replace")
    except Exception as e:
        return 0, str(e)

def req_bin(url):
    h = {"User-Agent": UA, "Accept": "*/*", "Origin": REF.rstrip("/"), "Referer": REF}
    # direct first
    try:
        r = urllib.request.Request(url, headers=h)
        with urllib.request.urlopen(r, timeout=30) as resp:
            b = resp.read()
        print("[*] direct seg:", len(b), "bytes, head:", b[:15], flush=True)
        if b and len(b) > 10000 and b[:1] != b"<":
            return b
    except Exception as e:
        print("[!] direct seg EXC:", str(e)[:50], flush=True)
    # relay
    for r2 in RELAYS:
        try:
            ru = r2["url"].rstrip("/") + "?" + urllib.parse.urlencode([("path", url)] + [("h_" + k, v) for k, v in h.items()])
            rq = urllib.request.Request(ru, headers={"X-KTS-Key": RELAY_KEY, "User-Agent": UA})
            with urllib.request.urlopen(rq, timeout=40) as resp:
                b = resp.read()
            print("[*] relay seg:", len(b), "bytes, head:", b[:15], flush=True)
            return b
        except Exception as e:
            print("[!] relay seg EXC:", str(e)[:50], flush=True)
    return b""

def main():
    if not TOKEN:
        print("[!] no TOKEN env", flush=True); return
    # S1E20 id
    st, body = req(f"/shows/{SHOW}")
    if st != 200:
        print("[!] shows fail", st, flush=True); return
    seasons = json.loads(body)["data"].get("seasons") or []
    s1 = min(seasons, key=lambda s: s.get("seasonNumber") or 0)
    st, body = req(f"/shows/{SHOW}/season/{s1['_id']}/all-episodes")
    eps = sorted(json.loads(body).get("data") or [], key=lambda e: e.get("episodeNumber") or 0)
    eid = eps[19]["_id"] if len(eps) > 19 else None
    print("[*] e20 id found:", bool(eid), flush=True)
    if not eid:
        return
    # pow
    st, body = req(f"/challenge/pow?content=episode:{eid}")
    pd = json.loads(body).get("data") or {}
    nonce, bits = pd.get("nonce"), pd.get("bits")
    sol = 0; target = "0" * (int(bits) // 4)
    while not hashlib.sha256(f"{nonce}:{sol}".encode()).hexdigest().startswith(target):
        sol += 1
    # links
    st, body = req(f"/shows/episode/{eid}/links",
        headers={"Authorization": "Bearer " + TOKEN, "X-Pow-Nonce": nonce,
                 "X-Pow-Solution": str(sol), "X-Challenge-Token": TOKEN})
    print("[*] links status:", st, flush=True)
    if st != 200:
        print("[!] links body:", body[:150], flush=True); return
    links = json.loads(body).get("data", {}).get("links") or []
    print("[*] links count:", len(links), flush=True)
    for l in links:
        u = l.get("url", "")
        if u.startswith("enc2:"):
            print("[*] link is enc2 (GCM) len:", len(u), flush=True)
            u = dec_gcm(u)
            print("[*] GCM decrypt:", u[:50], "| http:", u.startswith("http"), flush=True)
        elif not u.startswith("http"):
            u2 = dec_cbc(u)
            print("[*] CBC decrypt:", u2[:50], "| http:", u2.startswith("http"), flush=True)
            u = u2
        if u.startswith("http") and ("playlist" in u or ".m3u8" in u):
            print("[*] master URL:", u[:55], flush=True)
            # fetch master
            h = {"User-Agent": UA, "Accept": "*/*", "Origin": REF.rstrip("/"), "Referer": REF}
            got = None
            for r2 in RELAYS:
                try:
                    ru = r2["url"].rstrip("/") + "?" + urllib.parse.urlencode([("path", u)] + [("h_" + k, v) for k, v in h.items()])
                    rq = urllib.request.Request(ru, headers={"X-KTS-Key": RELAY_KEY, "User-Agent": UA})
                    with urllib.request.urlopen(rq, timeout=25) as resp:
                        got = resp.read().decode(errors="replace")
                    print("[*] master via relay len:", len(got), "| extm3u:", got.startswith("#EXTM3U"), flush=True)
                    break
                except Exception as e:
                    print("[!] master relay fail:", str(e)[:40], flush=True)
            if not got:
                try:
                    rq = urllib.request.Request(u, headers=h)
                    with urllib.request.urlopen(rq, timeout=25) as resp:
                        got = resp.read().decode(errors="replace")
                    print("[*] master direct len:", len(got), "| extm3u:", got.startswith("#EXTM3U"), flush=True)
                except Exception as e:
                    print("[!] master direct fail:", str(e)[:40], flush=True)
            if got:
                lines = got.splitlines()
                print("[*] master lines:", len(lines), "| STREAM-INF:", sum(1 for ln in lines if "STREAM-INF" in ln),
                      "| enc2:", sum(1 for ln in lines if "enc2:" in ln), flush=True)
                # variant decrypt
                for ln in lines:
                    if ln.strip().startswith("enc2:"):
                        mv = dec_gcm(ln.strip())
                        print("[*] variant GCM:", mv[:55], "| http:", mv.startswith("http"), flush=True)
                        if mv.startswith("http"):
                            # media playlist fetch
                            hm = {"User-Agent": UA, "Accept": "*/*", "Origin": REF.rstrip("/"), "Referer": REF}
                            for r2 in RELAYS:
                                try:
                                    ru = r2["url"].rstrip("/") + "?" + urllib.parse.urlencode([("path", mv)] + [("h_" + k, v) for k, v in hm.items()])
                                    rq = urllib.request.Request(ru, headers={"X-KTS-Key": RELAY_KEY, "User-Agent": UA})
                                    with urllib.request.urlopen(rq, timeout=25) as resp:
                                        ml = resp.read().decode(errors="replace")
                                    print("[*] media playlist len:", len(ml), "| extm3u:", ml.startswith("#EXTM3U"), flush=True)
                                    segs = [x.strip() for x in ml.splitlines() if x.strip().startswith("http")]
                                    if not segs:
                                        # relative segs
                                        segs = [x.strip() for x in ml.splitlines() if x.strip() and not x.startswith("#")]
                                    print("[*] media segs:", len(segs), flush=True)
                                    if segs:
                                        su = segs[0] if segs[0].startswith("http") else urllib.parse.urljoin(mv, segs[0])
                                        print("[*] trying segment fetch:", su[:70], flush=True)
                                        # DIRECT
                                        try:
                                            hd={"User-Agent":UA,"Accept":"*/*","Origin":REF.rstrip("/"),"Referer":REF}
                                            rq=urllib.request.Request(su, headers=hd)
                                            with urllib.request.urlopen(rq, timeout=30) as resp:
                                                b=resp.read()
                                            print("[*] direct seg:", len(b), "bytes, head:", b[:15], flush=True)
                                        except Exception as e:
                                            print("[!] direct seg EXC:", str(e)[:50], flush=True)
                                            b=b""
                                        # RELAY
                                        for r2 in RELAYS:
                                            try:
                                                hd={"User-Agent":UA,"Accept":"*/*","Origin":REF.rstrip("/"),"Referer":REF}
                                                ru=r2["url"].rstrip("/")+"?"+urllib.parse.urlencode([("path",su)]+[("h_"+k,v) for k,v in hd.items()])
                                                rq=urllib.request.Request(ru, headers={"X-KTS-Key":RELAY_KEY,"User-Agent":UA})
                                                with urllib.request.urlopen(rq, timeout=40) as resp:
                                                    rb=resp.read()
                                                print("[*] relay seg:", len(rb), "bytes, head:", rb[:15], flush=True)
                                                if len(rb) > len(b):
                                                    b = rb
                                                break
                                            except Exception as e:
                                                print("[!] relay seg EXC:", str(e)[:40], flush=True)
                                        print("[*] segment result:", len(b), "bytes", flush=True)
                                    break
                                except Exception as e:
                                    print("[!] media relay fail:", str(e)[:40], flush=True)
                        break
    print("[diag done]", flush=True)

if __name__ == "__main__":
    main()
