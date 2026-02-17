# Sport SaaS

Plataforma SaaS para gestão esportiva:
- Grupos organizam jogos, presença e financeiro
- (Em breve) Centros esportivos gerenciam quadras e reservas estilo “Airbnb”

## Stack
- Backend: FastAPI (Python 3.11) + SQLAlchemy 2.0 + Alembic
- Database: PostgreSQL 15
- Frontend: Next.js 14 + TypeScript + Tailwind
- Infra: Docker Compose

## Quick start

### 1) Subir tudo
```bash
docker compose up -d --build
2) Rodar migrations
docker compose exec api alembic upgrade head
3) Frontend
Via container (se seu compose já tem web)

Acesse http://localhost:3000

Via local (opcional):

cd apps/web
npm install
npm run dev
Backend: http://localhost:8000
Swagger: http://localhost:8000/docs

Funcionalidades atuais (Fase 1 + 2A)
Core
Auth JWT: register/login/me

Organizações (orgs)

Membros (RBAC + CRUD de membros)

Jogos (games)

Presença (attendance)

Ledger (entradas/saídas) por org

Billing (Phase 2A)
Configuração por org e cobranças (charges), com integração:

Ao marcar um charge como PAID -> cria LedgerEntry do tipo INCOME.

Páginas:

/dashboard/billing

/dashboard/charges

Endpoints:

Billing settings:

GET /api/v1/orgs/{org_id}/billing-settings

PUT /api/v1/orgs/{org_id}/billing-settings

Charges:

POST /api/v1/orgs/{org_id}/charges/generate

GET /api/v1/orgs/{org_id}/charges?cycle_key=&member_id=&status=

PATCH /api/v1/orgs/{org_id}/charges/{charge_id} (status: PAID | VOID)

Smoke tests (PowerShell)
$login = Invoke-RestMethod -Method Post "http://localhost:8000/api/v1/auth/login" `
  -ContentType "application/x-www-form-urlencoded" `
  -Body "username=EMAIL&password=PASSWORD"
$headers = @{ Authorization = "Bearer $($login.access_token)" }

$orgId = "YOUR_ORG_UUID"

Invoke-RestMethod -Method Get "http://localhost:8000/api/v1/orgs/$orgId/billing-settings" -Headers $headers

$settings = @{
  billing_mode = "HYBRID"
  cycle = "MONTHLY"
  cycle_weeks = $null
  anchor_date = "2026-02-17"
  due_day = 1
  membership_amount = 100
  session_amount = 15
}
Invoke-RestMethod -Method Put "http://localhost:8000/api/v1/orgs/$orgId/billing-settings" -Headers $headers `
  -ContentType "application/json" -Body ($settings | ConvertTo-Json)

Invoke-RestMethod -Method Post "http://localhost:8000/api/v1/orgs/$orgId/charges/generate" -Headers $headers `
  -ContentType "application/json" -Body (@{ force=$false } | ConvertTo-Json)

$charges = Invoke-RestMethod -Method Get "http://localhost:8000/api/v1/orgs/$orgId/charges" -Headers $headers
$chargeId = $charges[0].id

Invoke-RestMethod -Method Patch "http://localhost:8000/api/v1/orgs/$orgId/charges/$chargeId" -Headers $headers `
  -ContentType "application/json" -Body (@{ status="PAID" } | ConvertTo-Json)

Member Profile Expansion (Phase 2B.7)
Páginas:

/dashboard/profile

Endpoints:

GET /api/v1/users/me

PUT /api/v1/users/me

PATCH /api/v1/orgs/{org_id}/members/{member_id} (nickname | member_type | is_active)

Migration:

c2b7f3a9d1e4_phase_2b7_member_profile_expansion.py

Smoke tests (PowerShell)
$me = Invoke-RestMethod -Method Get "http://localhost:8000/api/v1/users/me" -Headers $headers

$meUpdate = @{
  full_name = "New Name"
  avatar_url = "https://example.com/avatar.png"
  phone = "+55 11 99999-9999"
}
Invoke-RestMethod -Method Put "http://localhost:8000/api/v1/users/me" -Headers $headers `
  -ContentType "application/json" -Body ($meUpdate | ConvertTo-Json)

$members = Invoke-RestMethod -Method Get "http://localhost:8000/api/v1/orgs/$orgId/members" -Headers $headers
$memberId = $members[0].id
$memberUpdate = @{
  nickname = "Capitão"
  member_type = "GUEST"
  is_active = $true
}
Invoke-RestMethod -Method Patch "http://localhost:8000/api/v1/orgs/$orgId/members/$memberId" -Headers $headers `
  -ContentType "application/json" -Body ($memberUpdate | ConvertTo-Json)
Estrutura do projeto
apps/api: backend FastAPI

apps/web: frontend Next.js

alembic/: migrations

Próxima fase
Veja CHECKLIST.md:

Fase 2B: convidados, mensalistas vs convidados, capitães, times, draft v1

Fase 3: marketplace estilo Airbnb (centros, quadras, disponibilidade, reservas)
