
function json(o, s) {
  return new Response(JSON.stringify(o), {
    status: s || 200,
    headers: {
      "Content-Type": "application/json",
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type,Authorization",
    },
  });
}

const TG = atob("aHR0cHM6Ly9hcGkudGVsZWdyYW0ub3Jn");
const TF = atob("aHR0cHM6Ly9hcGkudGVsZWdyYW0ub3JnL2ZpbGUvYm90");

async function sha256hex(s) {
  const b = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(s));
  return [...new Uint8Array(b)].map((x) => x.toString(16).padStart(2, "0")).join("");
}

async function sbGet(env, table, query) {
  if (!env.SB_URL || !env.SB_KEY) return null;
  let r;
  try {
    r = await fetch(`${env.SB_URL}/rest/v1/${table}?${query}`, {
      headers: { apikey: env.SB_KEY, Authorization: `Bearer ${env.SB_KEY}`, "User-Agent": "kts-worker" },
    });
  } catch (e) {
    console.log("sbGet fetch throw", table, String(e).slice(0, 120));
    return null;
  }
  if (!r.ok) {
    const txt = await r.text().catch(() => "");
    console.log("sbGet fail", table, r.status, txt.slice(0, 120));
    return null;
  }
  return r.json();
}

async function sbGetRow(env, id) {
  const docs = await sbGet(env, "progress", `select=state&id=eq.${encodeURIComponent(id)}&limit=1`);
  return (docs && docs[0]) || null;
}

async function sbPostRow(env, row) {
  if (!env.SB_URL || !env.SB_KEY) return false;
  const r = await fetch(`${env.SB_URL}/rest/v1/progress`, {
    method: "POST",
    headers: { apikey: env.SB_KEY, Authorization: `Bearer ${env.SB_KEY}`, "Content-Type": "application/json", "Prefer": "resolution=merge-duplicates", "User-Agent": "kts-worker" },
    body: JSON.stringify(row),
  });
  return r.ok;
}

async function ghDispatch(env, event, payload, repo) {
  const rp = repo || env.GH_REPO || "";
  if (!env.GH_TOKEN || !rp) return { ok: false, err: "GH not configured" };
  const body = { event_type: event, client_payload: payload || {} };
  const r = await fetch(`https://api.github.com/repos/${rp}/dispatches`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${env.GH_TOKEN}`,
      Accept: "application/vnd.github+json",
      "Content-Type": "application/json",
      "User-Agent": "kts-worker",   // GitHub API REQUIRES User-Agent — bina ye 403 deta hai!
    },
    body: JSON.stringify(body),
  });
  if (!r.ok) return { ok: false, err: `github dispatch fail`, status: r.status };
  return { ok: true };
}

async function ghRunActive(env, repo) {
  const rp = repo || env.GH_REPO || "";
  if (!env.GH_TOKEN || !rp) return false;
  const r = await fetch(`https://api.github.com/repos/${rp}/actions/runs?status=in_progress&per_page=1`, {
    headers: {
      Authorization: `Bearer ${env.GH_TOKEN}`,
      Accept: "application/vnd.github+json",
      "User-Agent": "kts-worker",
    },
  });
  if (!r.ok) return false;
  const d = await r.json();
  return (d.total_count || 0) > 0;
}

// Janitor helpers: commits backup + rolling prune (500 max, size watchdog 10MB)
async function sbDeleteRow(env, id) {
  try {
    const r = await fetch(`${env.SB_URL}/rest/v1/progress?id=eq.${encodeURIComponent(id)}`, {
      method: "DELETE",
      headers: { apikey: env.SB_KEY, Authorization: `Bearer ${env.SB_KEY}`, "User-Agent": "kts-worker" },
    });
    return r.ok;
  } catch (e) { return false; }
}

async function sbDeleteRows(env, ids) {
  // BULK delete — id=in.(a,b,c) ek request mein (subrequest limit save)
  if (!ids || !ids.length) return 0;
  let del = 0;
  for (let i = 0; i < ids.length; i += 80) {
    const chunk = ids.slice(i, i + 80);
    const q = chunk.map((x) => encodeURIComponent(x)).join(",");
    try {
      const r = await fetch(`${env.SB_URL}/rest/v1/progress?id=in.(${q})`, {
        method: "DELETE",
        headers: { apikey: env.SB_KEY, Authorization: `Bearer ${env.SB_KEY}`, "User-Agent": "kts-worker" },
      });
      if (r.ok) del += chunk.length;
    } catch (e) {}
  }
  return del;
}

