# Security Model

## Core Principle

```text
Default: DENY
```

Authorization is layered:

```text
Supabase Auth identity
→ FastAPI JWT validation
→ employee-account resolution
→ RBAC capability check
→ ABAC contextual check
→ database transaction
→ audit event
→ Supabase RLS defense-in-depth
```

## Identity

- Google sign-in through Supabase Auth
- only approved `@iemsnewdelhi.com` accounts
- employee records exist independently of auth identities
- disabled employees remain in historical records
- Director account: `director@iemsnewdelhi.com`

## Authorization

### RBAC

Broad capabilities:

```text
EMPLOYEE
MANAGER
ADMIN
SUPER_ADMIN
SUPER_USER
DIRECTOR
```

### ABAC

Contextual decisions based on:

```text
employee
department
project membership
access level
document type
confidentiality level
archive permission
resource state
action
```

### Super User

Super User does not mean silent bypass.

Required:

```text
meaningful reason
immutable override record
audit event
```

## File Storage

- all buckets private
- signed URLs only
- short expiration
- immutable storage keys
- user-visible hierarchy rebuilt from database
- content type and size validated
- optional malware scanning checkpoint before production

## Audit

Append-only audit events for:

```text
uploads
downloads
new document versions
archive exports
permission changes
approvals
attendance corrections
physical-file checkouts
returns
location changes
Super User overrides
```

## Release Security Gate

No production release until all items in:

```text
docs/checklists/SECURITY_GLOBAL.md
docs/checklists/SECURITY_RELEASE_GATE.md
```

are verified.
