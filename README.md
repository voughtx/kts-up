# KTS-Up 🚀

Doraemon (Kartoons.me) episodes auto-upload to Telegram channel **HF-Anime**.

## System
- **app.py** — main pipeline: Kartoons API (PoW+AES) → Katfile convert → multi-session bot upload → channel post → Supabase/Mongo save
- **worker.js** — Cloudflare Worker: cron `*/5` dispatch + janitor + `/api/*` endpoints + pause/resume + dashboard API
- **FastTelethon.py** — patched FastTelethon: `upload_file_multi()` multi-session split upload (speed: ~20-40 MB/s)
- **make_bot_sessions.py** — bot session factory (maintenance; 24 sessions stored in Supabase `bot_sessions`)
- **backfill.py** — DB backfill tool (backfill.yml workflow)

## Workflows
| Workflow | Trigger | Kaam |
|----------|---------|------|
| main.yml | cron (worker dispatch) / manual | Episode pipeline (1 episode per run) |
| tools.yml | manual (script input) | Any tool script |
| backfill.yml | manual (doc input) | DB backfill |

## Speed mode
- Upload: **multi-session split** (same bot × 4 sessions, ~40s per 500MB episode)
- **AUTO_CONTINUE=1** (default): run complete → 60s → next run auto-dispatch (pause ON pe skip)
- STATUS_MSG: default OFF (channel clean — sirf episode posts)

## Secrets (GitHub Actions)
KEY_1..KEY_37 — bot tokens, sessions, Kartoons API, MongoDB, Supabase, Telegram API.
