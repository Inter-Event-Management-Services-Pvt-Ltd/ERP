# Storage Conventions

All buckets are private.

## Buckets

```text
project-documents
generated-archives
generated-labels
document-previews
profile-assets
```

## Object Key Format

```text
project-documents/
  <project_uuid>/
    <document_uuid>/
      <document_version_uuid>/
        <sanitized-original-filename>
```

Example:

```text
37f.../
  71a.../
    c14.../
      quotation-v3.pdf
```

The folder tree shown to employees is rebuilt from PostgreSQL, not inferred from Storage object names.

## Signed URLs

Suggested defaults:

```text
Document preview URL: 15 minutes
Document download URL: 15 minutes
Generated ZIP URL: 15 minutes
Generated archive retention: 24 hours
```

## Upload Limits

MVP default:

```text
100 MiB per uploaded file
```

Large media uploads should be handled separately if required later.
