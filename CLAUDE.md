# Claude Instructions — Frontend Owner for IEMS ERP

Follow `AGENTS.md` first.

# Scope

Claude owns only the frontend and design system:

```text
apps/web/**
docs/14_FRONTEND_DESIGN_SYSTEM.md
docs/15_FRONTEND_SECURITY_MOTION.md
docs/checklists/FRONTEND_CLAUDE.md
frontend screenshots and visual QA notes
```

Do not modify:

```text
apps/api/**
supabase/**
database migrations
RLS policies
Celery workers
backend authorization logic
deployment secrets
```

If the frontend needs a backend change, record it in `docs/07_OPEN_ITEMS.md` and propose an API-contract update for Codex.

# Design Workflow

Use **either Claude Design or Google Stitch** for visual exploration and screen ideation. Choose whichever is more suitable for the screen.

Google Stitch output is a starting point, not production-ready code.

Required workflow:

```text
Read product scope
→ Review target screen and user role
→ Create or refine screen concept using either Claude Design or Google Stitch
→ Check consistency with the IEMS design system
→ Manually implement reviewed UI in Next.js
→ Replace any unsafe or low-quality generated code
→ Validate responsive behaviour
→ Validate accessibility
→ Validate reduced-motion behaviour
→ Run frontend tests and build
→ Update checklist and changelog
```

# Frontend Priorities

Build a professional internal ERP interface:

- clean and modern
- low cognitive load
- responsive
- keyboard accessible
- clear data hierarchy
- fast navigation
- subtle motion
- strong empty, error, loading, and permission-denied states
- suitable for non-technical employees
- efficient for Director Dashboard scanning

# Security Requirements

Claude must enforce frontend security practices:

- never expose server secrets
- never expose the Supabase service-role key
- never trust frontend route guards as authorization
- do not use `dangerouslySetInnerHTML` unless a reviewed sanitization decision exists
- avoid rendering unsanitized user-controlled HTML
- use framework escaping by default
- validate forms client-side for usability, while assuming backend validation remains authoritative
- use safe download links returned by the backend
- do not guess object-storage paths
- do not embed unrestricted third-party scripts
- add or preserve Content Security Policy and security headers
- keep auth tokens out of local storage unless explicitly approved
- do not leak restricted metadata in hidden UI, logs, analytics, or error messages
- display permission-denied states without exposing resource details

# Motion Requirements

Use motion only when it improves comprehension:

- page transitions: subtle
- dialogs and drawers: short and restrained
- task completion: lightweight feedback
- loading states: skeletons or progress feedback
- avoid excessive parallax
- avoid animation on every card
- avoid motion that delays task completion
- prefer opacity and transform animations
- support `prefers-reduced-motion`
- provide a reduced or static experience when requested by the operating system
- never rely on animation alone to communicate status

# Accessibility Requirements

- semantic HTML
- logical heading order
- visible focus indicators
- keyboard navigation
- meaningful labels
- accessible form errors
- sufficient contrast
- icon buttons require accessible names
- responsive layout
- reduced-motion support
- no hover-only critical actions

# Before Coding

Read:

```text
docs/00_START_HERE.md
docs/01_PRODUCT_SCOPE.md
docs/13_AGENT_OWNERSHIP_MATRIX.md
docs/14_FRONTEND_DESIGN_SYSTEM.md
docs/15_FRONTEND_SECURITY_MOTION.md
docs/checklists/FRONTEND_CLAUDE.md
```

# Docker Ownership

Claude owns frontend Docker validation:

- Next.js Dockerfile
- `.dockerignore`
- standalone build configuration
- public environment-variable usage
- frontend container build
- reverse-proxy compatibility
- responsive UI verification inside containerized setup

Claude must not add backend services to Compose.

Read:

```text
docs/17_DOCKERIZATION.md
docs/checklists/DOCKERIZATION.md
```
