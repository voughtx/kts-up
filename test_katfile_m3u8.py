#!/usr/bin/env python3
"""
TEST (read-only): kya katfile ek DECRYPTED playlist accept karta hai?

Kyun: run #1270 me branch-2 ne katfile ko wahi playlist di jisme segments `enc2:`
(AES-GCM) the. Katfile andar ffmpeg chalata hai -> `enc2:` samajh nahi aaya -> "ffmpeg failed".

Ye script sirf ye pukka karta hai:
  A) decrypted (plain https) playlist ko GIST pe host karke katfile ko doge to kaam karega?
  B) confirm ki raw enc2: playlist fail hoti hai (control test)

KUCH UPLOAD NAHI HOTA. Koi channel/DB touch nahi. Sirf katfile job + delete.
"""
import os, sys, re, json, time, base64, hashlib, urllib.request as Q, urllib.parse as U

def p(*a): print(*a, flush=True)

_A   = os.environ.get("KEY_8","")            # kartoons api base
_G   = os.environ.get("KEY_10","")           # GCM key material
_TB  = os.environ.get("KEY_11","").rstrip("/")  # katfile base
_TT  = os.environ.get("KEY_12","")           # katfile api token
_REF = os.environ.get("KEY_14","")
_GH  = os.environ.get("GH_TOKEN","")
_TOK = os.environ.get("CHALLENGE_TOKEN","")
_EID = os.environ.get("EP_ID","6825c4c70509281774f8fea8")
_UA  = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"

try:
    from Crypto.Cipher import AES
except Exception:
    from Cryptodome.Cipher import AES


def b64u(s):
    b = s.replace("-","+").replace("_","/")
    b += "="*((4-len(b)%4)%4)
    return base64.b64decode(b)

def dec_gcm(enc):
    s = enc[5:] if enc.startswith("enc2:") else enc
    raw = b64u(s); iv, body = raw[:12], raw[12:]
    key = hashlib.sha256(_G.encode()).digest()
    ct, tag = body[:-16], body[-16:]
    for nonce in (iv, bytes(12)):
        try:
            return AES.new(key, AES.MODE_GCM, nonce=nonce).decrypt_and_verify(ct, tag).decode("utf-8","replace")
        except Exception:
            pass
    return enc

