# scripts/smoke-billing-membership.ps1
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

Write-Step "3) Find my org_member and set member_type=MONTHLY..."
$members = Invoke-Api -Method "GET" -Url "$Api/orgs/$OrgId/members" -Headers $H
$meId = $ctx.me.id

# tenta achar seu membro (aqui normalmente vem user_id)
$myMember = $members | Where-Object { $_.user_id -eq $meId } | Select-Object -First 1
if (-not $myMember) {
  throw "Não consegui achar seu OrgMember em /orgs/$OrgId/members. Veja se você está nessa org."
}

$memberId = $myMember.id
$originalType = $myMember.member_type

$null = Invoke-Api -Method "PATCH" -Url "$Api/orgs/$OrgId/members/$memberId" -Headers $H -Body @{
  member_type = "MONTHLY"
  is_active   = $true
}

Write-Step "4) Generate charges..."
$gen = Invoke-Api -Method "POST" -Url "$Api/orgs/$OrgId/charges/generate" -Headers $H -Body @{ force=$false }
$cycleKey = $gen.cycle_key
Write-Step ("   cycle_key=" + $cycleKey)

Write-Step "5) List charges and find MEMBERSHIP for me (cycle_key)..."
$charges = Invoke-Api -Method "GET" -Url "$Api/orgs/$OrgId/charges" -Headers $H

$membership = $charges |
  Where-Object { $_.type -eq "MEMBERSHIP" -and $_.cycle_key -eq $cycleKey -and $_.org_member_id -eq $memberId } |
  Select-Object -First 1

if (-not $membership) {
  throw "Não achei charge MEMBERSHIP para seu member_id=$memberId e cycle_key=$cycleKey. Verifique generate."
}

Write-Step ("   Found charge: " + $membership.id + " amount=" + $membership.amount + " status=" + $membership.status)

Write-Step "6) Revert my member_type back (cleanup)..."
$null = Invoke-Api -Method "PATCH" -Url "$Api/orgs/$OrgId/members/$memberId" -Headers $H -Body @{
  member_type = $originalType
  is_active   = $true
}

Write-Step "OK ✅ billing membership"
