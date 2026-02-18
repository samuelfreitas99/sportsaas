# API_CONTRACT — SportSaaS (v1)

Contrato de API para o frontend (Next.js) consumir o backend (FastAPI).

## Base
- Base URL: `http://localhost:8000/api/v1`
- Auth: Bearer Token (JWT)
- Conteúdo:
  - JSON (`application/json`)
  - Login usa `application/x-www-form-urlencoded`

## Convenções
- IDs: UUID (string)
- Datas: ISO 8601 (ex: `2026-02-18T12:34:56Z`)
- Org-scoped: a maioria das rotas exige `org_id` no path
- Permissões (RBAC):
  - `OWNER` > `ADMIN` > `MEMBER`
- MemberType:
  - `MONTHLY` (mensalista)
  - `GUEST` (convidado/avulso)

## Headers
- Autenticadas:
  - `Authorization: Bearer <token>`
- Endpoints internos:
  - `X-Internal-Key: <INTERNAL_KEY>`

---

# 1) Auth

## POST /auth/login
Login por formulário (OAuth2PasswordRequestForm).

**Content-Type:** `application/x-www-form-urlencoded`

Body:
- `username` (email)
- `password`

Response:
```json
{
  "access_token": "string",
  "token_type": "bearer"
}
GET /users/me
Retorna usuário logado.

Headers:

Authorization Bearer

Response (exemplo):

{
  "id": "uuid",
  "email": "string",
  "full_name": "string|null",
  "avatar_url": "string|null",
  "phone": "string|null"
}
2) Organizations
Observação: detalhes exatos de payload podem variar; o frontend deve depender do que a API retornar no swagger/routers.

GET /organizations
Lista orgs que o usuário participa.

POST /organizations
Cria org.

GET /orgs/{org_id}
Detalhe da org.

3) Members
GET /orgs/{org_id}/members
Lista membros da org.

PATCH /orgs/{org_id}/members/{member_id}
Atualiza campos do membro (ex: nickname, member_type, is_active), respeitando RBAC.

Campos relevantes esperados:

member_type: MONTHLY | GUEST

is_active: boolean

nickname: string|null

4) Games
GET /orgs/{org_id}/games
Lista jogos da org.

POST /orgs/{org_id}/games
Cria jogo.

GET /orgs/{org_id}/games/{game_id}
Detalhe do jogo (Phase 2B.8), incluindo:

dados do jogo

attendance list/summary

convidados do jogo

capitães e times (A/B)

resumo do draft

5) Attendance
GET /orgs/{org_id}/games/{game_id}/attendance
Retorna:

status do usuário logado

lista de presenças do jogo

contagens por status

Status:

GOING | MAYBE | NOT_GOING

A attendance pode incluir flags (Phase 2B.3):

member_type

included

billable

PUT /orgs/{org_id}/games/{game_id}/attendance
Atualiza status do usuário logado.

6) Guests
Org Guests (catálogo)
GET /orgs/{org_id}/guests
Lista convidados cadastrados (catálogo por org).

POST /orgs/{org_id}/guests
Cria convidado no catálogo.

Game Guests (snapshot por jogo)
GET /orgs/{org_id}/games/{game_id}/guests
Lista convidados do jogo.

POST /orgs/{org_id}/games/{game_id}/guests
Adiciona convidado ao jogo.

Regra:

game_guest sempre billable=true

7) Captains / Teams (MVP A/B)
PUT /orgs/{org_id}/games/{game_id}/captains
Define capitães:

manual ou random

anti-repetição

GET /orgs/{org_id}/games/{game_id}/teams
Retorna times (A/B)

PUT /orgs/{org_id}/games/{game_id}/teams
Atualiza times (A/B)

8) Draft v1 (sem realtime)
POST /orgs/{org_id}/games/{game_id}/draft/start
Inicia draft (ordem ABBA).

POST /orgs/{org_id}/games/{game_id}/draft/pick
Registra pick (impede duplicidade), atualiza times.

POST /orgs/{org_id}/games/{game_id}/draft/finish
Finaliza draft.

GET /orgs/{org_id}/games/{game_id}/draft
Retorna estado atual.

9) Billing / Charges / Ledger
Billing gera cobranças (charges) e quando paga cria entradas no ledger.

Cobrança PER_SESSION (por jogo)
cycle_key: GAME:{game_id}

type: PER_SESSION

status:

PENDING

PAID (gera ledger_entry_id)

Cobrança MEMBERSHIP (mensal)
type: MEMBERSHIP

cycle_key: depende do ciclo (ex: MONTHLY:2026-02)

Rotas exatas de "generate charges" e settings podem existir em /billing e/ou /orgs/{org_id}/billing-settings.
Se necessário, o frontend pode ficar desacoplado disso no começo (somente finance/charges list).

10) Finance (org-scoped)
GET /orgs/{org_id}/finance/summary
Retorna totais e saldo:

income_total

expense_total

balance

pending_charges_total, paid_charges_total

pending_charges_count, paid_charges_count

GET /orgs/{org_id}/finance/recent?limit=20
Retorna:

ledger[] (recentes)

charges[] (recentes)

GET /orgs/{org_id}/finance/dashboard?start=&end=
Dashboard consolidado com filtro por período.

Parâmetros:

start (YYYY-MM-DD) opcional

end (YYYY-MM-DD) opcional

11) Internal (somente servidor / smoke)
POST /internal/billing/run
Headers:

X-Internal-Key

Ação:

percorre orgs e executa geração de charges

12) Erros (padrão)
401: Unauthorized (token inválido/ausente ou X-Internal-Key inválido)

403: Forbidden (sem permissão RBAC)

404: Not found

422: validação de payload

500: erro interno

Recomendação frontend:

tratar 401 => logout/redirect / (auth)/login

tratar 403 => toast e bloquear ações


---