def pow_solve(nonce, bits):
    zeros = "0"*(bits//4); extra = bits % 4; s = 0
    while True:
        hh = hashlib.sha256(f"{nonce}:{s}".encode()).hexdigest()
        if hh.startswith(zeros):
            if not extra or int(hh[len(zeros)],16) < (1 << (4-extra)):
                return str(s)
        s += 1

def http(url, data=None, hdr=None, method=None, timeout=60):
    r = Q.Request(url, data=data, headers=hdr or {}, method=method)
    with Q.urlopen(r, timeout=timeout) as x:
        return x.getcode(), x.read()


# ---------- 1) episode links (X-Challenge-Token + PoW) ----------
def get_playlist():
    # base headers app jaise (Origin + Referer zaroori)
    base = {"User-Agent":_UA, "Accept":"application/json",
            "Origin":_REF.rstrip("/"), "Referer":_REF}

    code, body = http(f"{_A}/challenge/pow?content=episode:{_EID}", hdr=dict(base))
    d = (json.loads(body).get("data") or {})
    nonce, bits = d.get("nonce"), int(d.get("bits") or 16)
    sol = pow_solve(nonce, bits)
    p(f"[ok] PoW solved (bits={bits})")

    # FIX: path /shows/episode/<eid>/links hai (mera /episodes/... galat tha -> 403)
    # FIX: Authorization Bearer + X-Challenge-Retry bhi chahiye, sirf X-Challenge-Token se 403
    h = dict(base)
    h.update({"X-Challenge-Token":_TOK, "Authorization":f"Bearer {_TOK}",
              "X-Challenge-Retry":"true", "X-Pow-Nonce":nonce, "X-Pow-Solution":sol})
    code, body = http(f"{_A}/shows/episode/{_EID}/links", hdr=h)
    p(f"[ok] /shows/episode/{_EID}/links HTTP {code}")
    links = (json.loads(body).get("data") or {}).get("links") or []
    if not links:
        p("[x] koi link nahi"); sys.exit(1)

    raw = links[0].get("url") or ""
    purl = dec_gcm(raw) if raw.startswith("enc2:") else raw
    p(f"[ok] playlist url: {purl[:60]}...")

    code, body = http(purl, hdr={"User-Agent":_UA, "Referer":_REF})
    return purl, body.decode("utf-8","replace")


# ---------- 2) enc2: -> plain https ----------
def decrypt_playlist(text):
    out = []
    for ln in text.splitlines():
        s = ln.strip()
        if s.startswith("enc2:"):
            out.append(dec_gcm(s))
        elif s.startswith("#EXT-X-MAP:"):
            m = re.search(r'URI="([^"]+)"', s)
            out.append(s.replace(m.group(1), dec_gcm(m.group(1))) if m and m.group(1).startswith("enc2:") else ln)
        else:
            out.append(ln)
    return "\n".join(out)


# ---------- 3) host on PUBLIC repo raw (gist scope nahi hai PAT me) ----------
# Fixed path pe overwrite karte hain -> KUCH DELETE NAHI hota (RULE 2 safe).
# raw URL me commit SHA lagate hain -> CDN cache ka jhanjhat nahi.
_HOST_REPO = os.environ.get("HOST_REPO", "voughtx/kts-up")
_HOST_PATH = "tmp/test_playlist.m3u8"

def host_raw(content):
    api = f"https://api.github.com/repos/{_HOST_REPO}/contents/{_HOST_PATH}"
    hdr = {"Authorization": f"Bearer {_GH}", "User-Agent":"kts",
           "Accept":"application/vnd.github+json", "Content-Type":"application/json"}
    sha = None
    try:
        code, resp = http(api, hdr=hdr)
        sha = (json.loads(resp) or {}).get("sha")
    except Exception:
        pass
    body = {"message": "katfile test playlist (temp, overwritten)",
            "content": base64.b64encode(content.encode()).decode()}
    if sha:
        body["sha"] = sha
    code, resp = http(api, data=json.dumps(body).encode(), hdr=hdr, method="PUT")
    commit = (json.loads(resp) or {}).get("commit", {}).get("sha", "main")
    return f"https://raw.githubusercontent.com/{_HOST_REPO}/{commit}/{_HOST_PATH}"


# ---------- 4) katfile convert ----------
def katfile(page_url, url, filename, label):
    p(f"\n--- KATFILE TEST: {label} ---")
    p(f"    url: {url[:70]}...")
    body = json.dumps({"pageUrl":page_url, "url":url, "type":"hls", "referer":_REF,
                       "origin":_REF, "cookie":"", "userAgent":_UA, "filename":filename}).encode()
    try:
        code, resp = http(f"{_TB}/api/convert", data=body,
                          hdr={"X-API-Token":_TT, "Content-Type":"application/json", "User-Agent":_UA},
                          method="POST")
    except Exception as e:
        p(f"    [x] convert call fail: {e}"); return False
    job = (json.loads(resp) or {}).get("id")
    if not job:
        p(f"    [x] job id nahi mila: {resp[:200]}"); return False
    p(f"    job: {job}")

    ok = False
    for i in range(120):
        time.sleep(5)
        try:
            code, resp = http(f"{_TB}/api/jobs/{job}", hdr={"X-API-Token":_TT, "User-Agent":_UA})
            st = json.loads(resp) or {}
        except Exception as e:
            p(f"    poll err: {e}"); continue
        s = st.get("status") or st.get("state") or "?"
        if i % 4 == 0 or s in ("done","completed","success","failed","error"):
            p(f"    [{i*5:>3}s] status={s} progress={st.get('progress')}")
        if s in ("done","completed","success"):
            p(f"    ✅ SUCCESS  file={st.get('filename')} size={st.get('size')}")
            ok = True; break
        if s in ("failed","error"):
            p(f"    ❌ FAILED: {str(st.get('error'))[:300]}")
            break
    try:
        http(f"{_TB}/api/jobs/{job}", hdr={"X-API-Token":_TT, "User-Agent":_UA}, method="DELETE")
        p("    (job deleted)")
    except Exception:
        pass
    return ok


if __name__ == "__main__":
    miss = [n for n,v in [("KEY_10",_G),("KEY_11",_TB),("KEY_12",_TT),("CHALLENGE_TOKEN",_TOK)] if not v]
    if miss:
        p(f"[x] missing env: {miss}"); sys.exit(1)

    purl, raw_text = get_playlist()
    n_enc = sum(1 for l in raw_text.splitlines() if l.strip().startswith("enc2:"))
    n_inf = raw_text.count("#EXT-X-STREAM-INF")
    p(f"[*] playlist: {len(raw_text)} B | STREAM-INF={n_inf} | enc2 lines={n_enc}")
    if n_inf:
        p("[!] ye branch-1 (variants) hai — branch-2 test ke liye doosra episode chahiye")

    dec_text = decrypt_playlist(raw_text)
    n_http = sum(1 for l in dec_text.splitlines() if l.startswith("http"))
    p(f"[*] decrypted: enc2 bache={('enc2:' in dec_text)} | plain http lines={n_http}")

    raw_url = host_raw(dec_text)
    p(f"[ok] hosted: {raw_url[:90]}")
    try:
        code, chk = http(raw_url, hdr={"User-Agent":_UA})
        p(f"[ok] raw reachable: HTTP {code}, {len(chk)} B")
    except Exception as e:
        p(f"[x] raw fetch fail: {e}")

    # TEST A: decrypted playlist (asli sawaal)
    a = katfile(purl, raw_url, "TEST_decrypted", "A) DECRYPTED playlist via raw URL")
    # TEST B: control — raw enc2 playlist (fail hona chahiye)
    b = katfile(purl, purl, "TEST_raw", "B) RAW enc2 playlist (control)")

    p("\n===== NATEEJA =====")
    p(f"  A) decrypted playlist : {'✅ CHALA' if a else '❌ FAIL'}")
    p(f"  B) raw enc2 playlist  : {'✅ chala' if b else '❌ fail (expected)'}")
    if a and not b:
        p("  ➡️ CONFIRMED: katfile ko decrypted playlist do — fix ka raasta saaf hai")
    elif a and b:
        p("  ➡️ dono chale — enc2 wajah nahi thi, aur dekhna padega")
    else:
        p("  ➡️ decrypted bhi fail — katfile ko segments tak pahunch nahi (IP/referer issue?)")
