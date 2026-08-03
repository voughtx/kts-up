function json(obj, status = 200) {
  return new Response(JSON.stringify(obj), {
    status,
    headers: { "Content-Type": "application/json", "Access-Control-Allow-Origin": "*" },
  });
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    if (request.method === "OPTIONS") {
      return new Response("ok", {
        headers: {
          "Access-Control-Allow-Origin": "*",
          "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
          "Access-Control-Allow-Headers": "Content-Type",
        },
      });
    }

    if (url.pathname === "/health") {
      return json({ ok: true, ready: !!env.BOT_TOKEN });
    }

    // /v/<file_id> — single media stream
    const TG = atob("aHR0cHM6Ly9hcGkudGVsZWdyYW0ub3Jn");
    const TF = atob("aHR0cHM6Ly9hcGkudGVsZWdyYW0ub3JnL2ZpbGUvYm90");
    const m = url.pathname.match(/^\/v\/([A-Za-z0-9_\-]+)$/);
    if (m) {
      const fileId = m[1];
      if (!env.BOT_TOKEN) return json({ error: "not configured" }, 500);
      const gf = await fetch(
        `${TG}/bot${env.BOT_TOKEN}/getFile?file_id=${encodeURIComponent(fileId)}`
      );
      const gj = await gf.json();
      if (!gj.ok) return json({ error: gj.description || "getFile failed" }, 502);
      const filePath = gj.result.file_path;
      const stream = await fetch(`${TF}/${env.BOT_TOKEN}/${filePath}`);
      if (!stream.ok) return json({ error: "unavailable" }, 404);
      const name = decodeURIComponent((url.pathname.split("/").pop() || "media")) + ".mp4";
      return new Response(stream.body, {
        status: 200,
        headers: {
          "Content-Type": "video/mp4",
          "Content-Disposition": `attachment; filename="${name}"`,
          "Cache-Control": "public, max-age=3600",
          "Access-Control-Allow-Origin": "*",
        },
      });
    }

    // /m/<id1>,<id2>,... — merged playlist (all parts as one)
    const mm = url.pathname.match(/^\/m\/([A-Za-z0-9_,\-]+)$/);
    if (mm) {
      const ids = mm[1].split(",").filter(Boolean);
      if (ids.length < 2) return json({ error: "need >=2 ids" }, 400);
      if (!env.BOT_TOKEN) return json({ error: "not configured" }, 500);
      let lines = ["#EXTM3U", "#EXT-X-VERSION:3", "#EXT-X-TARGETDURATION:1800", "#EXT-X-MEDIA-SEQUENCE:0"];
      for (let i = 0; i < ids.length; i++) {
        const gf = await fetch(
          `${TG}/bot${env.BOT_TOKEN}/getFile?file_id=${encodeURIComponent(ids[i])}`
        );
        const gj = await gf.json();
        if (!gj.ok) return json({ error: `part ${i + 1} invalid` }, 404);
        lines.push("#EXTINF:1800.0,");
        lines.push("#EXT-X-DISCONTINUITY");
        lines.push(`${url.origin}/v/${ids[i]}`);
      }
      lines.push("#EXT-X-ENDLIST");
      return new Response(lines.join("\n"), {
        status: 200,
        headers: {
          "Content-Type": "application/vnd.apple.mpegurl",
          "Content-Disposition": `attachment; filename="merged.m3u8"`,
          "Cache-Control": "no-cache",
          "Access-Control-Allow-Origin": "*",
        },
      });
    }

    // /api/items — optional db listing (future dashboard)
    if (url.pathname === "/api/items" && env.DB_URL && env.DB_KEY) {
      const limit = Math.min(parseInt(url.searchParams.get("limit") || "50", 10) || 50, 200);
      const body = {
        dataSource: env.DB_SOURCE || "Cluster0",
        database: env.DB_NAME || "kts",
        collection: "episodes",
        filter: {},
        sort: { at: -1 },
        limit,
      };
      const r = await fetch(env.DB_URL + "/action/find", {
        method: "POST",
        headers: { "Content-Type": "application/json", "api-key": env.DB_KEY },
        body: JSON.stringify(body),
      });
      const j = await r.json();
      return json(j.documents || []);
    }

    return json({ error: "not found" }, 404);
  },
};
