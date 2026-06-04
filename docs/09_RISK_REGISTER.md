# Risk Register

| Risk | Impact | Mitigation | Phase |
|---|---|---|---|
| Migration package contains SQL errors | Blocks development | Run local reset before scaffolding | Phase 0 |
| Service-role key leaks to frontend | Critical breach | Server-only env, automated checks, review | All |
| Public Storage bucket exposes documents | Critical breach | Private buckets, signed URLs, tests | All |
| Weak ABAC implementation | Unauthorized access | Central authorization service, deny-by-default, tests | Phase 1 onward |
| Super User bypass is not audited | Accountability failure | Mandatory reason and immutable audit event | Phase 1 onward |
| Physical folder checkout race | Duplicate checkout | Partial unique index + transaction | Phase 2 |
| Offline ZIP contains wrong version | Archive inconsistency | Export manifest with exact document versions | Phase 2 |
| Backups cannot be restored | Data-loss risk | Restore test before launch | Phase 5 |
| Pilot users cannot use interface | Adoption failure | Pilot rollout and training | Phase 6 |
