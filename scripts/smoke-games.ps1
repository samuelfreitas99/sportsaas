# scripts/smoke-games.ps1
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
Write-Step "2) List games..."
$games = Invoke-Api -Method "GET" -Url "$Api/orgs/$OrgId/games" -Headers $H
Write-Step "   Games count: $($games.Count)"

Write-Step "3) Create SMOKE game (ADMIN/OWNER required)..."
$game = Create-SmokeGame -Api $Api -Headers $H -OrgId $OrgId -TitlePrefix "SMOKE-GAME"
Write-Step "   Created game id: $($game.id)"

Write-Step "4) Get game detail..."
$detail = Invoke-Api -Method "GET" -Url "$Api/orgs/$OrgId/games/$($game.id)" -Headers $H
Write-Step "   Detail OK (has title: $($detail.title))"

Write-Step "OK ✅ games"
