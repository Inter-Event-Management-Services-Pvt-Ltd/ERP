$ErrorActionPreference = "Stop"

$rules = @(
  @{
    Name = "Supabase secret key"
    Pattern = "sb_secret_[A-Za-z0-9_-]{20,}"
    AllowedFragments = @(
      "sb_secret_test",
      "sb_secret_example",
      "sb_secret_placeholder"
    )
  },
  @{
    Name = "Assigned Supabase service-role key"
    Pattern = "\bSUPABASE_SERVICE_ROLE_KEY\s*=\s*['""]?(?!<|\$\{|your-|example|changeme|legacy-|test|local)[^\s'""]{12,}"
    AllowedFragments = @()
  },
  @{
    Name = "Assigned Supabase JWT secret"
    Pattern = "\bSUPABASE_JWT_SECRET\s*=\s*['""]?(?!<|\$\{|your-|example|changeme|legacy-|test|local)[^\s'""]{12,}"
    AllowedFragments = @()
  },
  @{
    Name = "Assigned Google client secret"
    Pattern = "\bGOOGLE_CLIENT_SECRET\s*=\s*['""]?(?!<|\$\{|your-|example|changeme|legacy-|test|local)[^\s'""]{12,}"
    AllowedFragments = @()
  },
  @{
    Name = "Database URL with embedded password"
    Pattern = "postgres(?:ql)?://[^:\s]+:(?!<|\$\{|postgres@|password@|example@|test@|local@)[^@\s]{8,}@"
    AllowedFragments = @()
  }
)

$trackedFiles = git ls-files --cached --others --exclude-standard
$findings = New-Object System.Collections.Generic.List[string]

foreach ($path in $trackedFiles) {
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
        $allowed = $false
        foreach ($fragment in $rule.AllowedFragments) {
          if ($line.Contains($fragment)) {
            $allowed = $true
            break
          }
        }
        if (-not $allowed) {
          $preview = $line -replace $rule.Pattern, "<redacted>"
          $findings.Add("${path}:$($index + 1): $($rule.Name): $preview")
        }
      }
    }
  }
}

if ($findings.Count -gt 0) {
  $findings | ForEach-Object { Write-Error $_ }
  exit 1
}

Write-Output "Secret scan passed."
