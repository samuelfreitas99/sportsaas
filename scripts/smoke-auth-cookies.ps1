param(
  [string] $Api = "http://localhost:8000/api/v1",
  [string] $Email,
  [string] $Pass
)

$ErrorActionPreference = "Stop"

Write-Host "== Smoke Auth (Cookies) =="
Write-Host "API: $Api"

# Usa sessão para manter cookies HttpOnly automaticamente
$session = New-Object Microsoft.PowerShell.Commands.WebRequestSession

Write-Host "1) Login..."
$loginBody = @{ email = $Email; password = $Pass } | ConvertTo-Json
$loginRes = Invoke-WebRequest -Uri "$Api/auth/login" -Method POST -Body $loginBody -ContentType "application/json" -WebSession $session
if ($loginRes.StatusCode -ne 200) { throw "Login falhou: $($loginRes.StatusCode)" }
Write-Host "   OK (cookies set)"

Write-Host "2) Me..."
$meRes = Invoke-WebRequest -Uri "$Api/auth/me" -Method GET -WebSession $session
if ($meRes.StatusCode -ne 200) { throw "Me falhou: $($meRes.StatusCode)" }
$meJson = $meRes.Content | ConvertFrom-Json
Write-Host ("   User: " + $meJson.email)

Write-Host "3) Refresh..."
$refreshRes = Invoke-WebRequest -Uri "$Api/auth/refresh" -Method POST -WebSession $session
if ($refreshRes.StatusCode -ne 200) { throw "Refresh falhou: $($refreshRes.StatusCode)" }
Write-Host "   OK (access_token atualizado)"

Write-Host "4) Logout..."
$logoutRes = Invoke-WebRequest -Uri "$Api/auth/logout" -Method POST -WebSession $session
if ($logoutRes.StatusCode -ne 200) { throw "Logout falhou: $($logoutRes.StatusCode)" }
Write-Host "   OK (cookies limpos)"

Write-Host "✅ Smoke cookies OK"
