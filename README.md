# Sport SaaS

Plataforma SaaS para gestão esportiva:
- Grupos organizam jogos, presença, convidados, times, draft e financeiro
- (Em breve) Centros esportivos gerenciam unidades/quadras/reservas estilo “Airbnb”

## Stack
- Backend: FastAPI (Python 3.11) + SQLAlchemy 2.0 + Alembic
- DB: PostgreSQL 15
- Frontend: Next.js 14 + TypeScript + Tailwind
- Infra: Docker Compose

---

## Quick start (dev)

### 1) Subir tudo
```bash
docker compose up -d --build
2) Rodar migrations
docker compose exec api alembic upgrade head
3) Acessos
Web: http://localhost:3000

API: http://localhost:8000/api/v1

Swagger: http://localhost:8000/docs

Smoke tests (PowerShell)
Os testes ficam em scripts/.

Billing
powershell -ExecutionPolicy Bypass -File .\scripts\smoke-billing-per-session.ps1 -Email "SEU_EMAIL" -Pass "SUA_SENHA" -OrgId "ORG_ID"
powershell -ExecutionPolicy Bypass -File .\scripts\smoke-billing-membership.ps1   -Email "SEU_EMAIL" -Pass "SUA_SENHA" -OrgId "ORG_ID"
Finance
powershell -ExecutionPolicy Bypass -File .\scripts\smoke-finance-summary.ps1   -Email "SEU_EMAIL" -Pass "SUA_SENHA" -OrgId "ORG_ID"
powershell -ExecutionPolicy Bypass -File .\scripts\smoke-finance-dashboard.ps1 -Email "SEU_EMAIL" -Pass "SUA_SENHA" -OrgId "ORG_ID"
Internal billing (trigger)
Requer header X-Internal-Key e INTERNAL_KEY configurado no backend.

powershell -ExecutionPolicy Bypass -File .\scripts\smoke-billing-internal-run.ps1
Status atual (resumo)
Fase 2B — Social Completo ✅
Attendance org-scoped

Guests (org_guests / game_guests)

MemberType (MONTHLY vs GUEST)

Game details

Capitães + Times A/B

Draft v1 persistido (sem realtime)

RBAC refinado

Smoke tests consolidados

Fase 2C — Billing / Finance ✅ (Backend)
Charges: MEMBERSHIP + PER_SESSION (por jogo)

Ledger auto ao pagar charge

Finance endpoints: summary/recent/dashboard + filtros

Trigger interno: /internal/billing/run + smoke

Próximo passo
Fase 2C.6: Frontend do dashboard financeiro (cards + filtros + gráfico + recent)

Depois: Fase 3 Marketplace