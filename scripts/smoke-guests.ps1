# scripts/smoke-guests.ps1
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
$game = Create-SmokeGame -Api $Api -Headers $H -OrgId $OrgId -TitlePrefix "SMOKE-GUEST"
$gameId = $game.id
Write-Step "   GAME_ID: $gameId"

$stamp = (Get-Date).ToString("yyyyMMdd-HHmmss")
$orgGuestName = "SmokeOrgGuest-$stamp"

Write-Step "3) Create OrgGuest (ADMIN/OWNER required by your RBAC)..."
$orgGuest = Invoke-Api -Method "POST" -Url "$Api/orgs/$OrgId/guests" -Headers $H -Body @{
  name  = $orgGuestName
  phone = $null
}
Write-Step "   OrgGuest id: $($orgGuest.id)"


Write-Step "4) Add GameGuest from org_guest..."
$gg1 = Invoke-Api -Method "POST" -Url "$Api/orgs/$OrgId/games/$gameId/guests" -Headers $H -Body @{
  org_guest_id = $orgGuest.id
}
Write-Step "   GameGuest id: $($gg1.id)"

Write-Step "5) Add GameGuest avulso..."
$gg2 = Invoke-Api -Method "POST" -Url "$Api/orgs/$OrgId/games/$gameId/guests" -Headers $H -Body @{
  name = "Avulso-$stamp"
  phone = $null
}
Write-Step "   GameGuest id: $($gg2.id)"

Write-Step "6) List game guests..."
$list = Invoke-Api -Method "GET" -Url "$Api/orgs/$OrgId/games/$gameId/guests" -Headers $H
Write-Step "   Game guests count: $($list.Count)"

Write-Step "OK ✅ guests"
