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
3) Acessos
Web: http://localhost:3000

API: http://localhost:8000

Swagger: http://localhost:8000/docs

Fases implementadas (resumo)
Phase 2B.1 — Attendance org-scoped
GET/PUT /api/v1/orgs/{org_id}/games/{game_id}/attendance

Status: GOING | MAYBE | NOT_GOING

Phase 2B.2 — Guests
org_guests (catálogo por org) e game_guests (snapshot por jogo)

game_guest sempre billable=true

Phase 2B.3 — MemberType (MONTHLY vs GUEST)
OrgMember.member_type: MONTHLY | GUEST

Attendance retorna flags: included e billable

Phase 2B.8 — Game Details
GET /api/v1/orgs/{org_id}/games/{game_id} com:

detalhes do jogo

attendance list/summary

convidados do jogo

capitães e times (A/B)

resumo do draft

Phase 2B.9 — Capitães e Times (MVP A/B)
PUT /captains (MANUAL/RANDOM)

GET/PUT /teams (A/B/null)

Nota: MVP atual é A/B; roadmap: N times.

Phase 2B.10 — Draft v1 (persistido, sem realtime)
POST /draft/start

POST /draft/pick

POST /draft/finish

GET /draft

Ordem ABBA e picks persistidos; atualiza times automaticamente.

Phase 2B.11 — RBAC refinado
MEMBER: pode ver jogos/draft e marcar presença

ADMIN/OWNER: pode criar jogo, gerenciar convidados, capitães/times e draft

Smoke tests (Phase 2B.12)
Os testes automatizados ficam em scripts/ e rodam via PowerShell.