param(
  [string] $Api = "http://localhost:8000/api/v1",
  [string] $OrgId,
  [string] $Email,
  [string] $Pass
)

$ErrorActionPreference = "Stop"
. "$PSScriptRoot/_lib.ps1"

Write-Step "1) Login..."
$ctx = Login -Api $Api -Email $Email -Pass $Pass
$H = $ctx.headers

Write-Step "2) Finance summary..."
$summary = Invoke-Api -Method "GET" -Url "$Api/orgs/$OrgId/finance/summary" -Headers $H

Write-Step "3) Finance recent..."
$recent = Invoke-Api -Method "GET" -Url "$Api/orgs/$OrgId/finance/recent?limit=10" -Headers $H

Write-Step ("   income=" + $summary.income_total + " expense=" + $summary.expense_total + " balance=" + $summary.balance)
Write-Step ("   recent.ledger=" + ($recent.ledger.Count) + " recent.charges=" + ($recent.charges.Count))

Write-Step "OK ✅ finance dashboard"