async function ghSaveCommits(env, repo) {
  const rp = repo || env.GH_REPO || "";
  if (!env.GH_TOKEN || !rp) return 0;
  try {
    const r = await fetch(`https://api.github.com/repos/${rp}/commits?per_page=20`, {
      headers: { Authorization: `Bearer ${env.GH_TOKEN}`, Accept: "application/vnd.github+json", "User-Agent": "kts-worker" },
    });
    if (!r.ok) return 0;
    const d = await r.json();
    let saved = 0;
    for (const c of d || []) {
      const ca = (c.commit && c.commit.author) || {};
      const row = {
        id: `commit_${String(c.sha || "").slice(0, 12)}`,
        state: {
          sha: String(c.sha || "").slice(0, 12),
          msg: String((c.commit && c.commit.message) || "").slice(0, 200),
          author: String(ca.name || ""),
          at: Math.floor(new Date(ca.date || Date.now()).getTime() / 1000),
        },
      };
      if (await sbPostRow(env, row)) saved++;
    }
    return saved;
  } catch (e) { return 0; }
}

async function sbPruneCount(env, prefix, max) {
  // FIX(2026-08-11): supabase REST max limit = 1000 (2000 -> 400 error).
  // FIX(2026-08-11b): BULK delete (id=in.()) — pehle 1-by-1 delete 500 subrequests leta tha
  // (CF free limit 50) isliye prune kabhi complete nahi hota tha.
  // FIX(2026-08-11c): SINGLE PASS — har tick pe 1 fetch + ~7 bulk delete (limit 50 ke andar).
  // Har tick ~500 purane delete -> backlog dheere-dheere clear.
  try {
    const docs = await sbGet(env, "progress", `select=id,state&id=like.${prefix}%25&limit=1000&offset=0`);
    if (!docs || !docs.length) return 0;
    docs.sort((a, b) => ((a.state && a.state.at) || 0) - ((b.state && b.state.at) || 0));
    const excess = docs.slice(0, docs.length - max);
    if (!excess.length) return 0;
    return await sbDeleteRows(env, excess.map((d) => d.id));
  } catch (e) { return 0; }
}

async function sbPruneSize(env, maxBytes) {
  try {
    const docs = await sbGet(env, "progress", "select=id,state&id=like.log%25&limit=2000");
    if (!docs) return 0;
    let total = 0;
    for (const d of docs) total += String((d.state && d.state.log) || "").length;
    docs.sort((a, b) => ((a.state && a.state.at) || 0) - ((b.state && b.state.at) || 0));
    let del = 0;
    while (total > maxBytes && docs.length) {
      const old = docs.shift();
      total -= String((old.state && old.state.log) || "").length;
      if (await sbDeleteRow(env, old.id)) del++;
    }
    return del;
  } catch (e) { return 0; }
}

