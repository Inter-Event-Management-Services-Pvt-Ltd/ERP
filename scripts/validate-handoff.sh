#!/usr/bin/env bash
set -euo pipefail

required=(
  "AGENTS.md"
  "CLAUDE.md"
  "CODEX.md"
  "SECURITY.md"
  "docs/00_START_HERE.md"
  "docs/04_SECURITY_MODEL.md"
  "docs/06_DEFINITION_OF_DONE.md"
  "docs/checklists/SECURITY_GLOBAL.md"
  "docs/checklists/SECURITY_RELEASE_GATE.md"
  "supabase/config.toml"
  ".codex/config.toml"
  ".mcp.json"
  "docs/18_MCP_AND_SKILLS_SETUP.md"
)

for path in "${required[@]}"; do
  if [[ ! -f "$path" ]]; then
    echo "Missing required file: $path"
    exit 1
  fi
done

if [[ ! -d "supabase/migrations" ]]; then
  echo "Missing supabase/migrations"
  exit 1
fi

migration_count="$(find supabase/migrations -type f -name '*.sql' | wc -l | tr -d ' ')"
if [[ "$migration_count" -lt 1 ]]; then
  echo "No SQL migrations found"
  exit 1
fi

echo "Handoff package structure is valid."
echo "SQL migrations: $migration_count"
