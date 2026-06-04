# Background Jobs

Use Celery with Redis.

| Job | Trigger | Result |
|---|---|---|
| `generate_project_archive` | User requests ZIP export | ZIP file, manifest checksum and `archive_export_items` |
| `generate_folder_label_pdf` | Physical file created or label requested | Printable PDF label with QR code |
| `generate_document_index_pdf` | Archive export requested | Project document index |
| `generate_document_preview` | New file version uploaded | Browser-friendly preview |
| `calculate_checksum` | New upload | SHA-256 checksum |
| `detect_duplicate_document` | Checksum available | Duplicate warning |
| `notify_overdue_physical_files` | Scheduled | Employee and Director notifications |
| `notify_pending_approvals` | Scheduled | Pending-approval reminders |
| `notify_archive_verification_due` | Scheduled | Verification reminders |
| `expire_archive_exports` | Scheduled | Marks exports expired and removes generated ZIP objects |

## Archive Job Sequence

```text
Create archive_exports row: QUEUED
→ Worker marks GENERATING
→ Resolve current visible document versions
→ Rebuild human-readable folder tree
→ Generate manifest, label, index PDF and QR code
→ Create ZIP
→ Upload ZIP to generated-archives
→ Insert archive_export_items
→ Mark READY with expiration time
→ Create notification
```
