
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
  const r = await fetch(`${env.SB_URL}/rest/v1/${table}?${query}`, {
    headers: { apikey: env.SB_KEY, Authorization: `Bearer ${env.SB_KEY}`, "User-Agent": "kts-worker" },
  });
  if (!r.ok) return null;
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

async function ghDispatch(env, event, payload) {
  if (!env.GH_TOKEN || !env.GH_REPO) return { ok: false, err: "GH not configured" };
  const body = { event_type: event, client_payload: payload || {} };
  const r = await fetch(`https://api.github.com/repos/${env.GH_REPO}/dispatches`, {
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

async function ghRunActive(env) {
  if (!env.GH_TOKEN || !env.GH_REPO) return false;
  const r = await fetch(`https://api.github.com/repos/${env.GH_REPO}/actions/runs?status=in_progress&per_page=1`, {
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

async function ghSaveCommits(env) {
  if (!env.GH_TOKEN || !env.GH_REPO) return 0;
  try {
    const r = await fetch(`https://api.github.com/repos/${env.GH_REPO}/commits?per_page=20`, {
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
  try {
    const docs = await sbGet(env, "progress", `select=id,state&id=like.${prefix}%25&limit=2000`);
    if (!docs) return 0;
    docs.sort((a, b) => ((a.state && a.state.at) || 0) - ((b.state && b.state.at) || 0));
    let del = 0;
    while (docs.length > max) {
      const old = docs.shift();
      if (await sbDeleteRow(env, old.id)) del++;
    }
    return del;
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

async function ghSaveRunLog(env, w) {
  if (!env.SB_URL || !env.SB_KEY || !env.GH_TOKEN || !env.GH_REPO) return false;
  try {
    const hdrs = { Authorization: `Bearer ${env.GH_TOKEN}`, Accept: "application/vnd.github+json", "User-Agent": "kts-worker" };
    const jr = await fetch(`https://api.github.com/repos/${env.GH_REPO}/actions/runs/${w.id}/jobs`, { headers: hdrs });
    if (!jr.ok) {
      console.log("janitor: jobs fetch fail", w.id, jr.status);
      return false;
    }
    const jd = await jr.json();
    let log = "";
    for (const j of jd.jobs || []) {
      try {
        const lr = await fetch(`https://api.github.com/repos/${env.GH_REPO}/actions/jobs/${j.id}/logs`, { headers: hdrs, redirect: "manual" });
        if (lr.status === 301 || lr.status === 302) {
          const loc = lr.headers.get("location");
          if (loc) {
            const lr2 = await fetch(loc, { headers: { "User-Agent": "kts-worker" } });
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
    const row = {
      id: `log_${w.id}`,
      state: {
        run_id: String(w.id),
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

async function ghCleanupRuns(env) {
  if (!env.GH_TOKEN || !env.GH_REPO) return { del: 0, saved: 0 };
  let del = 0, saved = 0;
  try {
    const r = await fetch(`https://api.github.com/repos/${env.GH_REPO}/actions/runs?per_page=50&status=completed`, {
      headers: { Authorization: `Bearer ${env.GH_TOKEN}`, Accept: "application/vnd.github+json", "User-Agent": "kts-worker" },
    });
    if (!r.ok) return { del, saved };
    const d = await r.json();
    const now = Date.now();
    let processed = 0;
    for (const w of d.workflow_runs || []) {
      if (processed >= 5) break; // per tick limit (subrequest 50 limit)
      const done = new Date(w.updated_at).getTime();
      if (now - done < 7 * 60 * 1000) continue; // abhi bhi fresh ho sakta hai (logs finalize)
      processed++;
      console.log("janitor: processing run", w.id, "age", Math.round((now - done) / 60000), "min");
      const okSave = await ghSaveRunLog(env, w);
      if (okSave) saved++;
      else continue; // save fail -> delete mat karo, agli tick par retry
      const delr = await fetch(`https://api.github.com/repos/${env.GH_REPO}/actions/runs/${w.id}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${env.GH_TOKEN}`, Accept: "application/vnd.github+json", "User-Agent": "kts-worker" },
      });
      if (delr.ok) del++;
    }
  } catch (e) {}
  return { del, saved };
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
      let q = `select=*&order=at.desc&limit=${lim}`;
      if (show) q += `&show=eq.${encodeURIComponent(show)}`;
      if (stt) q += `&status=eq.${encodeURIComponent(stt)}`;
      const docs = await sbGet(env, "episodes", q);
      if (docs === null) return json({ error: "sb not configured" }, 500);
      return json(docs);
    }

    if (url.pathname === "/api/episode") {
      const id = url.searchParams.get("id") || "";
      if (!id) return json({ error: "id required" }, 400);
      const docs = await sbGet(env, "episodes", `select=*&id=eq.${encodeURIComponent(id)}&limit=1`);
      return json((docs && docs[0]) || null);
    }

    if (url.pathname === "/api/stats") {
      const docs = await sbGet(env, "episodes", "select=*&limit=500");
      if (docs === null) return json({ error: "sb not configured" }, 500);
      const byShow = {};
      let total = 0, totalSize = 0;
      for (const d of docs) {
        total++;
        totalSize += d.size || 0;
        const k = d.show || "?";
        byShow[k] = byShow[k] || { count: 0, size: 0 };
        byShow[k].count++;
        byShow[k].size += d.size || 0;
      }
      return json({ total, totalSize, byShow });
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

    if (url.pathname === "/api/runlogs") {
      if (!checkAdmin(request, env)) return json({ error: "unauthorized" }, 401);
      const docs = await sbGet(env, "progress", "select=state&id=like.log%25&limit=500");
      if (docs === null) return json({ error: "sb fail" }, 500);
      const list = (docs || [])
        .map((d) => d.state || {})
        .sort((a, b) => (b.at || 0) - (a.at || 0))
        .slice(0, 100)
        .map((s) => ({
          run_id: s.run_id || "",
          result: s.result || "?",
          at: s.at || 0,
          preview: (s.log || "").slice(0, 150),
        }));
      return json(list);
    }

    // /api/commits (admin) — saved commit backups
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

    return json({ error: "not found" }, 404);
  },

  async scheduled(event, env, ctx) {
    try {
      // ORDER: dispatch PEHLE (Cloudflare subrequest limit 50 — janitor/backup baad mein best-effort)
      const pause = await sbGetRow(env, "pause");
      if (pause && pause.state && pause.state.paused) {
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

      if (await ghRunActive(env)) {
        console.log("cron: run already active, skip");
        return;
      }

      // DISPATCH — guaranteed (pehle)
      const res = await ghDispatch(env, "run-task", {});
      console.log("cron: dispatch run-task ->", JSON.stringify(res));

      // janitor: sirf 5 runs per tick (subrequest limit 50 ke andar rahe)
      try {
        const jn = await ghCleanupRuns(env);
        console.log("cron: janitor ->", JSON.stringify(jn));
      } catch (e) {
        console.log("cron: janitor err", String(e).slice(0, 80));
      }

      // commits backup + rolling prune (chhota: 20 commits per tick)
      try {
        const cs = await ghSaveCommits(env);
        const pl = await sbPruneCount(env, "log_", 500);
        const pc = await sbPruneCount(env, "commit_", 500);
        const ps = await sbPruneSize(env, 10 * 1024 * 1024);
        if (cs > 0 || pl > 0 || pc > 0 || ps > 0) console.log("cron: backup commits=" + cs + " pruneLogs=" + pl + " pruneCommits=" + pc + " pruneSize=" + ps);
      } catch (e) {
        console.log("cron: backup err", String(e).slice(0, 80));
      }
    } catch (e) {
      console.log("cron error:", String(e));
    }
  },
};
