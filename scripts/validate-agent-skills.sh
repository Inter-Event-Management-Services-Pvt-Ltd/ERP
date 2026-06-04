#!/usr/bin/env bash
set -euo pipefail

required=(
  ".codex/config.toml"
  ".mcp.json"
  ".agents/skills/iems-security-review/SKILL.md"
  ".agents/skills/iems-phase-gate/SKILL.md"
  ".agents/skills/iems-api-contract-review/SKILL.md"
  ".agents/skills/iems-release-check/SKILL.md"
  ".agents/skills/iems-supabase-migration-validation/SKILL.md"
  ".agents/skills/iems-backend-feature/SKILL.md"
  ".agents/skills/iems-docker-deployment-check/SKILL.md"
  ".agents/skills/iems-physical-archive-integrity/SKILL.md"
  ".claude/skills/iems-security-review/SKILL.md"
  ".claude/skills/iems-phase-gate/SKILL.md"
  ".claude/skills/iems-api-contract-review/SKILL.md"
  ".claude/skills/iems-release-check/SKILL.md"
  ".claude/skills/iems-frontend-screen/SKILL.md"
  ".claude/skills/iems-frontend-security-review/SKILL.md"
  ".claude/skills/iems-accessibility-motion-review/SKILL.md"
  ".claude/skills/iems-director-dashboard-design/SKILL.md"
)

for path in "${required[@]}"; do
  if [[ ! -f "$path" ]]; then
    echo "Missing agent skill or MCP file: $path"
    exit 1
  fi
done

echo "Agent skills and MCP templates are present."
