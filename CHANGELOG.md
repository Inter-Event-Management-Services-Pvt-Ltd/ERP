# Changelog

## Unreleased

- Validated local Supabase Phase 0 foundation from a clean Docker-backed environment.
- Hardened Supabase migrations by moving `citext` and `pg_trgm` into the `extensions` schema.
- Hardened SQL helper functions with explicit `search_path` settings and RLS-friendly `auth.uid()` usage.
- Enabled RLS on every exposed `public` table, preserving default-deny for tables without explicit policies.
- Converted public dashboard views to `security_invoker` views and scoped Storage object reads to authenticated users.
- Added Phase 0 SQL validation probes for schema, constraints, RLS, Storage buckets, audit immutability, and Director bootstrap logic.
- Initialized the repository as a Git repo on `main` with the provided GitHub SSH remote.
- Tracked Claude frontend planning docs under `docs/superpowers/`.
- Added the initial FastAPI shell with health/readiness routes, configuration loading, request IDs, stable error envelopes, and `uv` test/lint/type-check tooling.

- Assigned Claude as frontend-only owner using either Claude Design or Google Stitch for reviewed UI ideation.
- Assigned Codex as backend-only owner.
- Added frontend security, accessibility and motion guidance.
- Added agent ownership matrix and dedicated agent checklists.

- Added agent handoff documentation.
- Added phase checklists.
- Added security checkpoints.
- Included Supabase migration starter kit.
- Marked managed Supabase PostgreSQL as the active production direction.

- Added downloadable Codex and Claude `SKILL.md` packs.
- Added project-scoped Codex Supabase MCP template.
- Added project-scoped Claude Playwright MCP template.
- Added MCP and skills setup documentation.
- Added agent skill validation script.
