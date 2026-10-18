# E-commerce Recommendation System

This project is under construction. Phase 1 establishes the local project structure for a React frontend, FastAPI backend, Supabase schema work, and recommendation ML scripts. Phase 2 delivers the database schema and authentication. Phase 3 delivers the recommendation engine, API routes, and frontend features.

## Structure

- `frontend/` - Vite, React, TypeScript, and Tailwind CSS application.
- `backend/` - FastAPI application package, backend tests, and ML script area.
- `supabase/migrations/` - database migrations with schema, constraints, indexes, trigger, and RLS policies.
- `supabase/seed.sql` - seed categories and products for local development.
- `docs/` - verification and phase reports.
- `.github/copilot-instructions.md` - persistent project implementation rules.

## Local Setup

### Frontend

```powershell
Set-Location -LiteralPath "frontend"
npm install
npm run build
```

### Backend

```powershell
Set-Location -LiteralPath "backend"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python -m pytest
```

## Environment Files

Only example environment files are committed. Real `.env` files are ignored.

- `frontend/.env.example` documents public frontend variables.
- `backend/.env.example` documents backend-only Supabase and CORS variables.

## Database

The initial schema lives in `supabase/migrations/20261014120000_initial_schema.sql`, the atomic recommendation-replace function in `supabase/migrations/20261014130000_replace_recommendations_rpc.sql`, and seed data in `supabase/seed.sql`.

Apply locally (requires Docker with a working Linux engine):

```powershell
npx supabase start
npx supabase db reset
npx supabase db lint --local
```

Apply to a linked Supabase Cloud project:

```powershell
npx supabase link --project-ref <project-ref>
npx supabase db push
```

Schema summary:

- `profiles` - mirrors `auth.users`, created by the `on_auth_user_created` trigger.
- `categories` - catalogue categories.
- `products` - catalogue products referencing `categories`.
- `interactions` - user/product interactions using the `interaction_type` enum.
- `recommendations` - ranked, scored, model-versioned rows written only by trusted backend credentials.

## Current Status

Phases 1-3 are implemented. Phase 2 is verified against Supabase Cloud (project ref `ffnyvlbjnkvkkexvkgbr`); the schema migration, trigger, indexes, RLS policies, and seed data are applied, and RLS/trigger behavior was tested with real users. Phase 3 adds an item-item collaborative-filtering engine (`item-cf-v1`) with a popularity fallback, FastAPI routes (`/health`, `/categories`, `/products`, `/interactions`, `/recommendations`), and a React frontend for catalogue browsing, interaction tracking, and recommendations.

Local Supabase verification was not possible on this host because Docker's Linux engine cannot start (WSL2/virtualization unavailable); verification uses Supabase Cloud.

Authentication note: the Supabase Cloud project issues **ES256** user JWTs. The backend verifies them against the project JWKS (`app/auth.py`) and keeps symmetric HS256 as a fallback for legacy/local projects.

See `docs/phase-2-verification.md` and `docs/phase-3-verification.md` for the full verification reports, evidence, and environment deviations.

## Backend API

Run locally (requires `backend/.env` with `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_JWT_SECRET`, `CORS_ORIGINS`):

```powershell
Set-Location -LiteralPath "backend"
.\.venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --reload
```

Generate recommendations for every user offline:

```powershell
python -m ml.generate_recommendations
```

Remaining work for later phases: integration test hardening (including an ES256 unit test) and deployment documentation.
