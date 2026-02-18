# scripts/smoke-finance-summary.ps1
param(
  [string] $Api = "http://localhost:8000/api/v1",
  [string] $OrgId = "401eced3-4414-43da-a049-4d53bc19e1ac",
  [string] $Email,
  [string] $Pass
)

$ErrorActionPreference = "Stop"
. "$PSScriptRoot/_lib.ps1"

Write-Step "1) Login..."
$ctx = Login -Api $Api -Email $Email -Pass $Pass
$H = $ctx.headers

Write-Step "2) GET finance summary..."
$sum = Invoke-Api -Method "GET" -Url "$Api/orgs/$OrgId/finance/summary" -Headers $H
$sum | ConvertTo-Json -Depth 10

Write-Step "3) GET finance recent..."
$recent = Invoke-Api -Method "GET" -Url "$Api/orgs/$OrgId/finance/recent?limit=5" -Headers $H
Write-Step ("   ledger items: " + $recent.ledger.Count)
Write-Step ("   charges items: " + $recent.charges.Count)

Write-Step "OK ✅ finance summary"
