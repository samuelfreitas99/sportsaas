# CHECKLIST.md — Sport SaaS

## Como usar
- Cada fase deve ser concluída em pequenos PRs/commits.
- Marque [x] ao concluir e registre decisões em "Notas".

---

## Fase 2B — Social completo (antes do Marketplace)

### 2B.0 Hardening de repo
- [ ] Adicionar/ajustar `.gitignore` para impedir commit de:
  - `.next/`
  - `__pycache__/`
  - `*.pyc`
  - `node_modules/`
- [ ] Garantir que nenhum artefato de build entrou no Git (limpar se já entrou)

### 2B.1 Attendance consolidada

- [x] Definir enum AttendanceStatus: GOING | MAYBE | NOT_GOING
- [x] Garantir endpoints consistentes por org e por game (org-scoped)
- [x] Tela do game (ou lista) mostrando contagens e status do usuário
- [x] Migration segura/idempotente (criar enum/table se não existir; backfill e índices quando já existir)
- [x] README + smoke tests atualizados


### 2B.2 Convidados
- [ ] Permitir adicionar convidados por jogo (nome/telefone opcional)
- [ ] Vincular convidado a um OrgMember (member_type=GUEST) OU tabela separada de guest_attendance
- [ ] Regras: convidado não tem login; só aparece em presença e cobrança

### 2B.3 Cofre / Mensalistas
- [ ] Definir member_type no OrgMember: MONTHLY vs GUEST
- [ ] Tela simples para marcar tipo do membro
- [ ] Ajustar geração de charges:
  - mensalista: cobrança fixa por ciclo
  - convidado: cobrança por presença (PER_SESSION)

### 2B.4 Capitães e times do jogo
- [ ] Campo captains no game: manual ou sorteio
- [ ] Times A/B: atribuir jogadores presentes
- [ ] UI simples para organizar times

### 2B.5 Draft v1 (sem realtime)
- [ ] Draft por turnos (ordem definida, picks registrados)
- [ ] Persistência no backend (draft_state)
- [ ] UI mínima para picks + bloqueios

### 2B.6 Ajustes do Billing (Phase 2A)
- [ ] Garantir migrations idempotentes (evitar erro de enum/tabela já existente)
- [ ] Garantir: marcar charge PAID -> ledger INCOME (já existe, validar)
- [ ] Smoke tests atualizados no README

### 2B.7 Perfil do Membro (User + OrgMember)

- [x] Expandir User:
  - name (já existe?)
  - avatar_url (string)
  - phone (opcional)
- [x] Permitir upload ou definição de avatar (inicialmente URL simples)
- [x] Página /dashboard/profile
- [x] Permitir editar dados pessoais

- [x] Expandir OrgMember:
  - nickname (opcional, apelido no grupo)
  - member_type: MONTHLY | GUEST
  - is_active (boolean)
- [x] Tela para editar tipo do membro (mensalista vs convidado fixo)


---

### 2B.8 Página Detalhe do Jogo (Game Details)

- [ ] Criar página /dashboard/games/[id]
- [ ] Exibir:
  - Data, horário, local
  - Lista de presença (GOING/MAYBE/NOT_GOING)
  - Contagem total
  - Convidados adicionados
- [ ] Botão rápido para:
  - Marcar presença
  - Adicionar convidado
  - Definir capitães (futuro)
  - Iniciar draft (futuro)

---

### 2B.9 Capitães e Times

- [ ] Campo no Game:
  - captain_a_id
  - captain_b_id
- [ ] Opção:
  - Seleção manual
  - Sorteio automático
- [ ] Regra anti-repetição:
  - Não repetir capitão em jogos consecutivos se houver outros elegíveis
- [ ] UI para montar Times A/B manualmente

---

### 2B.10 Draft v1 (sem realtime)

- [ ] Modelo draft_state persistido no backend
- [ ] Ordem de picks definida (A-B-B-A ou configurável)
- [ ] Registrar picks por rodada
- [ ] Impedir duplicidade de jogador
- [ ] UI simples de seleção
- [ ] Encerrar draft e salvar times finais

---

### 2B.11 RBAC e Permissões Refinadas

- [ ] OWNER/ADMIN podem:
  - Editar jogo
  - Definir capitães
  - Iniciar draft
  - Gerenciar convidados
- [ ] MEMBER pode:
  - Marcar presença
  - Ver draft
- [ ] Validar todas rotas sensíveis

---

### 2B.12 Testes Rápidos (Smoke Tests por Fase)

- [ ] Criar bloco no README com:
  - Attendance test
  - Guest test
  - Draft test
  - Captain selection test
- [ ] Garantir build limpo:
  - docker compose up -d --build
  - alembic upgrade head
  - npm run build (apps/web)


## Fase 3 — Marketplace (centros esportivos)

### 3.0 Modelo e visibilidade
- [ ] OrgType: GROUP vs CENTER/BUSINESS
- [ ] Visibilidade: PRIVATE | MARKETPLACE | HYBRID

### 3.1 Estrutura do centro esportivo
- [ ] Units/Locations (unidades)
- [ ] Courts (quadras)
- [ ] Photos (opcional depois)
- [ ] Policies (cancelamento, antecedência, etc.)

### 3.2 Disponibilidade e reservas
- [ ] Templates de horários por quadra
- [ ] Bloqueios (manutenção/eventos)
- [ ] Reservas: status PENDING/CONFIRMED/CANCELLED
- [ ] Integração financeira (ledger + cobrança)

### 3.3 Busca pública (estilo Airbnb)
- [ ] Página pública com filtros (cidade/bairro, esporte, preço, horário)
- [ ] Página do centro
- [ ] Página da quadra + agenda

---

## Notas / Decisões
- (preencha aqui)
