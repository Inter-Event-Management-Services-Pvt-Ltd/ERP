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

$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$backupDir = "tmp\backups"
New-Item -ItemType Directory -Force -Path $backupDir | Out-Null

$backupPath = Join-Path $backupDir "iems-local-$timestamp.dump"

Invoke-CheckedNative "docker" @(
  "exec",
  "supabase_db_iems-erp",
  "pg_dump",
  "-U",
  "postgres",
  "-d",
  "postgres",
  "-Fc",
  "--schema=public",
  "--schema=app_private",
  "--no-owner",
  "--no-privileges",
  "-f",
  "/tmp/iems-local.dump"
)
Invoke-CheckedNative "docker" @("cp", "supabase_db_iems-erp:/tmp/iems-local.dump", $backupPath)
Invoke-CheckedNative "docker" @("exec", "supabase_db_iems-erp", "rm", "-f", "/tmp/iems-local.dump")

Write-Output $backupPath
