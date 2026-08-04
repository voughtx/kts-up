# KTS save_logs.py — workflow ke end mein run ka log Supabase (progress table, id=log_<run>) mein save karta hai
# Jobs logs endpoint (plain text, live) use karta hai — run ke andar se bhi kaam karta hai.
import os, json, subprocess, time, urllib.request as u

SB_URL = os.environ.get("KEY_20", "").strip().rstrip("/")
SB_KEY = os.environ.get("KEY_21", "").strip()
RUN_ID = os.environ.get("RUN_ID", "")
JOB_ID = os.environ.get("JOB_ID", "")
STATUS = os.environ.get("JOB_STATUS", "")
REPO = os.environ.get("GITHUB_REPOSITORY", "")
GH_TOKEN = os.environ.get("GITHUB_TOKEN", "")

log_txt = ""
if JOB_ID and REPO and GH_TOKEN:
    try:
        out = subprocess.run(
            ["curl", "-sL", "-H", f"Authorization: Bearer {GH_TOKEN}",
             "-H", "Accept: application/vnd.github+json",
             f"https://api.github.com/repos/{REPO}/actions/jobs/{JOB_ID}/logs"],
            capture_output=True, text=True, timeout=90,
        )
        log_txt = (out.stdout or "") + (out.stderr or "")
    except Exception as e:
        log_txt = f"[log fetch fail] {e}"
if not log_txt.strip():
    # fallback: gh run view (completed runs ke liye)
    try:
        out = subprocess.run(["gh", "run", "view", RUN_ID, "--repo", REPO, "--log"],
                             capture_output=True, text=True, timeout=60)
        log_txt = (out.stdout or "") + (out.stderr or "")
    except Exception:
        pass

# sirf useful lines rakho (pip install ka noise hatao)
KEEP = ("[ok]", "[!]", "[x]", "[dbg]", "[*]", "next:", "converting", "ready",
        "msg_id", "upload", "DONE", "progress", "Traceback", "Error",
        "token", "relay", "supabase", "gh release", "kartoons")
lines = [ln for ln in log_txt.splitlines() if any(k in ln for k in KEEP)]
if STATUS != "success":
    lines += log_txt.splitlines()[-60:]  # failure: last 60 lines bhi
log_txt = "\n".join(lines)[-8000:]  # cap 8KB

state = {
    "run_id": RUN_ID,
    "result": "success" if STATUS == "success" else "failed",
    "at": int(time.time()),
    "log": log_txt,
}

ok = False
if SB_URL and SB_KEY and RUN_ID:
    try:
        row = {"id": f"log_{RUN_ID}", "state": state}
        req = u.Request(f"{SB_URL}/rest/v1/progress", data=json.dumps(row).encode(), method="POST",
                        headers={"apikey": SB_KEY, "Authorization": f"Bearer {SB_KEY}",
                                 "Content-Type": "application/json",
                                 "Prefer": "resolution=merge-duplicates"})
        with u.urlopen(req, timeout=30) as r:
            print(f"[ok] log saved ({r.status}) id=log_{RUN_ID} result={state['result']}")
            ok = True
    except Exception as e:
        print(f"[!] log save fail: {str(e)[:100]}")
else:
    print("[!] skip: SB/RUN_ID missing")
print("[done]")
