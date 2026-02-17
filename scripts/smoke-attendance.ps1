# scripts/smoke-attendance.ps1
param(
  [string] $Api = "http://localhost:8000/api/v1",
  [string] $OrgId = "401eced3-4414-43da-a049-4d53bc19e1ac",
  [string] $Email,
  [string] $Pass
)

. "$PSScriptRoot/_lib.ps1"

Write-Step "1) Login..."
$ctx = Login -Api $Api -Email $Email -Pass $Pass
$H = $ctx.headers

Write-Step "2) Create SMOKE game..."
$game = Create-SmokeGame -Api $Api -Headers $H -OrgId $OrgId -TitlePrefix "SMOKE-ATT"
$gameId = $game.id
Write-Step "   GAME_ID: $gameId"

Write-Step "3) GET attendance (initial)..."
$att1 = Invoke-Api -Method "GET" -Url "$Api/orgs/$OrgId/games/$gameId/attendance" -Headers $H
Write-Step ("   Counts: " + ($att1.counts | ConvertTo-Json -Depth 5))

Write-Step "4) PUT attendance GOING..."
$att2 = Invoke-Api -Method "PUT" -Url "$Api/orgs/$OrgId/games/$gameId/attendance" -Headers $H -Body @{ status="GOING" }
Write-Step ("   Now counts: " + ($att2.counts | ConvertTo-Json -Depth 5))

Write-Step "OK ✅ attendance"
