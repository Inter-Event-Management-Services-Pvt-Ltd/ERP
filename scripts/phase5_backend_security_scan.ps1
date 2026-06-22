$ErrorActionPreference = "Stop"

$rules = @(
  @{
    Name = "Shell command execution"
    Pattern = "\bsubprocess\b|\bos\.system\s*\(|\bos\.popen\s*\(|\bcommands\.getoutput\s*\(|\bshell\s*=\s*True\b"
    Allowed = @()
  },
  @{
    Name = "Dynamic code execution"
    Pattern = "(?<!\.)\b(eval|exec|compile)\s*\("
    Allowed = @()
  },
  @{
    Name = "Unsafe deserialization"
    Pattern = "\bpickle\.(load|loads)\s*\(|\bmarshal\.(load|loads)\s*\(|\byaml\.load\s*\("
    Allowed = @()
  },
  @{
    Name = "Raw SQL string execution"
    Pattern = "\bsqlalchemy\.text\s*\(|\btext\s*\(\s*f['""]|\bexecute\s*\(\s*f['""]|\braw\s*\(\s*f['""]"
    Allowed = @()
  },
  @{
    Name = "Direct outbound HTTP outside approved helpers"
    Pattern = "\b(?:httpx|requests)\.(?:get|post|put|patch|delete|request)\s*\(|\burllib\.request\.urlopen\s*\(|\bclient\.request\s*\("
    Allowed = @(
      @{
        Path = "apps/api/app/core/supabase_http.py"
        Fragment = "client.request("
        Reason = "central Supabase REST helper"
      },
      @{
        Path = "apps/api/app/workers/archive_exports.py"
        Fragment = "client.request("
        Reason = "archive worker Supabase REST/Storage helper using configured Supabase URL"
      }
    )
  }
)

function Test-AllowedFinding {
  param(
    [string]$Path,
    [string]$Line,
    [object[]]$Allowed
  )

  foreach ($allow in $Allowed) {
    if ($Path -eq $allow["Path"] -and $Line.Contains($allow["Fragment"])) {
      return $true
    }
  }
  return $false
}

$trackedFiles = git ls-files apps/api/app
$pythonFiles = $trackedFiles | Where-Object { $_ -like "*.py" }
$findings = New-Object System.Collections.Generic.List[string]

foreach ($path in $pythonFiles) {
  if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
    continue
  }

  try {
    $lines = Get-Content -LiteralPath $path -ErrorAction Stop
  } catch {
    continue
  }

  for ($index = 0; $index -lt $lines.Count; $index++) {
    $line = [string]$lines[$index]
    foreach ($rule in $rules) {
      if ($line -match $rule.Pattern) {
        if (-not (Test-AllowedFinding -Path ($path -replace "\\", "/") -Line $line -Allowed $rule.Allowed)) {
          $findings.Add("${path}:$($index + 1): $($rule.Name): $($line.Trim())")
        }
      }
    }
  }
}

if ($findings.Count -gt 0) {
  $findings | ForEach-Object { Write-Error $_ }
  exit 1
}

Write-Output "Backend security pattern scan passed."
