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
- Added Supabase JWT verification and current employee resolution for `GET /v1/me`.
- Added centralized RBAC/ABAC services and `GET /v1/me/permissions`.
- Fixed current-user role-assignment resolution by disambiguating the Supabase PostgREST relationship.
- Added a local-only API access-token helper for exercising protected FastAPI routes against local Supabase.
- Added Super User override recording with atomic Supabase audit-event insertion.
- Added structured JSON API access logging and a minimal Celery worker scaffold.
- Added backend CI for Ruff, MyPy and Pytest.
- Added Phase 2 clients/projects API routes, typed schemas, RBAC/ABAC checks, audited transactional Supabase RPCs, folder-template application, folder-tree reads, and backend tests.
- Hardened custom Supabase trigger functions by revoking direct execution from `anon` and `authenticated` and adding trigger security validation.
- Added deterministic local demo seed data for Phase 2 client/project testing, including demo employees, clients, contacts, projects, memberships, and folder trees.
- Resolved Phase 2 frontend integration blockers by adding configured CORS, project reference lookup endpoints, project-member listing, and a server-side email-domain allowlist for local/staging auth.
- Fixed project visibility for assigned managers by ensuring project create/update RPCs grant active `MANAGE` project membership to the selected `project_manager_id` and backfill existing projects.
- Added a limited `GET /v1/employees` directory lookup for project-member assignment and employee-directory consumers, with manager access restricted to assignable employee statuses.
- Added field-level details to `VALIDATION_ERROR` responses without echoing submitted values, making invalid create-project payloads easier to debug.
- Completed project CRUD by adding audited `DELETE /v1/projects/{project_id}` soft delete with RBAC/ABAC checks and no hard deletion.
- Completed client CRUD by adding audited `DELETE /v1/clients/{client_id}` deactivation with RBAC checks and no hard deletion.
- Added explicit project-member role updates via `PATCH /v1/projects/{project_id}/members/{employee_id}` with audited access-level changes and last-manager protection.
- Added Phase 2 folder/document APIs with audited folder writes, server-side file upload validation, immutable private Storage keys, document versioning, SHA-256 checksums, preview capability flags, and short-lived signed download URLs.
- Added Phase 2 archive export APIs and Celery ZIP worker with folder hierarchy preservation, exact exported version records, manifest generation, document-index PDF generation, private archive Storage writes, export expiration and requester notifications.
- Added Phase 2 physical archive APIs for rooms, hierarchical locations, physical files, labels, checkout, return, movement and verification with audited transactional SQL RPCs and double-checkout prevention.
- Validated the Docker-backed Phase 2 archive-export dependencies by starting Redis plus the Celery worker and scheduler while keeping the normal local FastAPI server host-run; the worker registers `iems.archive_exports.generate`.
- Fixed Supabase Storage signed download URL normalization so backend responses include `/storage/v1/object/sign/...`.
- Added document upload lookup endpoints for confidentiality levels and document types.
- Fixed document search route ordering and accepted `q` as a search alias for frontend compatibility.
- Added queued archive export cancellation with audited `CANCELLED` state and worker skip behavior.
- Fixed archive ZIP generation to write explicit directory entries for every active folder, preserving empty folders in downloaded exports.

- Wired Phase 2 folder CRUD to live backend: inline create, rename, and delete in FolderTreePanel with INVALID_STATE protection and canManage gating.
- Added DocumentListPanel with per-folder document list, multipart upload dialog (INVALID_FILE_NAME, INVALID_MIME_TYPE, INVALID_FILE_SIZE error display), version upload, and signed download URLs fetched on-demand.
- Added ArchiveExportPanel with auto-polling (5 s when QUEUED/PROCESSING, stops when idle), READY download via signed URL, and 202-QUEUED feedback.
- Added physical archive screens: rooms overview, room detail with location browser, file detail (state badge, QR label with copy, action links), and checkout/return/move/verify forms with INVALID_PHYSICAL_FILE_STATE handling.
- Added lib/errors.ts mapping all documented backend error codes to user-facing strings.
- Added OPEN-025 (document search param names to confirm), OPEN-026 (confidentiality and document-type lookup endpoints), OPEN-027 (list locations by room), OPEN-028 (QR library approval).
- Resolved OPEN-024 (Phase 2 frontend wiring complete).
- Fixed hydration error: split folder-tree node row into sibling expand-button and action-buttons to remove nested <button> elements.

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