async function ghSaveRunLog(env, w, repo) {
  const rp = repo || env.GH_REPO || "";
  if (!env.SB_URL || !env.SB_KEY || !env.GH_TOKEN || !rp) return false;
  try {
    const hdrs = { Authorization: `Bearer ${env.GH_TOKEN}`, Accept: "application/vnd.github+json", "User-Agent": "kts-worker" };
    const jr = await fetch(`https://api.github.com/repos/${rp}/actions/runs/${w.id}/jobs`, { headers: hdrs });
    if (!jr.ok) {
      console.log("janitor: jobs fetch fail", w.id, jr.status);
      return false;
    }
    const jd = await jr.json();
    let log = "";
    for (const j of jd.jobs || []) {
      try {
        // manual redirect: blob host ko Authorization mat do (401 deta hai) — UA-only fetch
        const lr = await fetch(`https://api.github.com/repos/${rp}/actions/jobs/${j.id}/logs`, { headers: hdrs, redirect: "manual" });
        if (lr.status === 301 || lr.status === 302 || lr.status === 303) {
          const loc = lr.headers.get("location");
          if (loc) {
            const lr2 = await fetch(loc, { headers: { "User-Agent": "kts-worker", "Accept": "text/plain" } });
            if (lr2.ok) log += (await lr2.text()) + "\n";
            else console.log("janitor: blob fetch fail", w.id, lr2.status);
          }
        } else if (lr.ok) {
          log += (await lr.text()) + "\n";
        } else {
          console.log("janitor: logs fetch fail", w.id, "job", j.id, lr.status);
        }
      } catch (e) {
        console.log("janitor: logs fetch err", String(e).slice(0, 120));
      }
    }
    if (!log.trim()) {
      console.log("janitor: empty log for", w.id);
      return false;
    }
    const KEEP = /\[ok\]|\[!\]|\[x\]|\[dbg\]|\[\*\]|next:|converting|ready|msg_id|upload|DONE|progress|Traceback|Error|token|relay|supabase|gh release/;
    let lines = log.split("\n").filter((l) => KEEP.test(l));
    if ((w.conclusion || "") !== "success") {
      lines = lines.concat(log.split("\n").slice(-60));
    }
    const txt = lines.join("\n").slice(-8000);
    // speed parse (avg of last valid MB/s readings)
    let speeds = [];
    const spRe = /([\d.]+) MB\/s/g;
    let sm;
    while ((sm = spRe.exec(log)) !== null) {
      const v = parseFloat(sm[1]);
      if (v > 0 && v < 250) speeds.push(v);
    }
    const last10 = speeds.slice(-10);
    const avgSpeed = last10.length ? Math.round((last10.reduce((a, b) => a + b, 0) / last10.length) * 10) / 10 : 0;
    const repoNorm = String(rp || "").replace(/\//g, "_");
    const row = {
      id: `log_${w.id}`,
      state: {
        run_id: String(w.id),
        repo: repoNorm,
        avg_speed: avgSpeed,
        result: (w.conclusion || "") === "success" ? "success" : "failed",
        at: Math.floor(Date.now() / 1000),
        log: txt,
      },
    };
    return await sbPostRow(env, row);
  } catch (e) {
    return false;
  }
}

async function ghCleanupRuns(env, repo, budget) {
  const rp = repo || env.GH_REPO || "";
  if (!env.GH_TOKEN || !rp) return { del: 0, saved: 0, processed: 0 };
  let del = 0, saved = 0, processed = 0;
  try {
    const r = await fetch(`https://api.github.com/repos/${rp}/actions/runs?per_page=100&status=completed`, {
      headers: { Authorization: `Bearer ${env.GH_TOKEN}`, Accept: "application/vnd.github+json", "User-Agent": "kts-worker" },
    });
    if (!r.ok) return { del, saved, processed };
    const d = await r.json();
    const now = Date.now();
    // OLDEST-FIRST: purane runs pehle clean (naye 7-min fresh window mein rehte hain)
    const list = (d.workflow_runs || []).slice().reverse();
    for (const w of list) {
      if (processed >= budget) break; // shared budget across repos (subrequest 50 limit)
      const done = new Date(w.updated_at).getTime();
      if (now - done < 7 * 60 * 1000) continue; // abhi bhi fresh ho sakta hai (logs finalize)
      processed++;
      console.log("janitor:", rp, "run", w.id, "age", Math.round((now - done) / 60000), "min");
      const ageMin = (now - done) / 60000;
      // LOG SAVE = best-effort (time-limited 20s). DELETE = priority.
      // Runs 30min+ purane hamesha delete hote hain (log save fail ho to bhi) —
      // backup kharab na ho iske liye save pehle try hota hai.
      let okSave = false;
      if (ageMin >= 10) {
        // FIX(2026-08-11): log pehle se saved hai to fetch+save skip (subrequest budget bachao)
        try {
          const existing = await sbGetRow(env, "log_" + w.id);
          if (existing) {
            okSave = true;
          } else {
            const ctl = new AbortController();
            const to = setTimeout(() => ctl.abort(), 20000);
            const ok = await ghSaveRunLog(env, w, rp);
            clearTimeout(to);
            okSave = !!ok;
          }
        } catch (e) {
          okSave = false;
        }
      }
      if (okSave) saved++;
      if (!okSave && ageMin < 30) {
        console.log("janitor:", rp, "run", w.id, "save fail, age", Math.round(ageMin), "min -> retry next tick");
        continue;
      }
      if (!okSave) console.log("janitor:", rp, "run", w.id, "save fail, age", Math.round(ageMin), "min -> delete anyway");
      const delr = await fetch(`https://api.github.com/repos/${rp}/actions/runs/${w.id}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${env.GH_TOKEN}`, Accept: "application/vnd.github+json", "User-Agent": "kts-worker" },
      });
      if (delr.ok) del++;
    }
  } catch (e) {}
  return { del, saved, processed };
}

async function tgAlert(env, text) {
  if (!env.BOT_TOKEN || !env.CHAT_ID) return;
  try {
    await fetch(`${TG}/bot${env.BOT_TOKEN}/sendMessage`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ chat_id: env.CHAT_ID, text }),
    });
  } catch (e) {}
}

