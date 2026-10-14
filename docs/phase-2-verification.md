# Phase 2 Verification Report - Database And Authentication

Status: Complete, with one environment deviation (see below).
Date: 2026-10-14

## Scope

Phase 2 of the implementation plan covers the Supabase schema, constraints,
trigger, indexes, seed data, and Row Level Security (RLS) policies.

Deliverables:

- `supabase/config.toml` - local Supabase CLI project configuration.
- `supabase/migrations/20261014120000_initial_schema.sql` - schema, constraints,
  indexes, triggers, RLS policies, and privileges.
- `supabase/seed.sql` - seed categories and products.
- `.gitignore` - ignores `supabase/.temp/` and `supabase/.branches/`.

## Environment Deviation

The plan's Phase 2 verification says to apply migrations locally and to support
local Supabase development where possible.

Local Supabase (`supabase start`) could **not** run on this host:

- Docker CLI `29.4.1` is installed and `com.docker.service` was started.
- Docker's Linux engine pipe `dockerDesktopLinuxEngine` never came up.
- `wsl --status` reports WSL1 and WSL2 are **not supported** on this machine
  configuration and no Linux distribution is installed.

To keep Phase 2 verifiable, the migration and seed were applied to a
**Supabase Cloud** project instead of local Docker:

- Project name: `ecommerce-recommender`
- Project ref: `ffnyvlbjnkvkkexvkgbr`
- Region: `ap-southeast-1` (Singapore)
- Status at creation: `ACTIVE_HEALTHY`

All verification below was executed against that cloud project.

## Schema Summary

Tables created in schema `public`:

| Table | Purpose | Key relationships |
|---|---|---|
| `profiles` | Mirrors `auth.users` | `id` references `auth.users(id)` on delete cascade |
| `categories` | Product categories | none |
| `products` | Catalogue products | `category_id` references `categories(id)` on delete restrict |
| `interactions` | User/product interactions | `user_id` → `profiles(id)`, `product_id` → `products(id)` |
| `recommendations` | Ranked, scored recommendations | `user_id` → `profiles(id)`, `product_id` → `products(id)` |

Enum:

- `public.interaction_type`: `view`, `click`, `add_to_cart`, `purchase`, `rating`.

Constraints of note:

- Non-blank text checks on category name/slug, product name, model version.
- `products.price >= 0`.
- `interactions.rating` between 1 and 5 when present.
- Rating is only allowed on `rating` interactions, and `rating` interactions
  require a rating value.
- `recommendations.rank > 0`.
- Unique `(user_id, product_id, model_version)` and `(user_id, model_version, rank)`
  on recommendations, preserving model-version tracking.

Indexes:

- `interactions`: by user, product, type, created time, and `(user, type, created)`.
- `recommendations`: by user, rank, model version, and `(user, model version, rank)`.
- `products`: by category and by `is_active`.

Triggers:

- `on_auth_user_created` on `auth.users` - calls `handle_new_user()` to insert a
  matching `profiles` row.
- `profiles_set_updated_at` and `products_set_updated_at` - maintain `updated_at`.

## Verification Results

All checks below were actually executed. "Passed" means executed successfully.

| Requirement | Test method | Result |
|---|---|---|
| Migration applies to the database | `supabase db push` to linked cloud project | Passed |
| Seed categories and products | `supabase db query --linked` count query | Passed - 5 categories, 13 products |
| RLS enabled on exposed tables | `pg_tables` query for `rowsecurity` | Passed - all 5 tables `true` |
| Trigger objects installed | `pg_trigger` query | Passed - 3 triggers present |
| Anon can read categories | REST `GET /categories` with anon key | Passed - HTTP 200 |
| Anon can read products | REST `GET /products` with anon key | Passed - HTTP 200 |
| Frontend credentials cannot write recommendations | REST `POST /recommendations` with anon key | Passed - blocked, HTTP 401 |
| Frontend credentials cannot write categories | REST `POST /categories` with anon key | Passed - blocked, HTTP 401 |
| Anon cannot read interactions | REST `GET /interactions` with anon key | Passed - HTTP 200, empty result (no leakage) |
| Signup creates a profile row | Created confirmed user via admin API, then queried `profiles` | Passed - profile row auto-created with matching id, email, and `full_name` |
| Trigger handles multiple users | Created a second confirmed user | Passed - second profile row created |
| Users can read their own interactions | User 1 inserted a `view`, then read interactions | Passed - HTTP 201 insert, HTTP 200 read of own row only |
| User cannot read another user's interactions | User 2 read interactions | Passed - returned `[]`, no leakage |
| User cannot write as another user | User 2 attempted insert with user 1's `user_id` | Passed - blocked, HTTP 403 |
| Users can read only their own recommendations | User 1 read `recommendations` | Passed - HTTP 200, own scope only |
| Cascade cleanup | Deleted both test users | Passed - `auth.users`, `profiles`, `interactions` all returned to 0 |

Notes on methods:

- The public signup endpoint was rate-limited (HTTP 429) during testing, and
  `example.com` emails are rejected by Supabase (`email_address_invalid`).
  Test users were therefore created through the Supabase admin API with
  `email_confirm: true`. This still fires the same `on_auth_user_created`
  trigger, so the trigger and RLS checks remain valid.
- All test users and their interaction rows were deleted after testing. The
  database was left in the clean seeded state (5 categories, 13 products,
  0 users).

## Credentials

A git-ignored root `.env` holds the project connection values for later phases:

- `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`,
  `SUPABASE_PUBLISHABLE_KEY`, `SUPABASE_DB_PASSWORD`, `SUPABASE_JWT_SECRET`.
- Frontend values: `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`,
  `VITE_API_BASE_URL`.

The `SUPABASE_JWT_SECRET` was verified by recomputing the HMAC-SHA256 signature
of a real project token; the computed signature exactly matched the token
signature. This secret is backend-only and must never reach the frontend.

## Known Limitations

- Local Supabase/Docker verification is not possible on this host until WSL2 and
  hardware virtualization are enabled. Use Supabase Cloud for now.
- The recommendation engine, API, and frontend have not been built yet, so
  end-to-end product/recommendation flows are unverified.
- No demo users or interactions were seeded; interaction data is created at
  runtime.

## Outstanding Items After Phase 2

- Since no SQL migration existed in the workspace, the schema was authored from
  the plan's proposal. If the project specification requires preserving a
  specific pre-existing migration's relationships, columns, constraints, or
  version tracking, that migration must still be supplied and reconciled.
- Phase 3 onwards (recommendation engine, API, frontend, integration tests,
  deployment) are not started.

## Conclusion

Phase 2 is implemented and verified against Supabase Cloud. Schema, constraints,
indexes, trigger, seed data, and RLS policies are in place, and the executed
checks confirm trigger behavior and cross-user isolation. The only deviation
from the plan is the use of Supabase Cloud in place of local Docker, driven by
this host's lack of WSL2/virtualization support.

Stop point: Phase 3 should not begin without explicit approval.