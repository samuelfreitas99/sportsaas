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

* [x] Cobrança por ciclo (MONTHLY)
* [x] Cobrança por presença (PER_SESSION)

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

Perfeito — dá pra deixar **bem mais “clean” e sem duplicidade**, e já encaixar a parte **Auth definitiva (cookies + sessões)** dentro da 2D (porque isso é base do app), e deixar a **PWA** como 2E mesmo, antes do Marketplace.

Abaixo vai a **versão atualizada** dessa parte “de baixo” do checklist (já removendo repetição da 2E e deixando 2F só como placeholder).

---

# 💰 Fase 2C — Cofre / Billing Inteligente

* [x] 2C.1 Cobrança por presença (PER_SESSION por jogo)

  * org_charges.game_id + indexes + FK
  * generate cria PER_SESSION com cycle_key=GAME:{game_id}
  * PAID gera ledger_entry_id
  * smoke: scripts/smoke-billing-per-session.ps1

* [x] 2C.2 Cobrança ciclo MONTHLY (MEMBERSHIP)

  * smoke: scripts/smoke-billing-membership.ps1

* [x] 2C.3 Integração ledger + relatórios (Backend)

  * endpoints:

    * GET /orgs/{org_id}/finance/summary
    * GET /orgs/{org_id}/finance/recent
  * smoke: scripts/smoke-finance-summary.ps1

* [x] 2C.4 Geração automática charges (trigger interno)

  * endpoint interno: POST /internal/billing/run (header: X-Internal-Key)
  * reuso da lógica via função core (_generate_charges_core) no billing.py
  * smoke: scripts/smoke-billing-internal-run.ps1

* [x] 2C.5 Dashboard financeiro por org (Backend)

  * API pronta:

    * GET /orgs/{org_id}/finance/summary
    * GET /orgs/{org_id}/finance/recent
    * GET /orgs/{org_id}/finance/dashboard?start=&end=
  * suporte a filtro por período
  * smoke: scripts/smoke-finance-dashboard.ps1

* [ ] 2C.6 Dashboard financeiro por org (Frontend)

  * rota definitiva: /app/orgs/[orgId]/finance
  * cards: income, expense, balance, pending_total, paid_total
  * lista “recent” (ledger + charges)
  * filtro período (start/end)
  * gráfico simples (saldo ou income/expense por dia)

---

## 🧭 Fase 2D — Frontend Definitivo (Base do App)

* [x] 2D.1 Estrutura de rotas do app (org-scoped)

  * /app/orgs/[orgId]/...
  * layouts base (app + org)

* [ ] 2D.2 Auth definitiva (Cookies HTTPOnly) — **MVP seguro**

  * backend: cookies access/refresh + CORS credentials
  * endpoints: /auth/me, /auth/refresh, /auth/logout
  * frontend: axios `withCredentials`, remover localStorage token
  * guard de rota (redirect quando não autenticado)

* [ ] 2D.3 Sessões (refresh revogável no banco) — **definitivo**

  * migration: tabela `auth_sessions` (hash do refresh + revogação)
  * logout revoga sessão + limpa cookies
  * smoke: script simples de login/refresh/logout (opcional)

* [ ] 2D.4 API client único (web)

  * baseURL por env (dev/prod)
  * interceptors: 401 → tenta refresh → retry → fallback logout
  * padronizar erros/toasts (mínimo)

* [ ] 2D.5 Módulo Finance real (2C.6) ✅ (primeiro módulo definitivo)

  * page + cards + lista + filtros + gráfico simples
  * consumir endpoints reais `/orgs/{org_id}/finance/*`

* [ ] 2D.6 Games real (lista + detalhe)

  * consumir endpoints reais
  * ações (presença, convidados, times, draft)

* [ ] 2D.7 Members/Guests real (não experimental)

  * membros + badges + editar member_type
  * org_guests + game_guests

---

## 📱 Fase 2E — PWA Base (antes do Marketplace)

* [ ] 2E.1 Manifest + ícones

  * `app/manifest.ts` (name, short_name, start_url, display, theme_color)
  * ícones `public/icons/*` (192/512 + maskable)
  * metadata no layout (theme-color / apple-web-app)

* [ ] 2E.2 Service Worker (cache básico)

  * estratégia: cache “app shell” + network-first para API
  * página offline fallback
  * teste: “Add to Home Screen” + reload offline

* [ ] 2E.3 UX PWA

  * detectar instalação / prompt (opcional)
  * ajustes mobile (safe areas, scroll, touch targets)

* [ ] 2E.4 Observabilidade mínima

  * log de erro client-side (console + placeholder p/ tool futura)

---

## 🔔 Fase 2F — Push Notifications (placeholder)

* [ ] 2F.1 Modelagem + opt-in
* [ ] 2F.2 Envio básico (ex.: lembrete de jogo)
* [ ] 2F.3 Preferências por usuário/org

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