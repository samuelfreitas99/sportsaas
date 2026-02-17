# scripts/smoke-captains-teams.ps1
param(
  [string] $Api = "http://localhost:8000/api/v1",
  [string] $OrgId = "401eced3-4414-43da-a049-4d53bc19e1ac",
  [string] $Email,
  [string] $Pass
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

. "$PSScriptRoot/_lib.ps1"

Write-Step "1) Login..."
$ctx = Login -Api $Api -Email $Email -Pass $Pass
$H = $ctx.headers

Write-Step "2) Create SMOKE game..."
$game = Create-SmokeGame -Api $Api -Headers $H -OrgId $OrgId -TitlePrefix "SMOKE-CAPTAINS"
$gameId = $game.id
Write-Step "   GAME_ID: $gameId"

Write-Step "3) Mark myself GOING (so we have at least one GOING member)..."
$null = Invoke-Api -Method "PUT" -Url "$Api/orgs/$OrgId/games/$gameId/attendance" -Headers $H -Body @{ status="GOING" }

# helper: pega um org_member_id GOING do game detail
function Get-GoingMemberId {
  param([object] $detail)

  $id = ($detail.attendance_list |
    Where-Object { $_.status -eq "GOING" -and $_.org_member_id } |
    Select-Object -First 1).org_member_id

  return $id
}

Write-Step "4) Try set captains RANDOM..."
try {
  $cap = Invoke-Api -Method "PUT" -Url "$Api/orgs/$OrgId/games/$gameId/captains" -Headers $H -Body @{
    mode = "RANDOM"
    captain_a = $null
    captain_b = $null
  }
  Write-Step "   Captains RANDOM ok"
} catch {
  Write-Step "   RANDOM failed -> fallback to MANUAL (captain_a = first GOING member, captain_b = null)"

  $detail = Invoke-Api -Method "GET" -Url "$Api/orgs/$OrgId/games/$gameId" -Headers $H
  $myMemberId = Get-GoingMemberId -detail $detail

  if (-not $myMemberId) {
    throw "Não achei nenhum org_member_id com status GOING no game detail. Confirme se o PUT attendance GOING ocorreu."
  }

  $null = Invoke-Api -Method "PUT" -Url "$Api/orgs/$OrgId/games/$gameId/captains" -Headers $H -Body @{
    mode = "MANUAL"
    captain_a = @{ type="MEMBER"; id=$myMemberId }
    captain_b = $null
  }
  Write-Step "   Captains MANUAL ok"
}

Write-Step "5) Read game detail..."
$detail = Invoke-Api -Method "GET" -Url "$Api/orgs/$OrgId/games/$gameId" -Headers $H
$myMemberId = Get-GoingMemberId -detail $detail

if (-not $myMemberId) {
  throw "Não achei nenhum org_member_id GOING no game detail (inesperado)."
}

Write-Step "6) Assign that GOING member to Team A..."
$null = Invoke-Api -Method "PUT" -Url "$Api/orgs/$OrgId/games/$gameId/teams" -Headers $H -Body @{
  target = @{ type="MEMBER"; id=$myMemberId }
  team = "A"
}

Write-Step "7) Get teams..."
$teams = Invoke-Api -Method "GET" -Url "$Api/orgs/$OrgId/games/$gameId/teams" -Headers $H
Write-Step ("   Team A members: " + $teams.team_a.members.Count)
Write-Step ("   Team B members: " + $teams.team_b.members.Count)

Write-Step "OK ✅ captains/teams"
