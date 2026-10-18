# Deployment And Operations

This guide covers deployment readiness for the Phase 4 application: Supabase,
FastAPI backend, React frontend, and the offline recommendation job.

## Security Boundaries

- Backend-only secrets: `SUPABASE_SERVICE_ROLE_KEY` and `SUPABASE_JWT_SECRET`.
- Frontend variables must be limited to `VITE_SUPABASE_URL`,
  `VITE_SUPABASE_ANON_KEY`, and `VITE_API_BASE_URL`.
- Never put the service-role key or JWT secret into frontend hosting settings,
  static files, browser logs, CI artifacts, or public issue reports.

## Supabase

Apply migrations to a linked Supabase project:

```powershell
npx supabase link --project-ref <project-ref>
npx supabase db push
```

Seed catalogue data where appropriate:

```powershell
npx supabase db execute --file supabase/seed.sql
```

The schema includes RLS policies for user-owned interaction and recommendation
data. Recommendation rows are written by trusted backend credentials through the
`replace_recommendations` RPC so each user's current model-version rows are
replaced atomically.

## Backend

Runtime requirements:

- Python 3.11 or newer.
- Network access to the Supabase project.
- Environment variables from `backend/.env.example`.

Required backend environment variables:

- `SUPABASE_URL` - Supabase project URL.
- `SUPABASE_ANON_KEY` - Supabase anon key, used for auth metadata.
- `SUPABASE_SERVICE_ROLE_KEY` - backend-only key for trusted database access.
- `SUPABASE_JWT_SECRET` - required for legacy/local HS256 token verification;
  Supabase Cloud ES256 projects use JWKS first.
- `CORS_ORIGINS` - comma-separated browser origins allowed to call the API.

`CORS_ORIGINS=*` is rejected because the API allows credentials. Configure the
exact frontend origins instead, for example:

```text
CORS_ORIGINS=https://shop.example.com,https://preview.example.com
```

Install and run:

```powershell
Set-Location -LiteralPath "backend"
python -m pip install -e ".[dev]"
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Production hosts should run the app behind HTTPS and set health checks to
`GET /health`.

## Authentication Modes

Supabase Cloud projects may issue ES256 JWTs. The backend verifies those tokens
against the project's JWKS endpoint and pins verification to `ES256` for that
path.

Legacy or local Supabase projects may issue HS256 JWTs. If no matching JWKS key
is found, the backend falls back to `SUPABASE_JWT_SECRET` and pins verification
to `HS256`.

Do not choose the verification algorithm from an untrusted token header.

## Frontend

Runtime requirements:

- Node.js compatible with Vite 6.
- Public Supabase URL and anon key.
- Public backend base URL.

Build:

```powershell
Set-Location -LiteralPath "frontend"
npm install
npm run build
```

Frontend hosting variables:

```text
VITE_SUPABASE_URL=https://<project-ref>.supabase.co
VITE_SUPABASE_ANON_KEY=<anon-key>
VITE_API_BASE_URL=https://<api-host>
```

The generated `frontend/dist` directory can be deployed to any static host. Add
the static host origin to backend `CORS_ORIGINS` before release.

## Offline Recommendation Job

Preview a run without writes:

```powershell
Set-Location -LiteralPath "backend"
python -m ml.generate_recommendations --dry-run
```

Write recommendations for all users:

```powershell
python -m ml.generate_recommendations --confirm-write
```

Limit operational blast radius during checks:

```powershell
python -m ml.generate_recommendations --dry-run --limit 10
python -m ml.generate_recommendations --confirm-write --user-id <profile-id>
```

Schedule the confirmed command on a trusted backend worker or scheduler with the
same backend-only environment variables. Start with dry-run output in logs after
changing Supabase projects or environment values.

## Verification

Before release, run:

```powershell
Set-Location -LiteralPath "backend"
python -m pytest
python -m ruff check .
```

```powershell
Set-Location -LiteralPath "frontend"
npm run build
```

Optional live verification remains guarded by `ALLOW_LIVE_VERIFY=1` and should
only be executed against a target project where test users can be created and
deleted safely.
