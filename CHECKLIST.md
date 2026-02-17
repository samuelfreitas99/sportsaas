# 📄 CHECKLIST.md — Sport SaaS

## Como usar

* Cada fase deve ser concluída em pequenos PRs/commits.
* Marque `[x]` ao concluir.
* Registre decisões importantes na seção **Notas**.

---

# 🚀 Fase 2B — Social Completo (antes do Marketplace)

---

## ✅ 2B.0 Hardening de Repositório

* [x] `.gitignore` configurado para impedir commit de:

  * [x] `.next/`
  * [x] `__pycache__/`
  * [x] `*.pyc`
  * [x] `node_modules/`
* [x] Garantir que nenhum artefato de build está versionado

---

## ✅ 2B.1 Attendance Consolidada (org-scoped)

* [x] Enum `AttendanceStatus`: `GOING | MAYBE | NOT_GOING`
* [x] Endpoint org-scoped:

  * [x] `/orgs/{org_id}/games/{game_id}/attendance`
* [x] Migration idempotente segura
* [x] Tela exibindo contagens + status do usuário
* [x] README + smoke tests atualizados

---

## ✅ 2B.2 Convidados (Guests)

### Modelagem

* [x] `org_guests` (catálogo por organização)
* [x] `game_guests` (snapshot por jogo)
* [x] Convidado não é `User` nem `OrgMember`
* [x] Snapshot pode vir do catálogo

### Backend

* [x] Endpoints org-scoped
* [x] Flag `billable=true` para convidados sem login

### Frontend

* [x] UI mínima no `/dashboard`

---

## ✅ 2B.3 Mensalistas vs Convidados Fixos (member_type)

### Modelagem

* [x] `OrgMember.member_type: MONTHLY | GUEST`
* [x] `is_active`
* [x] `nickname`
* [x] Migration segura com defaults + índices

### Backend

* [x] PATCH org-scoped com permissões refinadas
* [x] Attendance retorna:

  * [x] `member_type`
  * [x] `included`
  * [x] `billable`

### Frontend

* [x] UI para editar tipo do membro em `/dashboard/members`
* [x] Badges MONTHLY/GUEST na presença

### ⚠️ Pendente (entra na Fase 2C — Billing)

* [ ] Geração automática de charges:

  * [ ] Mensalista → cobrança por ciclo
  * [ ] Convidado fixo → cobrança por presença

---

## ✅ 2B.7 Perfil do Membro (User + OrgMember)

### User

* [x] `full_name`
* [x] `avatar_url`
* [x] `phone`
* [x] Página `/dashboard/profile`
* [x] Editar dados pessoais

### OrgMember

* [x] `nickname` integrado à UI

---

# 🔜 Próximas Fases Sociais

---

## 🟡 2B.8 Página Detalhe do Jogo (Game Details)

* [x] Criar página `/dashboard/games/[id]`
* [x] Endpoint detalhado:

  * [x] `/orgs/{org_id}/games/{game_id}`
* [x] Exibir:

  * [x] Data / horário
  * [x] Lista de presença
  * [x] Contagens
  * [x] Convidados do jogo
* [x] Botões rápidos:

  * [x] Marcar presença
  * [x] Adicionar convidado
  * [ ] Definir capitães (futuro)
  * [ ] Iniciar draft (futuro)

---

## 🟡 2B.9 Capitães e Times

### Backend

* [x] Campo no Game:

  * [x] `captain_a_member_id` / `captain_a_guest_id`
  * [x] `captain_b_member_id` / `captain_b_guest_id`
* [x] Seleção:

  * [x] Manual
  * [x] Sorteio automático
* [x] Regra anti-repetição de capitão

### Frontend

* [x] UI para montar Times A/B

---

## 🟡 2B.10 Draft v1 (sem realtime)

### Backend

* [ ] Modelo `draft_state` persistido
* [ ] Ordem A-B-B-A (ou configurável)
* [ ] Registrar picks
* [ ] Impedir duplicidade

### Frontend

* [ ] UI simples de seleção
* [ ] Encerrar draft e salvar times

---

## 🟡 2B.11 RBAC e Permissões Refinadas

### OWNER / ADMIN podem:

* [ ] Editar jogo
* [ ] Definir capitães
* [ ] Iniciar draft
* [ ] Gerenciar convidados

### MEMBER pode:

* [ ] Marcar presença

* [ ] Ver draft

* [ ] Validar todas rotas sensíveis

---

## 🟡 2B.12 Smoke Tests por Fase

* [ ] Bloco no README com:

  * [ ] Attendance test
  * [ ] Guest test
  * [ ] Draft test
  * [ ] Captain selection test
* [ ] Validar build limpo:

  * [ ] `docker compose up -d --build`
  * [ ] `alembic upgrade head`
  * [ ] `npm run build`

---

# 💰 Fase 2C — Cofre / Billing Inteligente

(Entrará após Capitães/Draft)

* [ ] Cobrança por ciclo para `MONTHLY`
* [ ] Cobrança por presença para `GUEST`
* [ ] Integração com ledger
* [ ] Geração automática de charges
* [ ] Dashboard financeiro por organização

---

# 🏟 Fase 3 — Marketplace (Centros Esportivos)

---

## 3.0 Modelo e Visibilidade

* [ ] `OrgType: GROUP | CENTER`
* [ ] `Visibilidade: PRIVATE | MARKETPLACE | HYBRID`

---

## 3.1 Estrutura do Centro

* [ ] Units
* [ ] Courts
* [ ] Photos
* [ ] Policies

---

## 3.2 Disponibilidade e Reservas

* [ ] Templates de horários
* [ ] Bloqueios
* [ ] Reservas `PENDING | CONFIRMED | CANCELLED`
* [ ] Integração financeira

---

## 3.3 Busca Pública estilo Airbnb

* [ ] Página pública com filtros
* [ ] Página do centro
* [ ] Página da quadra + agenda

---

# 📝 Notas / Decisões

* `member_type` influencia cobrança futura
* `game_guest` sempre `billable=true`
* Attendance é org-scoped
* Convidado não vira automaticamente membro

---


