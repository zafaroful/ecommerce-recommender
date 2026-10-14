# E-commerce Recommendation System

This project is under construction. Phase 1 establishes the local project structure for a React frontend, FastAPI backend, Supabase schema work, and recommendation ML scripts.

## Structure

- `frontend/` - Vite, React, TypeScript, and Tailwind CSS application.
- `backend/` - FastAPI application package, backend tests, and ML script area.
- `supabase/migrations/` - database migrations with schema, constraints, indexes, trigger, and RLS policies.
- `supabase/seed.sql` - seed categories and products for local development.
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

The initial schema lives in `supabase/migrations/20261014120000_initial_schema.sql` and seed data in `supabase/seed.sql`.

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

Phase 2 in progress. The schema migration, trigger, indexes, RLS policies, and seed data are authored. Runtime verification with local Supabase was blocked because Docker's Linux engine could not start on this host (WSL2/virtualization unavailable), so RLS behavior checks were not executed here. Recommendation logic, API routes, frontend features, integration tests, and deployment documentation remain planned for later phases.
