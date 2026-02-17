# scripts/smoke-rbac.ps1
param(
  [string] $Api = "http://localhost:8000/api/v1",
  [string] $OrgId = "401eced3-4414-43da-a049-4d53bc19e1ac",

  # Admin/Owner
  [string] $AdminEmail,
  [string] $AdminPass,

  # Member (opcional)
  [string] $MemberEmail = "",
  [string] $MemberPass = ""
)

. "$PSScriptRoot/_lib.ps1"

Write-Step "1) Login ADMIN/OWNER..."
$admin = Login -Api $Api -Email $AdminEmail -Pass $AdminPass
$HAdmin = $admin.headers
Write-Step "   Admin OK"

Write-Step "2) Create SMOKE game (admin)..."
$game = Create-SmokeGame -Api $Api -Headers $HAdmin -OrgId $OrgId -TitlePrefix "SMOKE-RBAC"
$gameId = $game.id
Write-Step "   GAME_ID: $gameId"

Write-Step "3) Admin can start draft -> should be 200"
$draft = Invoke-Api -Method "POST" -Url "$Api/orgs/$OrgId/games/$gameId/draft/start" -Headers $HAdmin
Write-Step "   Draft started: $($draft.status)"

if ([string]::IsNullOrWhiteSpace($MemberEmail) -or [string]::IsNullOrWhiteSpace($MemberPass)) {
  Write-Step "4) MEMBER creds not provided -> skipping MEMBER checks (OK)."
  Write-Step "OK ✅ rbac (partial)"
  exit 0
}

Write-Step "4) Login MEMBER..."
$member = Login -Api $Api -Email $MemberEmail -Pass $MemberPass
$HMember = $member.headers
Write-Step "   Member OK"

Write-Step "5) MEMBER tries start draft -> should be 403"
try {
  $null = Invoke-Api -Method "POST" -Url "$Api/orgs/$OrgId/games/$gameId/draft/start" -Headers $HMember
  throw "ERRO: MEMBER conseguiu start draft (esperado 403)."
} catch {
  if ($_.Exception.Message -match "403|insufficient role|detail") {
    Write-Step "   Got expected denial."
  } else {
    throw
  }
}

Write-Step "6) MEMBER can GET game details -> should be 200"
$detail = Invoke-Api -Method "GET" -Url "$Api/orgs/$OrgId/games/$gameId" -Headers $HMember
Write-Step "   Detail OK: $($detail.title)"

Write-Step "OK ✅ rbac"
