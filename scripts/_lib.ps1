# scripts/_lib.ps1
# Helpers compartilhados para smoke tests (PowerShell 5+ / 7+)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Step($msg) {
  Write-Host $msg
}

function Ensure-Json($obj) {
  return ($obj | ConvertTo-Json -Depth 50)
}

function Invoke-Api {
  param(
    [Parameter(Mandatory=$true)][ValidateSet("GET","POST","PUT","PATCH","DELETE")] [string] $Method,
    [Parameter(Mandatory=$true)][string] $Url,
    [hashtable] $Headers = @{},
    $Body = $null,
    [string] $ContentType = "application/json"
  )

  try {
    if ($null -ne $Body) {
      if ($ContentType -eq "application/json" -and ($Body -isnot [string])) {
        $Body = ($Body | ConvertTo-Json -Depth 50)
      }
      return Invoke-RestMethod -Method $Method -Uri $Url -Headers $Headers -ContentType $ContentType -Body $Body
    } else {
      return Invoke-RestMethod -Method $Method -Uri $Url -Headers $Headers
    }
  } catch {
    # Tenta extrair body do erro HTTP (quando existir)
    $msg = $_.Exception.Message
    try {
      $resp = $_.Exception.Response
      if ($resp -and $resp.GetResponseStream()) {
        $reader = New-Object System.IO.StreamReader($resp.GetResponseStream())
        $bodyText = $reader.ReadToEnd()
        if ($bodyText) { $msg = "$msg`n$bodyText" }
      }
    } catch {}
    throw $msg
  }
}

function Login {
  param(
    [Parameter(Mandatory=$true)][string] $Api,
    [Parameter(Mandatory=$true)][string] $Email,
    [Parameter(Mandatory=$true)][string] $Pass
  )
  # OAuth2PasswordRequestForm (x-www-form-urlencoded)
  $login = Invoke-Api -Method "POST" -Url "$Api/auth/login" -Headers @{} `
    -ContentType "application/x-www-form-urlencoded" `
    -Body "username=$Email&password=$Pass"

  if (-not $login.access_token) {
    throw "Login não retornou access_token."
  }

  $headers = @{ Authorization = "Bearer $($login.access_token)" }
  $me = Invoke-Api -Method "GET" -Url "$Api/users/me" -Headers $headers
  return @{
    token = $login.access_token
    headers = $headers
    me = $me
    raw = $login
  }
}

function Get-FirstGameId {
  param(
    [Parameter(Mandatory=$true)][string] $Api,
    [Parameter(Mandatory=$true)][hashtable] $Headers,
    [Parameter(Mandatory=$true)][string] $OrgId
  )
  $games = Invoke-Api -Method "GET" -Url "$Api/orgs/$OrgId/games" -Headers $Headers
  if (-not $games -or $games.Count -eq 0) { return $null }
  return $games[0].id
}

function Create-SmokeGame {
  param(
    [Parameter(Mandatory=$true)][string] $Api,
    [Parameter(Mandatory=$true)][hashtable] $Headers,
    [Parameter(Mandatory=$true)][string] $OrgId,
    [string] $TitlePrefix = "SMOKE"
  )

  $now = Get-Date
  $stamp = $now.ToString("yyyyMMdd-HHmmss")
  # UTC ISO
  $startAt = (Get-Date).ToUniversalTime().AddHours(2).ToString("yyyy-MM-ddTHH:mm:ssZ")

  $body = @{
    title = "$TitlePrefix-$stamp"
    sport = "Futebol"
    location = "Quadra Smoke"
    start_at = $startAt
    notes = "Smoke test"
  }

  $game = Invoke-Api -Method "POST" -Url "$Api/orgs/$OrgId/games" -Headers $Headers -Body $body
  return $game
}
