# copy_secrets.py — main repo ke saare KEY_* secrets naye repos mein copy karo
# (GitHub API encrypted PUT — runner pe env vars se)
import os, json, urllib.request, base64, sys

TOKEN = os.environ.get("GH_TOKEN", "").strip() or os.environ.get("GITHUB_TOKEN", "").strip()
# SHOW_ID mein PAT daala hai (GITHUB_TOKEN secrets API nahi de sakta) — isse copy karo
if not TOKEN or not TOKEN.startswith("ghp_"):
    TOKEN = os.environ.get("SHOW_ID", "").strip()
TARGETS = ["voughtx/kts-up-2", "voughtx/kts-up-3"]
SECRET_NAMES = [f"KEY_{i}" for i in range(1, 38)] + ["SHOW_ID", "SHOW_ID2", "CONCURRENCY", "PRIORITY"]

def gh(method, path, body=None):
    req = urllib.request.Request(f"https://api.github.com{path}", method=method,
        headers={"Authorization": f"Bearer {TOKEN}", "Accept": "application/vnd.github+json",
                 "Content-Type": "application/json"})
    data = json.dumps(body).encode() if body is not None else None
    try:
        with urllib.request.urlopen(req, data=data, timeout=30) as r:
            return r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()

def main():
    try:
        from nacl import encoding, public
    except Exception:
        os.system(f"{sys.executable} -m pip install -q pynacl")
        from nacl import encoding, public
    print(f"[*] token: ...{TOKEN[-6:]}")
    # source repo public key (encrypt ke liye kisi bhi repo ki chalega — same org)
    st, b = gh("GET", "/repos/voughtx/kts-up/actions/secrets/public-key")
    if st != 200:
        print(f"[x] pubkey fetch: HTTP {st} {b[:200]}")
        return
    pk = json.loads(b)
    key = public.PublicKey(pk["key"], encoding.Base64Encoder())
    print(f"[*] pubkey: {pk['key_id']}")
    # ratelimit info
    try:
        st3, b3 = gh("GET", "/rate_limit")
        rl = json.loads(b3).get("resources", {}).get("core", {})
        print(f"[*] rate: {rl.get('remaining')}/{rl.get('limit')} reset={rl.get('reset')}")
    except Exception:
        pass
    copied, skipped = 0, 0
    for target in TARGETS:
        print(f"\n=== {target} ===")
        for name in SECRET_NAMES:
            val = os.environ.get(name, "").strip()
            if not val:
                skipped += 1
                continue
            sealed = public.SealedBox(key).encrypt(val.encode())
            enc = base64.b64encode(sealed).decode()
            st2, b2 = gh("PUT", f"/repos/{target}/actions/secrets/{name}",
                         {"encrypted_value": enc, "key_id": pk["key_id"]})
            if st2 == 204:
                copied += 1
                print(f"  [ok] {name} (len {len(val)})")
            else:
                print(f"  [x] {name}: HTTP {st2} {b2[:100]}")
    print(f"\n[done] copied={copied} skipped_empty={skipped}")

main()
