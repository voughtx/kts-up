# fileid_test.py — MTProto doc -> Bot API file_id -> getFile verify
import os, sys, time, json, struct, base64, asyncio, urllib.request

try:
    import cryptg  # noqa
except Exception:
    os.system(f"{sys.executable} -m pip install -q cryptg")

from telethon import TelegramClient
from telethon.sessions import StringSession

CHAT = os.environ.get("KEY_2", "").strip()
AID = int(os.environ.get("KEY_16", "0").strip())
AHASH = os.environ.get("KEY_17", "").strip()
K1 = os.environ.get("KEY_1", "").strip()
BOT_TOKENS = {f"bot{i+1}": os.environ.get(f"KEY_{i}", "").strip() for i in range(22, 28)}
SBURL = os.environ.get("KEY_20", "").strip()
SBKEY = os.environ.get("KEY_21", "").strip()

def rle_encode(s: bytes) -> bytes:
    """pyrogram-exact zero-value RLE encoder"""
    r = []
    n = 0
    for b in s:
        if not b:
            n += 1
        else:
            if n:
                r.extend((0, n))
                n = 0
            r.append(b)
    if n:
        r.extend((0, n))
    return bytes(r)

def b64_encode(data):
    return base64.urlsafe_b64encode(data).decode().rstrip("=")

def make_doc_file_id(dc_id, media_id, access_hash, file_reference):
    FILE_REFERENCE_FLAG = 1 << 25
    file_type = 5 | FILE_REFERENCE_FLAG  # DOCUMENT
    buf = struct.pack("<ii", file_type, dc_id)
    fr = file_reference or b""
    if len(fr) <= 253:
        buf += bytes([len(fr)]) + fr + b"\x00" * (-(len(fr) + 1) % 4)
    else:
        buf += bytes([254]) + len(fr).to_bytes(3, "little") + fr + b"\x00" * (-len(fr) % 4)
    buf += struct.pack("<qq", media_id, access_hash)
    buf += struct.pack("<ii", 30, 4)
    buf += struct.pack("<bb", 30, 4)
    return b64_encode(rle_encode(buf))

def sb_sessions():
    req = urllib.request.Request(f"{SBURL}/rest/v1/progress?select=state&id=eq.bot_sessions&limit=1",
                                 headers={"apikey": SBKEY, "Authorization": f"Bearer {SBKEY}"})
    with urllib.request.urlopen(req, timeout=30) as r:
        d = json.loads(r.read().decode())
    return (d[0].get("state") or {}) if d else {}

def getFile(token, file_id):
    try:
        req = urllib.request.Request(f"https://api.telegram.org/bot{token}/getFile?file_id={urllib.parse.quote(file_id)}")
        with urllib.request.urlopen(req, timeout=30) as r:
            j = json.loads(r.read().decode())
        return j.get("ok"), j.get("result", {}).get("file_size"), j.get("description", "")
    except urllib.error.HTTPError as e:
        return False, None, f"HTTP {e.code}"
    except Exception as e:
        return False, None, str(e)[:60]

async def main():
    import urllib.parse
    st = sb_sessions()
    print(f"[*] sessions: {sum(len(v) for v in st.values() if isinstance(v, list))}", flush=True)
    # USER session se messages padho (bots history nahi dekh sakte)
    SS = os.environ.get("KEY_18", "").strip()
    print(f"[*] K1 tail: {K1[-6:]} | user sess len: {len(SS)}", flush=True)
    if not SS:
        print("[x] KEY_18 missing")
        return
    c = TelegramClient(StringSession(SS), AID, AHASH)
    await c.connect()
    ch = await c.get_entity(int(CHAT))
    # last messages
    msgs = await c.get_messages(ch, limit=3)
    for m in msgs:
        doc = getattr(m, "document", None)
        if doc:
            print(f"[*] msg {m.id}: doc id={doc.id} dc=? ah={doc.access_hash} fr_len={len(doc.file_reference or b'')} size={doc.size}", flush=True)
            # dc_id: location
            dc_id = getattr(m.media.document, "dc_id", None)
            print(f"    dc_id attr: {dc_id}", flush=True)
            # try to get location dc
            try:
                loc = c.session.dc_id  # upload DC = session dc (same DC upload)
            except Exception:
                loc = None
            print(f"    session dc: {loc}", flush=True)
            fid = make_doc_file_id(loc, doc.id, doc.access_hash, doc.file_reference)
            print(f"    file_id: {fid[:50]}...", flush=True)
            # getFile with masterbot (K1) — cross-bot
            ok, sz, desc = getFile(K1, fid)
            print(f"    [masterbot getFile] ok={ok} size={sz} desc={desc}", flush=True)
            # getFile with bot3's own token
            t3 = BOT_TOKENS.get("bot3", "")
            if t3:
                ok2, sz2, desc2 = getFile(t3, fid)
                print(f"    [bot3 getFile] ok={ok2} size={sz2} desc={desc2}", flush=True)
    await c.disconnect()
    print("[done]", flush=True)

asyncio.run(main())
