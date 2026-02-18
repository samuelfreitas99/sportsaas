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

Write-Step "2) Ensure billing settings = HYBRID / MONTHLY ..."
$settings = @{
  billing_mode      = "HYBRID"
  cycle             = "MONTHLY"
  cycle_weeks       = $null
  anchor_date       = (Get-Date).ToString("yyyy-MM-dd")
  due_day           = 1
  membership_amount = 100
  session_amount    = 15
}
$null = Invoke-Api -Method "PUT" -Url "$Api/orgs/$OrgId/billing-settings" -Headers $H -Body $settings

Write-Step "3) Create SMOKE game..."
$game = Create-SmokeGame -Api $Api -Headers $H -OrgId $OrgId -TitlePrefix "SMOKE-BILLING"
$gameId = $game.id
Write-Step "   GAME_ID: $gameId"

Write-Step "4) Mark myself GOING..."
$null = Invoke-Api -Method "PUT" -Url "$Api/orgs/$OrgId/games/$gameId/attendance" -Headers $H -Body @{ status="GOING" }

Write-Step "5) Generate charges..."
$null = Invoke-Api -Method "POST" -Url "$Api/orgs/$OrgId/charges/generate" -Headers $H -Body @{ force=$false }

Write-Step "6) List charges and find PER_SESSION for this game..."
$charges = Invoke-Api -Method "GET" -Url "$Api/orgs/$OrgId/charges" -Headers $H
$cycleKey = "GAME:$gameId"
$sessionCharge = $charges | Where-Object { $_.type -eq "PER_SESSION" -and $_.cycle_key -eq $cycleKey } | Select-Object -First 1

if (-not $sessionCharge) {
  throw "Não achei charge PER_SESSION com cycle_key=$cycleKey. Verifique a lógica do generate."
}

Write-Step ("   Found charge: " + $sessionCharge.id + " amount=" + $sessionCharge.amount + " status=" + $sessionCharge.status)

Write-Step "7) Mark charge as PAID -> should create ledger entry..."
$paid = Invoke-Api -Method "PATCH" -Url "$Api/orgs/$OrgId/charges/$($sessionCharge.id)" -Headers $H -Body @{ status="PAID" }

if (-not $paid.ledger_entry_id) {
  throw "Charge foi marcado como PAID mas não retornou ledger_entry_id."
}

Write-Step ("   ledger_entry_id=" + $paid.ledger_entry_id)
Write-Step "OK ✅ billing per-session"
