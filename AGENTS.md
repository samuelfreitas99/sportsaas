# AGENTS.md
Guia operacional para agentes/IA no repositório SportSaaS.

## Regras de ouro
1) NUNCA quebrar fluxos existentes (login, orgs, members, games, ledger).
2) Toda mudança backend precisa:
   - migrations Alembic
   - schemas pydantic
   - rotas registradas no main.py
   - smoke test (PowerShell) documentado no README ou no CHECKLIST.
3) Frontend:
   - não usar Server Actions
   - preferir páginas client-side simples com fetch/axios para /api/v1
4) Banco (Postgres):
   - `Base.metadata.create_all()` pode existir apenas como fallback de desenvolvimento, mas migrations Alembic são a fonte oficial de schema.
   - Enum em Postgres: cuidado com “type already exists” (usar checkfirst / create_type=False quando aplicável).
5) Commits:
   - não commitar `.next/`, `__pycache__/`, `.pyc`
   - atualizar `.gitignore` se necessário
6) Em modelos com múltiplas FKs entre as mesmas tabelas, sempre declarar `foreign_keys` explicitamente nos relationships.


## Convenções
- API base: /api/v1
- Auth: /api/v1/auth
- Org-scoped: /api/v1/orgs/{org_id}/...
- RBAC: OWNER > ADMIN > MEMBER
- MemberType: MONTHLY (mensalista) vs GUEST (convidado/avulso)

## Roadmap (alto nível)
- Fase 1: Core social (orgs, members, games, attendance, ledger) ✅
- Fase 2A: Billing + Charges ✅ (mínimo)
- Fase 2B: Social completo (convidados, capitães, times, draft v1, cofre/mensalistas)
- Fase 3: Marketplace (centros esportivos, unidades, quadras, disponibilidade, reservas)
- Fase 4: Pagamentos reais, notificações, PWA avançado, multi-tenant avançado

## Critério de aceite geral
- `docker compose up -d --build` funciona
- `docker compose exec api alembic upgrade head` funciona (idempotente o máximo possível)
- `apps/web` builda: `npm run build`
- Rotas principais respondem via Swagger (/docs)
