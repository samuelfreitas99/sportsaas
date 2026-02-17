# scripts/smoke-auth.ps1
param(
  [string] $Api = "http://localhost:8000/api/v1",
  [string] $Email,
  [string] $Pass
)

. "$PSScriptRoot/_lib.ps1"

Write-Step "1) Login..."
$ctx = Login -Api $Api -Email $Email -Pass $Pass
Write-Step "   Token OK"
Write-Step "2) /users/me ..."
$ctx.me | ConvertTo-Json -Depth 10
Write-Step "OK ✅ auth"
