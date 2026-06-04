# MCP and Skills Setup

## Agent Roles

```text
Claude:
frontend only

Codex:
backend only
```

## Included MCP Templates

### Codex

```text
.codex/config.toml
```

Includes local Supabase MCP:

```text
http://localhost:54321/mcp
```

Use only local or staging Supabase data.

Do not connect MCP to production ERP data.

### Claude

```text
.mcp.json
```

Includes Playwright MCP for frontend QA.

## Optional MCP Later

```text
GitHub MCP:
add after private repository and PR workflow exist

Stitch MCP:
optional only if Claude needs direct Stitch integration
manual Stitch usage is also acceptable

Sentry MCP:
add after staging monitoring exists
```

## Included Skills

### Shared

```text
iems-security-review
iems-phase-gate
iems-api-contract-review
iems-release-check
```

### Codex backend-only

```text
iems-supabase-migration-validation
iems-backend-feature
iems-docker-deployment-check
iems-physical-archive-integrity
```

### Claude frontend-only

```text
iems-frontend-screen
iems-frontend-security-review
iems-accessibility-motion-review
iems-director-dashboard-design
```

## Official Supabase Skills

The custom skills in this repository are included directly.

Also install the official Supabase agent skills in the repository when beginning implementation:

```bash
npx skills add supabase/agent-skills --all
```

Review generated changes before committing.

## Security Rules

- Keep MCP scoped to local or staging systems.
- Do not connect agent MCP to production.
- Keep secrets outside committed configuration.
- Review each MCP server before installation.
- Use the smallest tool set needed.
