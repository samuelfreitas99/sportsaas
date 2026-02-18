param(
  [string] $Api = "http://localhost:8000/api/v1",
  [string] $InternalKey = "troque_isto"
)

$ErrorActionPreference = "Stop"
. "$PSScriptRoot/_lib.ps1"

Write-Step "1) Call internal billing run..."
$r = Invoke-Api -Method "POST" -Url "$Api/internal/billing/run" -Headers @{ "X-Internal-Key" = $InternalKey } -Body @{}
Write-Step ("   orgs=" + $r.orgs)
Write-Step "OK ✅ internal billing run"
