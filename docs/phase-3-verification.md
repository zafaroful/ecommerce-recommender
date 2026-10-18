# Phase 3 Verification Report - Recommendation Engine, API, And Frontend

Status: Complete.
Date: 2026-10-14

## Scope

Phase 3 covers the recommendation engine, the FastAPI routes that expose the
catalogue, interactions, and recommendations, and the React frontend that
consumes them.

Deliverables:

- Backend foundation: `app/config.py`, `app/supabase_client.py`, `app/auth.py`.
- Recommendation engine: `ml/engine.py` (pure logic) and
  `app/services/recommender.py` (Supabase bridge).
- Offline job: `ml/generate_recommendations.py`.
- API routes: `app/routers/health.py`, `catalog.py`, `interactions.py`,
  `recommendations.py`, wired in `app/main.py` with CORS and schemas in
  `app/schemas.py`.
- Frontend: `src/lib/supabase.ts`, `src/lib/api.ts`, `src/auth/AuthContext.tsx`,
  `src/components/AuthPanel.tsx`, `ProductCard.tsx`, `RecommendationsPanel.tsx`,
  and a rebuilt `src/App.tsx`.
- Tests: `tests/test_engine.py`, `tests/test_auth.py`, `tests/test_routes.py`,
  `tests/test_recommender_service.py`.
- Atomic write support: `supabase/migrations/20261014130000_replace_recommendations_rpc.sql`.
- Verification helper: `scripts/verify_live.py`.

## Recommendation Engine

Model version: `item-cf-v1`.

- Weighted interaction signals: view 1, click 2, add_to_cart 3, purchase 5,
  rating = the rating value (1-5).
- Item-item collaborative filtering from user-item co-occurrence; a user's
  candidate score sums `user_weight x co-occurrence` across their items.
- Fallback to popularity (with a preferred top-category boost) for cold-start
  users and for users whose history produces no co-occurring candidates.
- Already-seen products are excluded.
- Deterministic: scores rounded to 6 dp and ties break on product id, so ranks
  are stable across runs.

## Verification Results

All checks below were executed. "Passed" means executed successfully.

| Requirement | Test method | Result |
|---|---|---|
| Engine unit behaviour | `python -m pytest` | Passed - 31 tests, all passed |
| Lint clean | `python -m ruff check .` | Passed - all checks passed |
| Frontend typecheck + build | `npm run build` (tsc -b && vite build) | Passed - built in ~2.5s |
| API image boots | `uvicorn app.main:app` | Passed - `/health` HTTP 200 `{"status":"ok"}` |
| Catalogue served | `GET /products` | Passed - 13 active products |
| Auth required on user routes | `GET /recommendations` without token | Passed - HTTP 401 |
| Interaction recorded for authed user | `POST /interactions` with real JWT | Passed - HTTP 201 |
| Recommendations generated | `GET /recommendations` with real JWT | Passed - `model_version=item-cf-v1`, item returned |
| Seen products excluded | compare recommendations to view history | Passed - no overlap |
| Collaborative filtering works | seeded co-occurrence for a second user | Passed - the co-occurring product was recommended |
| Model-version persistence | query `recommendations` by `user_id` + `model_version` | Passed - rows stored with `item-cf-v1` |
| Atomic replace function applied | `supabase db push` + `pg_proc` lookup | Passed - `replace_recommendations` present |
| Cross-user isolation | second user's recommendations | Passed - returned only in-catalogue, user-scoped items |
| Offline job runs | `python -m ml.generate_recommendations` | Passed - completed using `item-cf-v1` |
| Live script opt-in guard | run without `ALLOW_LIVE_VERIFY` | Passed - refused to run (exit 2) |
| Cleanup | delete test users, re-count tables | Passed - profiles/interactions/recommendations = 0 |

Live evidence (from `ALLOW_LIVE_VERIFY=1 python -m scripts.verify_live`):

