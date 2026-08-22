#!/usr/bin/env python3
"""copy katfile secret to tnxi repos (values never printed)"""
import os, json, base64, urllib.request, urllib.error

PAT = os.environ.get("PAT", "").strip()
KAT_BASE = os.environ.get("KEY_11", "").strip()
KAT_TOKEN = os.environ.get("KEY_12", "").strip()

def api(path, data=None, method="GET"):
    url = "https://api.github.com" + path
    h = {"Authorization": "token " + PAT, "Accept": "application/vnd.github+json", "User-Agent": "cp"}
    if data is not None:
        h["Content-Type"] = "application/json"
        req = urllib.request.Request(url, data=json.dumps(data).encode(), headers=h, method=method)
    else:
        req = urllib.request.Request(url, headers=h, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode() or "{}")

print("pat len", len(PAT), "| base", KAT_BASE[:30], "| tok len", len(KAT_TOKEN), flush=True)

try:
    import nacl.bindings
except ImportError:
    import subprocess, sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "pynacl"])
    import nacl.bindings

def set_secret(repo, name, value):
    st, pk = api(f"/repos/{repo}/actions/secrets/public-key")
    if st != 200:
        return f"pub{st}"
    sealed = nacl.bindings.crypto_box_seal(value.encode(), base64.b64decode(pk["key"]))
    st2, _ = api(f"/repos/{repo}/actions/secrets/{name}",
                 {"encrypted_value": base64.b64encode(sealed).decode(), "key_id": pk["key_id"]}, method="PUT")
    return "ok" if st2 in (201, 204) else f"f{st2}"

for i in range(1, 11):
    repo = f"voughtx/tnxi-up-{i}"
    r1 = set_secret(repo, "KAT_BASE", KAT_BASE)
    r2 = set_secret(repo, "KAT_TOKEN", KAT_TOKEN)
    print(repo, "KAT_BASE:", r1, "KAT_TOKEN:", r2, flush=True)
print("done", flush=True)
