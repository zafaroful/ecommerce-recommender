# Deployment Rehearsal Report

Status: Partially complete; blocked only on deployment credentials/environment.
Date: 2026-10-18

## Purpose

This records the immediate pre-Phase-5 deployment rehearsal performed after the
Phase 4 checkpoint commit.

## Executed Checks

| Area | Command | Result |
|---|---|---|
| Git checkpoint | `git status --short` | Passed - working tree was clean before rehearsal |
| Supabase CLI | `npx supabase --version` | Passed - CLI version `2.121.0` |
| Supabase project link | `npx supabase projects list` | Passed - linked to `ecommerce-recommender` project `ffnyvlbjnkvkkexvkgbr` |
| Backend tests | `python -m pytest` | Passed - 42 tests |
| Backend lint | `python -m ruff check .` | Passed |
| Frontend production build | `npm run build` | Passed |
| Backend settings load | settings import check | Passed - backend settings load locally without printing secrets |
| Backend health | `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000`, then `GET /health` | Passed - returned `status: ok` |
| Offline job dry run | `python -m ml.generate_recommendations --dry-run` | Passed - preview completed for 0 user(s), no writes |

## Blocked Or Not Executed

`npx supabase migration list` could not connect to the remote database because
`SUPABASE_DB_PASSWORD` is not configured in the shell environment:

```text
password authentication failed for user "postgres"
Connect to your database by setting the env var correctly: SUPABASE_DB_PASSWORD
```

`npx supabase status` could not inspect local Supabase because Docker Linux
Engine is unavailable on this host:

```text
failed to connect to the docker API at npipe:////./pipe/dockerDesktopLinuxEngine
```

Remote `supabase db push`, frontend hosting deployment, backend hosting
deployment, and a confirmed offline write were not executed because they require
target deployment credentials and host access.

## Before Phase 5

The codebase is locally verified and ready for Phase 5 planning. If a real
deployment is required before Phase 5, provide or configure the target deployment
credentials first:

- `SUPABASE_DB_PASSWORD` for migration inspection/push.
- Backend host environment variables from `backend/.env.example`.
- Frontend host `VITE_*` variables from `frontend/.env.example`.
- The final frontend origin for backend `CORS_ORIGINS`.
