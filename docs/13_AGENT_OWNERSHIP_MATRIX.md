# Agent Ownership Matrix

## Claude — Frontend and Design

| Area | Claude responsibility |
|---|---|
| Next.js application | Own |
| UI components | Own |
| Design system | Own |
| Responsive layouts | Own |
| Accessibility | Own |
| Motion | Own |
| Claude Design or Google Stitch ideation workflow | Own |
| Frontend tests | Own |
| API consumption | Own |
| Backend API design | Propose changes only |
| Database | No changes |
| RLS | No changes |
| Celery | No changes |

## Codex — Backend and Data

| Area | Codex responsibility |
|---|---|
| FastAPI application | Own |
| Database migrations | Own |
| Supabase local validation | Own |
| RLS | Own |
| RBAC and ABAC | Own |
| Audit logs | Own |
| Storage signed URLs | Own |
| Celery and Redis | Own |
| Offline ZIP exports | Own |
| QR and PDF generation | Own |
| Backend tests | Own |
| Next.js UI | No changes |
| Design system | No changes |
| Motion | No changes |

## Shared Contract

The shared boundary is:

```text
docs/api-contract.md
```

Rules:

1. Codex owns server implementation.
2. Claude consumes documented endpoints.
3. API contract changes must be documented.
4. Backend errors must use stable error codes.
5. Frontend must not infer authorization from hidden UI.
6. Human approval is required for cross-boundary edits.
