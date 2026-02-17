# scripts/smoke-all.ps1
param(
  [string] $Api = "http://localhost:8000/api/v1",
  [string] $OrgId = "401eced3-4414-43da-a049-4d53bc19e1ac",
  [string] $Email,
  [string] $Pass,

  # opcional p/ RBAC
  [string] $MemberEmail = "",
  [string] $MemberPass = ""
)

$ErrorActionPreference = "Stop"

Write-Host "=== SMOKE ALL (Phase 2B.12) ==="
Write-Host "API: $Api"
Write-Host "ORG: $OrgId"
Write-Host ""

powershell -ExecutionPolicy Bypass -File "$PSScriptRoot/smoke-auth.ps1" -Api $Api -Email $Email -Pass $Pass
powershell -ExecutionPolicy Bypass -File "$PSScriptRoot/smoke-games.ps1" -Api $Api -OrgId $OrgId -Email $Email -Pass $Pass
powershell -ExecutionPolicy Bypass -File "$PSScriptRoot/smoke-attendance.ps1" -Api $Api -OrgId $OrgId -Email $Email -Pass $Pass
powershell -ExecutionPolicy Bypass -File "$PSScriptRoot/smoke-guests.ps1" -Api $Api -OrgId $OrgId -Email $Email -Pass $Pass
powershell -ExecutionPolicy Bypass -File "$PSScriptRoot/smoke-captains-teams.ps1" -Api $Api -OrgId $OrgId -Email $Email -Pass $Pass
powershell -ExecutionPolicy Bypass -File "$PSScriptRoot/smoke-draft.ps1" -Api $Api -OrgId $OrgId -Email $Email -Pass $Pass

# RBAC opcional: só roda se MemberEmail/MemberPass vierem preenchidos
if (-not [string]::IsNullOrWhiteSpace($MemberEmail) -and -not [string]::IsNullOrWhiteSpace($MemberPass)) {
  powershell -ExecutionPolicy Bypass -File "$PSScriptRoot/smoke-rbac.ps1" `
    -Api $Api -OrgId $OrgId `
    -AdminEmail $Email -AdminPass $Pass `
    -MemberEmail $MemberEmail -MemberPass $MemberPass
} else {
  Write-Host "RBAC: pulado (MemberEmail/MemberPass não informados)."
}


Write-Host ""
Write-Host "ALL OK ✅"
