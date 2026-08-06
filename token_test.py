# token_test.py — dono tokens ko Kartoons API pe live test karo
# 1) captcha token (env KEY_3)  2) login JWT (Supabase saved) 3) master ke paas koi aur?
import os, json, urllib.request, urllib.parse, hashlib, base64, time

API = "https://api.kartoons.me/api"
EP = "686e711252b2d65b4faaf816"  # S10E4 — fresh episode, kisi bhi DB mein nahi

CAPTCHA = os.environ.get("KEY_3", "").strip()
JWT = os.environ.get("KEY_4", "").strip()
SBURL = os.environ.get("KEY_20", "").strip().rstrip("/")
SBKEY = os.environ.get("KEY_21", "").strip()

def api(path, hdrs=None):
    h = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120",
         "Accept": "application/json", "Origin": "https://kartoons.me",
         "Referer": "https://kartoons.me/", "X-Challenge-Token": ""}
    if hdrs: h.update(hdrs)
    try:
        with urllib.request.urlopen(urllib.request.Request(API + path, headers=h), timeout=30) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")

def solve_pow(nonce, bits):
    zeros = "0" * (bits // 4)
    s = 0
    while True:
        if hashlib.sha256(f"{nonce}:{s}".encode()).hexdigest().startswith(zeros):
            return str(s)
        s += 1

def test_token(name, tok):
    if not tok:
        print(f"[{name}] token missing (len=0)")
        return
    print(f"\n=== TEST: {name} (tail ...{tok[-6:]}) ===")
    # PoW solve
    try:
        st, b = api("/challenge/pow?content=" + urllib.parse.quote(f"episode:{EP}"), {"X-Challenge-Token": tok})
        print(f"  pow: {st}", end="")
        d = json.loads(b).get("data") or {}
        if st == 200 and d.get("nonce"):
            sol = solve_pow(d["nonce"], d.get("bits", 16))
            print(f" solved={sol[:10]}...")
            hdrs = {"X-Challenge-Token": tok, "Authorization": f"Bearer {tok}",
                    "X-Challenge-Retry": "true", "X-Pow-Nonce": d["nonce"], "X-Pow-Solution": sol}
        else:
            print(" (no pow needed)")
            hdrs = {"X-Challenge-Token": tok, "Authorization": f"Bearer {tok}", "X-Challenge-Retry": "true"}
    except Exception as e:
        print(f"  pow fail: {str(e)[:80]}")
        return
    # links
    try:
        st2, b2 = api(f"/shows/episode/{EP}/links", hdrs)
        ok = "✅ WORKS" if st2 == 200 else f"❌ FAIL {st2}"
        print(f"  links: {st2} {ok} | {b2[:120]}")
    except Exception as e:
        print(f"  links fail: {str(e)[:80]}")

# Supabase saved token bhi lo
saved = ""
try:
    req = urllib.request.Request(f"{SBURL}/rest/v1/progress?select=state&id=eq.token&limit=1",
                                 headers={"apikey": SBKEY, "Authorization": f"Bearer {SBKEY}"})
    with urllib.request.urlopen(req, timeout=20) as r:
        arr = json.loads(r.read().decode())
    saved = (arr[0].get("state") or {}).get("token", "") if arr else ""
    print(f"[sb] saved token tail: ...{saved[-6:] if saved else 'NONE'}")
except Exception as e:
    print(f"[sb] fetch fail: {str(e)[:60]}")

test_token("captcha (KEY_3)", CAPTCHA)
test_token("login JWT (KEY_4)", JWT)
if saved and saved != JWT and saved != CAPTCHA:
    test_token("supabase saved", saved)
print("\n[done]")
