# 📄 CHECKLIST.md — Sport SaaS

## Como usar

* Cada fase deve ser concluída em pequenos PRs/commits.
* Marque `[x]` ao concluir.
* Registre decisões importantes na seção **Notas**.

---

# 🚀 Fase 2B — Social Completo (antes do Marketplace)

---

## ✅ 2B.0 Hardening de Repositório

* [x] `.gitignore` configurado

  * [x] `.next/`
  * [x] `__pycache__/`
  * [x] `*.pyc`
  * [x] `node_modules/`
* [x] Nenhum artefato de build versionado

---

## ✅ 2B.1 Attendance Consolidada (org-scoped)

* [x] Enum `AttendanceStatus`
* [x] Endpoint org-scoped `/orgs/{org_id}/games/{game_id}/attendance`
* [x] Migration idempotente
* [x] Tela com contagens + status do usuário
* [x] README + smoke tests

---

## ✅ 2B.2 Convidados (Guests)

### Modelagem

* [x] `org_guests`
* [x] `game_guests`
* [x] Snapshot por jogo
* [x] Convidado não é User/OrgMember

### Backend

* [x] Endpoints org-scoped
* [x] `billable=true` para game_guest

### Frontend

* [x] UI mínima no dashboard

---

## ✅ 2B.3 Mensalistas vs Convidados Fixos

### Modelagem

* [x] `member_type`
* [x] `is_active`
* [x] `nickname`
* [x] Migration com defaults + índices

### Backend

* [x] PATCH com permissões refinadas
* [x] Attendance retorna `member_type`, `included`, `billable`

### Frontend

* [x] UI edição membro
* [x] Badges na presença

⚠️ **Pendência (2C — Billing)**

* [ ] Cobrança por ciclo (MONTHLY)
* [ ] Cobrança por presença (GUEST)

---

## ✅ 2B.7 Perfil do Membro

### User

* [x] `full_name`
* [x] `avatar_url`
* [x] `phone`
* [x] `/dashboard/profile`
* [x] Edição de dados

### OrgMember

* [x] `nickname` integrado

---

## ✅ 2B.8 Página Detalhe do Jogo

* [x] Página `/dashboard/games/[id]`
* [x] Endpoint detalhado do jogo
* [x] Presença completa
* [x] Convidados
* [x] Ações rápidas

---

## ✅ 2B.9 Capitães e Times (MVP A/B)

### Backend

* [x] Capitães manual
* [x] Capitães sorteio
* [x] Anti-repetição
* [x] Persistência de times

### Frontend

* [x] UI Times A/B

📌 Nota: MVP suporta 2 times (A/B). Roadmap: suportar N times (3+).

---

## ✅ 2B.10 Draft v1 (sem realtime)

### Backend

* [x] Model Draft persistido
* [x] Ordem ABBA
* [x] Registrar picks
* [x] Impedir duplicidade
* [x] Atualizar times automaticamente

### Frontend

* [x] UI draft
* [x] Controle de turno
* [x] Finalizar draft

---

## ✅ 2B.11 RBAC Refinado

OWNER / ADMIN:

* [x] Editar jogo
* [x] Definir capitães
* [x] Iniciar draft
* [x] Gerenciar convidados

MEMBER:

* [x] Marcar presença
* [x] Ver draft

Geral:

* [x] Validar todas rotas sensíveis

---

## ✅ 2B.12 Smoke Tests Consolidados

Objetivo: validar sistema completo após cada fase.

* [x] Login test
* [x] Games test
* [x] Attendance test
* [x] Guest test
* [x] Captain test
* [x] Draft test
* [ ] RBAC test (opcional — requer conta MEMBER separada)

* [x] docker compose up -d --build
* [x] alembic upgrade head
* [x] npm run build


---

# 💰 Fase 2C — Cofre / Billing Inteligente

* [x] 2C.1 Cobrança por presença (PER_SESSION por jogo)
  - org_charges.game_id + indexes + FK
  - generate cria PER_SESSION com cycle_key=GAME:{game_id}
  - PAID gera ledger_entry_id
  - smoke: scripts/smoke-billing-per-session.ps1

* [ ] 2C.2 Cobrança ciclo MONTHLY (MEMBERSHIP)
* [ ] 2C.3 Integração ledger (dash / relatórios)
* [ ] 2C.4 Geração automática charges (agendada)
* [ ] 2C.5 Dashboard financeiro por org




---

# 🏟 Fase 3 — Marketplace

## 3.0 Modelo

* [ ] OrgType: GROUP | CENTER
* [ ] Visibilidade

## 3.1 Centro

* [ ] Units
* [ ] Courts
* [ ] Photos
* [ ] Policies

## 3.2 Reservas

* [ ] Templates
* [ ] Bloqueios
* [ ] Reservas
* [ ] Financeiro

## 3.3 Busca Pública

* [ ] Filtros
* [ ] Página centro
* [ ] Página quadra

---

# 📝 Notas

* member_type influencia cobrança futura
* game_guest sempre billable
* Attendance é org-scoped
* Convidado não vira membro
* MVP usa Times A/B; futuro: N teams
* Relacionamentos Game ↔ GameGuest devem sempre declarar `foreign_keys` explicitamente para evitar ambiguidade de mapper no SQLAlchemy.

---