```
health: 200 {'status': 'ok'}
products: 13
recorded views for both users
unauthenticated recommendations: 401
model_version: item-cf-v1 items: 1
other-user items: 0
stored recommendation rows: 1
LIVE VERIFICATION PASSED
test users deleted
```

## Environment Deviation Carried Forward

Local Supabase/Docker still cannot run on this host (no WSL2/virtualization);
verification used the Supabase Cloud project `ffnyvlbjnkvkkexvkgbr`, as in
Phase 2.

## Authentication Finding (Important)

The Supabase Cloud project signs user JWTs with the **ES256** algorithm using an
asymmetric ECC key, not the legacy symmetric HS256 `SUPABASE_JWT_SECRET`.

Evidence:

- Token header: `{"alg": "ES256", "kid": "6ff8c679-...", "typ": "JWT"}`.
- `python-jose` HS256 decode with `SUPABASE_JWT_SECRET` failed with
  `JWSError: The specified alg value is not allowed`.
- The project JWKS endpoint `/auth/v1/.well-known/jwks.json` returned an `EC`
  key whose `kid` matches the token header.

`app/auth.py` verifies ES256 tokens against the project JWKS (cached public
keys, refreshed on an unknown `kid`) and validates the key `kty`/`alg` before
use. The algorithm is pinned to `ES256` for the JWKS path and `HS256` for the
secret path; the verifier no longer trusts the token's `alg` header to choose
the algorithm or the verification path. HS256 remains a fallback for
legacy/local symmetric projects when no JWKS key matches.

## Post-Review Hardening

A local review of the uncommitted changes produced fixes that are included here:

- JWT verification now pins the algorithm per path and validates the JWKS key
  type; verification-path selection no longer branches on unverified token
  header fields (`app/auth.py`).
- The recommendation request path bounds the interaction load by a 90-day
  window with a hard sample cap (`app/services/recommender.py`, constants
  `INTERACTION_WINDOW_DAYS`, `INTERACTION_SAMPLE_LIMIT`).
- `store_recommendations` now calls an atomic server-side function so the
  delete+insert can no longer lose a user's rows mid-way
  (`supabase/migrations/20261014130000_replace_recommendations_rpc.sql`,
  `public.replace_recommendations`).
- The offline job loads global interactions/products once and scores every user
  against that shared context instead of re-reading the tables per user
  (`ml/generate_recommendations.py`, `services.recommender.load_catalog_context`,
  `generate_from_context`).
- The frontend decouples interaction recording from refresh: it records the
  event and refreshes on a 2s debounce, guarded against overlapping in-flight
  requests (`frontend/src/App.tsx`).
- The live verification script requires an explicit `ALLOW_LIVE_VERIFY=1` opt-in
  and takes the test password from `LIVE_VERIFY_PASSWORD` when set
  (`backend/scripts/verify_live.py`).

New tests: `tests/test_recommender_service.py` covers context loading, scoring
without extra queries, and atomic replacement. `tests/test_auth.py` now covers
the ES256/JWKS path (generated EC key) and rejection of a forged-header token.

## Credentials

`backend/.env` (git-ignored) holds the backend `SUPABASE_*` and `CORS_ORIGINS`
values derived from the root `.env`. The frontend uses only `VITE_*` values.

## Known Limitations

- The engine still computes item-item similarity in-process; the request path is
  now bounded (90-day window, capped sample), but very large datasets would
  benefit from precomputed neighbourhoods produced by the offline job.
- `GET /interactions` and `GET /products` remain unpaginated; acceptable for the
  current seed size but a follow-up should add limit/offset and field
  projection.
- Frontend has no component test runner; verification relies on `tsc -b` plus
  `vite build`.
- Local Docker/Supabase remains unavailable on this host.
- The offline job rewrites every user's rows and has no dry-run flag yet; run it
  deliberately against the intended project.

## Stop Point

Phase 4 (whatever the plan defines next) should not begin without explicit
approval.