# Project Rules

- Keep Supabase service-role credentials backend-only. Never expose them to frontend code, build output, documentation examples with real values, or client logs.
- The frontend may use only `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`, and `VITE_API_BASE_URL`.
- The backend and ML scripts are the only areas allowed to use `SUPABASE_SERVICE_ROLE_KEY`.
- Do not claim a requirement is complete without executed verification evidence.
- Keep generated ML artifacts out of version control unless explicitly requested.
- Use Supabase Row Level Security for user-owned data and test cross-user isolation when database work begins.
- Preserve model-version tracking on recommendation rows once the recommendation schema is implemented.
- Prefer small, typed, testable changes that match the current phase scope.
