# scripts/smoke-draft.ps1
param(
  [string] $Api = "http://localhost:8000/api/v1",
  [string] $OrgId = "401eced3-4414-43da-a049-4d53bc19e1ac",
  [string] $Email,
  [string] $Pass,
  [int] $GuestCount = 8
)

. "$PSScriptRoot/_lib.ps1"

Write-Step "1) Login..."
$ctx = Login -Api $Api -Email $Email -Pass $Pass
$H = $ctx.headers
Write-Step "   Token OK"

Write-Step "2) /users/me ..."
Write-Step "   User: $($ctx.me.email) / id=$($ctx.me.id)"

Write-Step "3) Using ORG_ID: $OrgId"

Write-Step "4) Create SMOKE game..."
$game = Create-SmokeGame -Api $Api -Headers $H -OrgId $OrgId -TitlePrefix "SMOKE-DRAFT"
$gameId = $game.id
Write-Step "   NEW GAME_ID: $gameId"

Write-Step "5) Create game guests (pool do draft)..."
$stamp = (Get-Date).ToString("yyyyMMdd-HHmmss")
$created = @()
for ($i=1; $i -le $GuestCount; $i++) {
  $name = "SmokeGuest-$stamp-$i"
  $gg = Invoke-Api -Method "POST" -Url "$Api/orgs/$OrgId/games/$gameId/guests" -Headers $H -Body @{
    name = $name
    phone = $null
  }
  $created += $gg
}
Write-Step "   Guests created: $($created.Count)"

Write-Step "6) Start draft..."
$draft = Invoke-Api -Method "POST" -Url "$Api/orgs/$OrgId/games/$gameId/draft/start" -Headers $H
Write-Step "   Draft status: $($draft.status) / turn: $($draft.current_turn_team_side)"

function NextTeamSideABBA([int]$idx) {
  # idx começa em 0
  # ABBA repeats: A, B, B, A
  $mod = $idx % 4
  if ($mod -eq 0) { return "A" }
  if ($mod -eq 1) { return "B" }
  if ($mod -eq 2) { return "B" }
  return "A"
}

Write-Step "7) Auto-pick all guests (ABBA)..."
for ($i=0; $i -lt $GuestCount; $i++) {
  $side = NextTeamSideABBA -idx $i
  Write-Step ("   Pick {0}/{1} - team {2}" -f ($i+1), $GuestCount, $side)
  $remaining = Invoke-Api -Method "GET" -Url "$Api/orgs/$OrgId/games/$gameId/draft" -Headers $H
  $pickTarget = $remaining.remaining_pool[0]
  if (-not $pickTarget) { throw "remaining_pool vazio antes de completar picks." }

  # Para o smoke, estamos criando somente convidados do jogo.
  $body = @{
    team_side = $side
    game_guest_id = $pickTarget.game_guest_id
    org_member_id = $null
  }

  $null = Invoke-Api -Method "POST" -Url "$Api/orgs/$OrgId/games/$gameId/draft/pick" -Headers $H -Body $body
}

Write-Step "8) Finish draft..."
$finish = Invoke-Api -Method "POST" -Url "$Api/orgs/$OrgId/games/$gameId/draft/finish" -Headers $H
Write-Step "   Draft finished: $($finish.status)"

Write-Step "9) Get final draft..."
$final = Invoke-Api -Method "GET" -Url "$Api/orgs/$OrgId/games/$gameId/draft" -Headers $H

Write-Host "=== RESULT ==="
Write-Host "Game: $gameId"
Write-Host "Status: $($final.status)"
Write-Host "Picks: $($final.picks.Count)"
Write-Host "Team A guests: $($final.teams.team_a.guests.Count)"
Write-Host "Team B guests: $($final.teams.team_b.guests.Count)"
Write-Host ""
Write-Host "Team A:"
$final.teams.team_a.guests | ForEach-Object { Write-Host (" - " + $_.name) }
Write-Host ""
Write-Host "Team B:"
$final.teams.team_b.guests | ForEach-Object { Write-Host (" - " + $_.name) }

Write-Step "OK ✅ Smoke draft concluído."
