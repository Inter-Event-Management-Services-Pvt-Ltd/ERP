param(
  [Parameter(Mandatory = $true)]
  [string]$BackupPath
)

$ErrorActionPreference = "Stop"

function Invoke-CheckedNative {
  param(
    [Parameter(Mandatory = $true)]
    [string]$FilePath,
    [Parameter(Mandatory = $true)]
    [string[]]$Arguments
  )

  & $FilePath @Arguments
  if ($LASTEXITCODE -ne 0) {
    throw "$FilePath $($Arguments -join ' ') failed with exit code $LASTEXITCODE"
  }
}

if (-not (Test-Path -LiteralPath $BackupPath -PathType Leaf)) {
  throw "Backup path not found: $BackupPath"
}

Invoke-CheckedNative "docker" @("exec", "supabase_db_iems-erp", "dropdb", "-U", "postgres", "--if-exists", "iems_restore_test")
Invoke-CheckedNative "docker" @("exec", "supabase_db_iems-erp", "createdb", "-U", "postgres", "iems_restore_test")
Invoke-CheckedNative "docker" @(
  "exec",
  "supabase_db_iems-erp",
  "psql",
  "-U",
  "postgres",
  "-d",
  "iems_restore_test",
  "-v",
  "ON_ERROR_STOP=1",
  "-c",
  "create schema if not exists extensions; create extension if not exists pgcrypto with schema extensions; create extension if not exists citext with schema extensions; create extension if not exists pg_trgm with schema extensions; drop schema if exists public cascade; create schema if not exists auth; create table if not exists auth.users(id uuid primary key); create or replace function auth.uid() returns uuid language sql stable as 'select null::uuid';"
)
Invoke-CheckedNative "docker" @("cp", $BackupPath, "supabase_db_iems-erp:/tmp/iems-restore-test.dump")
Invoke-CheckedNative "docker" @("exec", "supabase_db_iems-erp", "pg_restore", "-U", "postgres", "-d", "iems_restore_test", "--no-owner", "--no-privileges", "/tmp/iems-restore-test.dump")
Invoke-CheckedNative "docker" @("exec", "supabase_db_iems-erp", "psql", "-U", "postgres", "-d", "iems_restore_test", "-c", "select count(*) as employee_count from public.employees;")
Invoke-CheckedNative "docker" @("exec", "supabase_db_iems-erp", "rm", "-f", "/tmp/iems-restore-test.dump")

Write-Output "Restore test passed."
