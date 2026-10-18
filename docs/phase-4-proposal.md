# Phase 4 Proposal - Hardening And Deployment Readiness

Status: Proposed (not started). Requires explicit approval before implementation.
Date: 2026-10-18

## Purpose

Phase 3 delivered and verified the end-to-end recommendation flow. Phase 4 is a
hardening and deployment-readiness phase: it closes the concrete gaps recorded in
the Phase 3 review and report, adds pagination and configuration safety, and
documents how to deploy and operate the system.

This document is a proposal. It defines the intended scope so it can be approved,
adjusted, or replaced with the project's own Phase 4 specification.

## Guiding Constraints

From `.github/copilot-instructions.md`:

- Service-role and JWT secrets stay backend-only; the frontend uses only `VITE_*`.
- Keep model-version tracking on recommendation rows.
- Do not claim a requirement complete without executed verification evidence.
- Prefer small, typed, testable changes.

## Scope

### A. API hardening and pagination

- Add `limit`/`offset` pagination to `GET /products` and `GET /interactions`
  with a sane default and a hard maximum. Return a stable ordering.
- Keep `GET /recommendations` `limit` bounded (already 1-50) and document it.
- Add response models that expose only the fields the client needs for list
  endpoints (avoid `select("*")` where practical).
- Tests for pagination boundaries (default, max clamp, offset past end).

### B. CORS and configuration safety

- Narrow CORS to explicit `allow_methods` (e.g. `GET`, `POST`) and
  `allow_headers` (`Authorization`, `Content-Type`) instead of `["*"]`.
- Reject a `*` value in `CORS_ORIGINS` at startup when credentials are enabled.
- Fail fast with a clear error when required backend settings are missing.
- Tests for origin parsing and the `*` rejection path.

### C. Frontend robustness

- Stop surfacing raw backend error bodies to users; show a generic message and
  log details only in development.
- Surface a friendly offline/error state in the UI.
- Optional: derive the interaction-type union from the OpenAPI schema (or a
  single shared constant) to remove the FE/BE contract duplication.

### D. Offline job operability

- Add a `--dry-run` mode to `ml/generate_recommendations.py` that computes and
  reports without writing.
- Add an explicit confirmation flag for real runs, and skip/limit by user where
  useful (e.g. `--limit N`).
- Document the intended runbook against a target project.

### E. Deployment documentation

- `docs/deployment.md` covering:
  - backend hosting (env vars, start command, CORS), never exposing service-role
    or JWT secrets to the frontend.
  - frontend build and hosting with `VITE_*` values only.
  - applying Supabase migrations (`supabase db push`) and seeding.
  - running the offline recommendation job on a schedule.
  - the ES256/JWKS vs HS256 authentication behavior and what each deployment
    setup requires.
- `README.md` deployment and operations section with links.

### F. Integration test hardening

- Add an end-to-end backend test that exercises the ES256/JWKS path against a
  generated key pair (already partially covered) and a full
  interactions -> recommendations flow through the API with a fake/isolated
  client.
- Optional: a documented, optional CI workflow (`pytest`, `ruff`, frontend
  build). No secrets in CI config.

### G. Documentation accuracy fixes

- Correct the stale README "Remaining work" line that still lists "an ES256 unit
  test" as outstanding; it was added in Phase 3.
- Update `docs/phase-3-verification.md` cross-references if needed.

## Proposed Deliverables

| Area | Files (proposed) |
|---|---|
| Pagination | `backend/app/routers/catalog.py`, `interactions.py`, `schemas.py`, tests |
| CORS/config | `backend/app/main.py`, `config.py`, tests |
| Frontend robustness | `frontend/src/lib/api.ts`, `App.tsx`, components |
| Offline job flags | `backend/ml/generate_recommendations.py`, tests |
| Deployment docs | `docs/deployment.md`, `README.md` |
| Test hardening | `backend/tests/*` |
| Doc fixes | `README.md` |

## Verification Plan (executed, not assumed)

- `python -m pytest` and `python -m ruff check .` (backend).
- `npm run build` (frontend typecheck + build).
- Exercised pagination/limit boundaries and CORS rejection via tests.
- Dry-run and confirmed offline job runs against Supabase Cloud.
- `docs/deployment.md` steps followed end to end (or explicitly marked as
  documented-but-not-executed where the host cannot support it).

## Out Of Scope (unless you add it)

- New recommendation models or algorithm changes.
- New product features beyond hardening the Phase 3 surface.
- Enabling local Docker/Supabase (still blocked on this host by missing
  WSL2/virtualization).

## Open Questions

1. Is deployment meant for a specific platform (container host, serverless,
   static frontend host), or should `docs/deployment.md` stay
   platform-agnostic?
2. Should a CI workflow be added, or is CI handled elsewhere?
3. Any Phase 4 requirements from the original project spec that differ from this
   proposal?

## Stop Point

Implementation of Phase 4 should not begin without explicit approval of this
scope (or a replacement specification).