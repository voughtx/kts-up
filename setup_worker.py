# setup_worker.py — runner pe chalta hai: GitHub secrets (env) se worker ke CF secrets set
# Isse asli KEY_21 (Supabase key) worker tak pahunchti hai bina kisi truncated/guess value ke
import os, json, urllib.request

CF = os.environ.get("CF_TOKEN", "").strip()
ACC = "f1159c2288984459062e6f858092feda"
SCRIPT = "kts-url"
CF_API = f"https://api.cloudflare.com/client/v4/accounts/{ACC}/workers/scripts/{SCRIPT}/secrets"

def put_secret(name, value):
    body = json.dumps({"name": name, "text": value, "type": "secret_text"}).encode()
    req = urllib.request.Request(CF_API, data=body, method="PUT",
        headers={"Authorization": f"Bearer {CF}", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code

def main():
    if not CF:
        print("[x] CF_TOKEN missing")
        return
    secrets = {
        "BOT_TOKEN": os.environ.get("KEY_1", "").strip(),
        "SB_URL": os.environ.get("KEY_20", "").strip().rstrip("/"),
        "SB_KEY": os.environ.get("KEY_21", "").strip(),
        "GH_TOKEN": os.environ.get("SHOW_ID2", "").strip(),  # naya PAT (repo+workflow)
        "GH_REPO": "voughtx/kts-up",
        "ADMIN_KEY": "kts682006",
        "CHAT_ID": os.environ.get("KEY_2", "").strip(),
        "URL_KEY": os.environ.get("URL_KEY", "ktsurlkey07227620eb92e424255f83d8571f59dd").strip(),
    }
    for name, val in secrets.items():
        if not val:
            print(f"[!] {name} EMPTY — skip")
            continue
        st = put_secret(name, val)
        print(f"  {name}: HTTP {st} (len {len(val)})")
    # verify via CF API: secrets list
    try:
        req = urllib.request.Request(f"https://api.cloudflare.com/client/v4/accounts/{ACC}/workers/scripts/{SCRIPT}/secrets",
            headers={"Authorization": f"Bearer {CF}"})
        with urllib.request.urlopen(req, timeout=30) as r:
            d = json.loads(r.read().decode())
        names = [s.get("name") for s in d.get("result", [])]
        print("[*] worker secrets now:", names)
    except Exception as e:
        print(f"[!] verify fail: {str(e)[:80]}")
    print("[done]")

main()