function checkAdmin(request, env) {
  const auth = (request.headers.get("Authorization") || "").replace("Bearer ", "");
  return env.ADMIN_KEY && auth === env.ADMIN_KEY;
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    if (request.method === "OPTIONS") {
      return new Response("ok", {
        headers: {
          "Access-Control-Allow-Origin": "*",
          "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
          "Access-Control-Allow-Headers": "Content-Type,Authorization",
        },
      });
    }

    if (url.pathname === "/health") {
      return json({ ok: true, ready: !!env.BOT_TOKEN, db: !!env.SB_URL });
    }

    if (url.pathname === "/debug") {
      return json({
        bot: !!env.BOT_TOKEN,
        db: !!env.SB_URL,
        gh_token: !!env.GH_TOKEN,
        gh_tail: env.GH_TOKEN ? env.GH_TOKEN.slice(-4) : "",
        gh_repo: env.GH_REPO || "",
        admin: !!env.ADMIN_KEY,
        url_key: !!env.URL_KEY,
      });
    }

    const v = url.pathname.match(/^\/v\/([A-Za-z0-9_\-]+)$/);
    if (v) {
      const f = v[1];
      if (!env.BOT_TOKEN) return json({ error: "not configured" }, 500);
      const exp = parseInt(url.searchParams.get("exp") || "0", 10);
      const sig = url.searchParams.get("sig") || "";
      if (exp) {
        if (!env.URL_KEY) return json({ error: "URL_KEY not set" }, 500);
        if (Date.now() / 1000 > exp) return json({ error: "link expired" }, 403);
        const want = await sha256hex(env.URL_KEY + f + exp);
        if (sig !== want) return json({ error: "bad signature" }, 403);
      }
      const gf = await fetch(`${TG}/bot${env.BOT_TOKEN}/getFile?file_id=${encodeURIComponent(f)}`);
      const gj = await gf.json();
      if (!gj.ok) return json({ error: gj.description || "getFile failed" }, 502);
      const p = gj.result.file_path;
      const st = await fetch(`${TF}/${env.BOT_TOKEN}/${p}`);
      if (!st.ok) return json({ error: "unavailable" }, 404);
      const nm = decodeURIComponent((url.pathname.split("/").pop() || "media")) + ".mp4";
      return new Response(st.body, {
        status: 200,
        headers: {
          "Content-Type": "video/mp4",
          "Content-Disposition": `attachment; filename="${nm}"`,
          "Cache-Control": "public, max-age=3600",
          "Access-Control-Allow-Origin": "*",
        },
      });
    }

    const mm = url.pathname.match(/^\/m\/([A-Za-z0-9_,\-]+)$/);
    if (mm) {
      const ids = mm[1].split(",").filter(Boolean);
      if (ids.length < 2) return json({ error: "need >=2 ids" }, 400);
      if (!env.BOT_TOKEN) return json({ error: "not configured" }, 500);
      let l = ["#EXTM3U", "#EXT-X-VERSION:3", "#EXT-X-TARGETDURATION:1800", "#EXT-X-MEDIA-SEQUENCE:0"];
      for (let i = 0; i < ids.length; i++) {
        const gf = await fetch(`${TG}/bot${env.BOT_TOKEN}/getFile?file_id=${encodeURIComponent(ids[i])}`);
        const gj = await gf.json();
        if (!gj.ok) return json({ error: `part ${i + 1} invalid` }, 404);
        l.push("#EXTINF:1800.0,");
        l.push("#EXT-X-DISCONTINUITY");
        l.push(`${url.origin}/v/${ids[i]}`);
      }
      l.push("#EXT-X-ENDLIST");
      return new Response(l.join("\n"), {
        status: 200,
        headers: {
          "Content-Type": "application/vnd.apple.mpegurl",
          "Content-Disposition": 'attachment; filename="merged.m3u8"',
          "Cache-Control": "no-cache",
          "Access-Control-Allow-Origin": "*",
        },
      });
    }

    if (url.pathname === "/api/episodes") {
      const lim = Math.min(parseInt(url.searchParams.get("limit") || "100", 10) || 100, 500);
      const show = url.searchParams.get("show") || "";
      const stt = url.searchParams.get("status") || "";
      const all = url.searchParams.get("all") === "1";
      const extra = (show ? `&show=eq.${encodeURIComponent(show)}` : "") + (stt ? `&status=eq.${encodeURIComponent(stt)}` : "");
      let docs;
      if (all) {
        // ALL-TIME: paginate (supabase limit max 1000/req) up to 6000 rows
        docs = [];
        let off = 0;
        while (off < 6000) {
          const chunk = await sbGet(env, "episodes", `select=*&order=at.desc&limit=1000&offset=${off}${extra}`);
          if (chunk === null) return json({ error: "sb not configured" }, 500);
          if (!chunk.length) break;
          docs.push(...chunk);
          if (chunk.length < 1000) break;
          off += 1000;
        }
      } else {
        docs = await sbGet(env, "episodes", `select=*&order=at.desc&limit=${lim}${extra}`);
        if (docs === null) return json({ error: "sb not configured" }, 500);
      }
      return json(docs);
    }

    if (url.pathname === "/api/episode") {
      const id = url.searchParams.get("id") || "";
      if (!id) return json({ error: "id required" }, 400);
      const docs = await sbGet(env, "episodes", `select=*&id=eq.${encodeURIComponent(id)}&limit=1`);
      return json((docs && docs[0]) || null);
    }

    if (url.pathname === "/api/stats") {
      // ALL-TIME stats: paginate every episode row (up to 20000)
      const docs = [];
      let off = 0, fail = false;
      while (off < 20000) {
        const chunk = await sbGet(env, "episodes", `select=*&limit=1000&offset=${off}`);
        if (chunk === null) { fail = true; break; }
        if (!chunk.length) break;
        docs.push(...chunk);
        if (chunk.length < 1000) break;
        off += 1000;
      }
      if (fail && !docs.length) return json({ error: "sb not configured" }, 500);
      const byShow = {};
      let total = 0, totalSize = 0, thumb = 0, today = 0, last24 = 0;
      const nowS = Date.now() / 1000;
      for (const d of docs) {
        total++;
        totalSize += d.size || 0;
        if (d.thumb) thumb++;
        if (d.at && nowS - d.at < 86400) today++;
        const k = d.show || "?";
        byShow[k] = byShow[k] || { count: 0, size: 0 };
        byShow[k].count++;
        byShow[k].size += d.size || 0;
      }
      last24 = docs.filter((d) => d.at && nowS - d.at < 86400).length;
      return json({ total, totalSize, byShow, thumb, today, last24, allTime: true });
    }

    if (url.pathname === "/api/queue") {
      // LIVE SHOW QUEUE — ordered list from Supabase `showlist` doc + real counts
      const sl = await sbGet(env, "progress", "select=state&id=eq.showlist&limit=1");
      const shows = (sl && sl[0] && sl[0].state && Array.isArray(sl[0].state.shows)) ? sl[0].state.shows : [];
      const docs = [];
      let off = 0, fail = false;
      while (off < 20000) {
        const chunk = await sbGet(env, "episodes", `select=show&limit=1000&offset=${off}`);
        if (chunk === null) { fail = true; break; }
        if (!chunk.length) break;
        docs.push(...chunk);
        if (chunk.length < 1000) break;
        off += 1000;
      }
      if (fail && !docs.length) return json({ error: "sb not configured" }, 500);
      const norm = (s) => String(s || "").toLowerCase().replace(/[^a-z0-9]/g, "");
      const per = {};
      for (const d of docs) {
        const k = norm(d.show);
        if (k) per[k] = (per[k] || 0) + 1;
      }
      const out = shows.map((s) => ({
        id: s.id || "",
        name: s.name || "?",
        total: parseInt(s.total, 10) || 0,
        done: per[norm(s.name)] || 0,
      }));
      return json({ shows: out, updated: Math.floor(Date.now() / 1000), allTime: true });
    }

    if (url.pathname === "/api/progress") {
      const docs = await sbGet(env, "progress", "select=state&id=eq.main&limit=1");
      return json((docs && docs[0] && docs[0].state) || {});
    }

    if (url.pathname === "/api/control" && request.method === "POST") {
      if (!checkAdmin(request, env)) return json({ error: "unauthorized" }, 401);
      let body = {};
      try { body = await request.json(); } catch (e) {}
      const ev = body.event || "run-task";
      const res = await ghDispatch(env, ev, body.payload || {});
      if (!res.ok) return json({ error: res.err, status: res.status || 0 }, res.status || 502);
      return json({ ok: true, event: ev });
    }

    if (url.pathname === "/api/relay" && request.method === "POST") {
      if (!checkAdmin(request, env)) return json({ error: "unauthorized" }, 401);
      let body = {};
      try { body = await request.json(); } catch (e) {}
      const id = (body.id || "").toString();
      if (!id) return json({ error: "id required" }, 400);
      const res = await ghDispatch(env, "relay-task", { id: id });
      if (!res.ok) return json({ error: res.err, status: res.status || 0 }, res.status || 502);
      return json({ ok: true, event: "relay-task", id: id });
    }

    if (url.pathname === "/api/token") {
      if (!checkAdmin(request, env)) return json({ error: "unauthorized" }, 401);
      if (request.method === "POST") {
        let body = {};
        try { body = await request.json(); } catch (e) {}
        const tk = (body.token || "").trim();
        if (!tk) return json({ error: "token required" }, 400);
        let ok = false;
        let dbg = { status: 0 };
        try {
          const v = await fetch(atob("aHR0cHM6Ly9hcGkua2FydG9vbnMubWUvYXBpL3Nob3dzL2VwaXNvZGUvNjg2ZjQxYjBhMTkxNDY2MTZkOGFiNDY4L2xpbmtz"), {
            headers: { "X-Challenge-Token": tk, "Authorization": `Bearer ${tk}`, "User-Agent": "kts-worker", "Origin": atob("aHR0cHM6Ly9rYXJ0b29ucy5tZQ=="), "Referer": atob("aHR0cHM6Ly9rYXJ0b29ucy5tZQ==") + "/" },
          });
          dbg = { status: v.status, url: v.url, ct: (v.headers.get("content-type") || "").slice(0, 40) };
          ok = v.status === 428 || v.status === 200;
        } catch (e) {
          dbg.err = String(e).slice(0, 120);
        }
        // fallback: /auth/me Bearer 200 = login token valid (links par security flag ho to)
        if (!ok) {
          try {
            const a = await fetch(atob("aHR0cHM6Ly9hcGkua2FydG9vbnMubWUvYXBpL2F1dGgvbWU="), {
              headers: { "Authorization": `Bearer ${tk}`, "User-Agent": "kts-worker", "Origin": atob("aHR0cHM6Ly9rYXJ0b29ucy5tZQ=="), "Referer": atob("aHR0cHM6Ly9rYXJ0b29ucy5tZQ==") + "/" },
            });
            dbg.auth = a.status;
            ok = a.status === 200;
          } catch (e) {
            dbg.autherr = String(e).slice(0, 80);
          }
        }
        if (!ok) return json({ ok: false, err: "invalid token — rejected", dbg }, 400);
        if (!ok) return json({ ok: false, err: "invalid token — rejected" }, 400);
        if (!env.SB_URL || !env.SB_KEY) return json({ ok: false, err: "sb not configured" }, 500);
        const row = { id: "token", state: { token: tk, at: Math.floor(Date.now() / 1000) } };
        const r = await fetch(`${env.SB_URL}/rest/v1/progress`, {
          method: "POST",
          headers: { apikey: env.SB_KEY, Authorization: `Bearer ${env.SB_KEY}`, "Content-Type": "application/json", "Prefer": "resolution=merge-duplicates", "User-Agent": "kts-worker" },
          body: JSON.stringify(row),
        });
        if (!r.ok) return json({ ok: false, err: "supabase save fail" }, 502);
        return json({ ok: true, verified: true, saved: true });
      }
      const docs = await sbGet(env, "progress", "select=state&id=eq.token&limit=1");
      const st = (docs && docs[0] && docs[0].state) || {};
      return json({
        saved: !!(st.token || "").trim(),
        at: st.at || 0,
        masked: (st.token || "").trim() ? String(st.token).slice(-4) : "",
      });
    }

    if (url.pathname === "/api/pause") {
      if (!checkAdmin(request, env)) return json({ error: "unauthorized" }, 401);
      if (request.method === "POST") {
        let body = {};
        try { body = await request.json(); } catch (e) {}
        const paused = body.paused === true || body.paused === "true";
        const ok = await sbPostRow(env, { id: "pause", state: { paused, at: Math.floor(Date.now() / 1000) } });
        if (!ok) return json({ ok: false, err: "supabase save fail" }, 502);
        return json({ ok: true, paused });
      }
      const row = await sbGetRow(env, "pause");
      const p = (row && row.state) || {};
      return json({ paused: !!p.paused, at: p.at || 0 });
    }

    if (url.pathname === "/api/health") {
      if (!checkAdmin(request, env)) return json({ error: "unauthorized" }, 401);
      const row = await sbGetRow(env, "health");
      return json((row && row.state) || { result: "none", at: 0 });
    }

    if (url.pathname === "/api/diag") {
      if (!checkAdmin(request, env)) return json({ error: "unauthorized" }, 401);
      let out = { sb_url: env.SB_URL || "", sb_key_len: (env.SB_KEY || "").length };
      try {
        const r = await fetch(`${env.SB_URL}/rest/v1/progress?select=state&id=eq.pause&limit=1`, {
          headers: { apikey: env.SB_KEY, Authorization: `Bearer ${env.SB_KEY}`, "User-Agent": "kts-worker" },
        });
        out.status = r.status;
        out.body = (await r.text()).slice(0, 200);
      } catch (e) {
        out.err = String(e).slice(0, 150);
      }
      return json(out);
    }

    if (url.pathname === "/api/runlogs") {
      if (!checkAdmin(request, env)) return json({ error: "unauthorized" }, 401);
      const lim = Math.min(parseInt(url.searchParams.get("limit") || "100", 10) || 100, 500);
      const all = url.searchParams.get("all") === "1";
      let docs = [];
      if (all) {
        let off = 0;
        while (off < 8000) {
          const chunk = await sbGet(env, "progress", `select=state&id=like.log%25&limit=1000&offset=${off}`);
          if (chunk === null) return json({ error: "sb fail" }, 500);
          if (!chunk.length) break;
          docs.push(...chunk);
          if (chunk.length < 1000) break;
          off += 1000;
        }
      } else {
        docs = await sbGet(env, "progress", "select=state&id=like.log%25&limit=2000");
        if (docs === null) return json({ error: "sb fail" }, 500);
      }
      const list = (docs || [])
        .map((d) => d.state || {})
        .sort((a, b) => (b.at || 0) - (a.at || 0))
        .slice(0, all ? 8000 : lim)
        .map((s) => ({
          run_id: s.run_id || "",
          repo: s.repo || "",
          result: s.result || "?",
          avg_speed: s.avg_speed || 0,
          at: s.at || 0,
          preview: (s.log || "").slice(0, 150),
        }));
      return json(list);
    }

    // /api/commits (admin) — saved commit backups
    if (url.pathname === "/api/status") {
      if (!checkAdmin(request, env)) return json({ error: "unauthorized" }, 401);
      // LIVE per-repo status (app.py har progress pe update karta hai)
      const docs = await sbGet(env, "progress", "select=id,state&id=like.status_%25&limit=20");
      const out = {};
      for (const d of docs || []) {
        const slug = String(d.id || "").replace("status_", "");
        out[slug] = d.state || {};
      }
      return json({ repos: out, at: Math.floor(Date.now() / 1000) });
    }

    if (url.pathname === "/api/analytics") {
      if (!checkAdmin(request, env)) return json({ error: "unauthorized" }, 401);
      try {
        // 1) run logs (per-repo analytics)
        const logs = await sbGet(env, "progress", "select=state&id=like.log%25&limit=2000");
        const byRepo = {};
        let totalRuns = 0, okRuns = 0, failRuns = 0;
        const day = 24 * 3600;
        const now = Math.floor(Date.now() / 1000);
        let runsToday = 0;
        for (const d of logs || []) {
          const st = d.state || {};
          const repo = String(st.repo || "unknown").replace(/\//g, "_");
          byRepo[repo] = byRepo[repo] || { runs: 0, ok: 0, fail: 0, last_at: 0, spds: [] };
          byRepo[repo].runs++;
          totalRuns++;
          if (st.result === "success") { byRepo[repo].ok++; okRuns++; }
          else { byRepo[repo].fail++; failRuns++; }
          if ((st.at || 0) > now - day) runsToday++;
          if ((st.at || 0) > byRepo[repo].last_at) byRepo[repo].last_at = st.at || 0;
          if (st.avg_speed) byRepo[repo].spds.push(st.avg_speed);
        }
        // 2) episodes (throughput + quality)
        const eps = await sbGet(env, "episodes", "select=*&limit=2000");
        let epTotal = 0, epToday = 0, sizeTotal = 0;
        const qMap = {};
        const showMap = {};
        for (const e of eps || []) {
          epTotal++;
          sizeTotal += e.size || 0;
          if ((e.at || 0) > now - day) epToday++;
          const q = (e.quality || "?").toLowerCase();
          qMap[q] = (qMap[q] || 0) + 1;
          const sh = e.show || "?";
          showMap[sh] = (showMap[sh] || 0) + 1;
        }
        const byRepoOut = {};
        for (const k of Object.keys(byRepo)) {
          const sp = (byRepo[k].spds || []).slice(-15);
          byRepoOut[k] = {
            runs: byRepo[k].runs,
            ok: byRepo[k].ok,
            fail: byRepo[k].fail,
            last_at: byRepo[k].last_at,
            avg_speed: sp.length ? Math.round((sp.reduce((a, b) => a + b, 0) / sp.length) * 10) / 10 : 0,
          };
        }
        // LIVE data merge (status rows se — abhi kya ho raha hai)
        let live = {};
        try {
          const stRows = await sbGet(env, "progress", "select=id,state&id=like.status_%25&limit=20");
          for (const d of stRows || []) {
            const slug = String(d.id || "").replace("status_", "").replace(/\//g, "_");
            live[slug] = d.state || {};
          }
        } catch (e) {}
        return json({
          runs: { total: totalRuns, ok: okRuns, fail: failRuns, today: runsToday },
          live,
          byRepo: byRepoOut,
          episodes: { total: epTotal, today: epToday, size: sizeTotal, byQuality: qMap, byShow: showMap },
          at: now,
        });
      } catch (e) {
        return json({ error: String(e).slice(0, 120) }, 500);
      }
    }

    if (url.pathname === "/api/commits") {
      if (!checkAdmin(request, env)) return json({ error: "unauthorized" }, 401);
      const docs = await sbGet(env, "progress", "select=state&id=like.commit%25&limit=500");
      if (docs === null) return json({ error: "sb fail" }, 500);
      const list = (docs || [])
        .map((d) => d.state || {})
        .filter((s) => s.sha)
        .sort((a, b) => (b.at || 0) - (a.at || 0))
        .slice(0, 100);
      return json(list);
    }

    if (url.pathname === "/api/runlog") {
      if (!checkAdmin(request, env)) return json({ error: "unauthorized" }, 401);
      const id = url.searchParams.get("id") || "";
      if (!id.startsWith("log_")) return json({ error: "id required" }, 400);
      const row = await sbGetRow(env, id);
      return json((row && row.state) || { run_id: id, result: "?", log: "(not found)" });
    }

    if (url.pathname === "/api/kproxy" || url.pathname === "/relay") {
      // kartoons.me API proxy — GH runner IPs blocked (403 Are you a human?)
      // CF edge se fetch karta hai (CF-to-CF challenge bypass)
      // AUTH: admin key (dashboard) YA X-KTS-Key relay key (app relay chain)
      const rk = request.headers.get("X-KTS-Key") || "";
      if (!checkAdmin(request, env) && rk !== "ktsrelay2026")
        return json({ error: "unauthorized" }, 401);
      const path = (url.searchParams.get("path") || "").trim();
      // relative path -> kartoons API; absolute URL -> direct fetch (binary segments bhi)
      let target;
      if (path.startsWith("http://") || path.startsWith("https://")) {
        target = path;
      } else if (path.startsWith("/")) {
        const apiBase = env.KAPI || "https://api.kartoons.me/api";
        target = apiBase + path;
      } else {
        return json({ error: "bad path" }, 400);
      }
      const apiBase = env.KAPI || "https://api.kartoons.me/api";
      const fwd = ["X-Challenge-Token", "X-Pow-Nonce", "X-Pow-Solution", "X-Challenge-Retry", "Authorization", "Referer", "Origin"];
      const hdrs = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
        "Accept": "application/json",
        "Origin": "https://kartoons.me/",
        "Referer": "https://kartoons.me/",
      };
      for (const h of fwd) {
        const v = request.headers.get(h);
        if (v) hdrs[h] = v;
      }
      // app relay format: h_<Header> query params
      for (const [k, v] of url.searchParams.entries()) {
        if (k.startsWith("h_") && v) hdrs[k.slice(2)] = v;
      }
      let body = null;
      if (request.method === "POST") {
        try { body = await request.text(); } catch (e) { body = null; }
        if (body) hdrs["Content-Type"] = "application/json";
      }
      try {
        const r = await fetch(target, {
          method: request.method,
          headers: hdrs,
          body: body || undefined,
        });
        const txt = await r.text();
        return new Response(txt, {
          status: r.status,
          headers: { "Content-Type": "application/json", "Access-Control-Allow-Origin": "*" },
        });
      } catch (e) {
        return json({ error: "proxy fetch fail: " + String(e).slice(0, 120) }, 502);
      }
    }

    return json({ error: "not found" }, 404);
  },

  async scheduled(event, env, ctx) {
    try {
      // SAFETY: SB fail hone pe dispatch BAND (ci runs ki bauchhar na ho)
      if (!env.SB_URL || !env.SB_KEY) {
        console.log("cron: SB not configured, dispatch disabled");
        return;
      }
      const pause = await sbGetRow(env, "pause");
      if (!pause) {
        console.log("cron: sb fetch fail, dispatch disabled");
        return;
      }
      if (pause.state && pause.state.paused) {
        console.log("cron: paused, skip");
        return;
      }

      const health = await sbGetRow(env, "health");
      const tok = await sbGetRow(env, "token");
      if (health && health.state && health.state.result === "token_expired") {
        const tokenFresh = tok && tok.state && tok.state.at > (health.state.at || 0);
        if (!tokenFresh) {
          console.log("cron: token expired, dispatch paused");
          const h = health.state;
          if (!h.alerted || Math.floor(Date.now() / 1000) - h.alerted > 6 * 3600) {
            await tgAlert(env, "🔑 API token expire!\nDashboard se naya token save karo — phir auto-upload resume ho jayega.");
            await sbPostRow(env, { id: "health", state: { ...h, alerted: Math.floor(Date.now() / 1000) } });
            console.log("cron: tg alert sent");
          }
          return;
        }
      }

      // MULTI-REPO: saare repos ko dispatch (agar active run nahi hai to)
      // CADENCE: run khud jaldi exit karta hai — cron har 5 min pe agli dispatch karta hai
      const repos = (env.GH_REPOS || env.GH_REPO || "voughtx/kts-up").split(",").map(x => x.trim()).filter(Boolean);
      for (const rp of repos) {
        try {
          if (await ghRunActive(env, rp)) {
            console.log("cron:", rp, "active, skip");
            continue;
          }
          const res = await ghDispatch(env, "run-task", {}, rp);
          console.log("cron: dispatch", rp, "->", JSON.stringify(res));
        } catch (e) {
          console.log("cron: dispatch err", rp, String(e).slice(0, 80));
        }
      }

      // JANITOR: PRUNE PEHLE (fresh subrequest budget — CF free limit 50), phir GH cleanup.
      // Bulk delete ~8 subrequests, cleanup check-first ~2/run (saved logs skip fetch).
      try {
        let jnTot = { del: 0, saved: 0 };
        // 1) rolling prune (log_ -> 500, commit_ -> 300, size cap)
        const pl = await sbPruneCount(env, "log_", 500);
        const pc = await sbPruneCount(env, "commit_", 300);
        const ps = await sbPruneSize(env);
        if (pl > 0 || pc > 0 || ps > 0)
          console.log("cron: prune logs=" + pl + " commits=" + pc + " size=" + ps);
        // 2) GH run cleanup — log saved-check ke saath (sirf delete purane ke liye)
        let budget = 10;
        for (const rp of repos) {
          const jn = await ghCleanupRuns(env, rp, Math.min(2, budget));
          jnTot.del += jn.del || 0;
          jnTot.saved += jn.saved || 0;
          budget -= jn.processed || 0;
          if (budget <= 0) break;
        }
        console.log("cron: janitor ->", JSON.stringify(jnTot));
        // 3) commits backup (last — sabse kam priority)
        for (const rp of repos) {
          try {
            const cs = await ghSaveCommits(env, rp);
            if (cs > 0) console.log("cron:", rp, "backup commits=" + cs);
          } catch (e2) {
            console.log("cron: commit backup err", String(e2).slice(0, 60));
          }
        }
      } catch (e) {
        console.log("cron: janitor err", String(e).slice(0, 80));
      }


    } catch (e) {
      console.log("cron error:", String(e));
    }
  },
};
