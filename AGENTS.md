# Sport SaaS – AI Agent Rules

## Context

This is a multi-tenant sports SaaS platform.

Stack:
- FastAPI
- SQLAlchemy 2.0
- Alembic
- PostgreSQL
- Next.js 14 (App Router)
- TypeScript
- Tailwind
- Docker Compose

---

## Multi-Tenant Rules

1. All data must be scoped by org_id.
2. All organization routes must validate membership.
3. Role hierarchy:
   - OWNER
   - ADMIN
   - MEMBER
4. Only OWNER/ADMIN can manage financial entries.
5. OWNER cannot remove himself.

---

## Backend Standards

- UUID primary keys
- Numeric(12,2) for money
- Separate schemas: Create / Update / Response
- Always use response_model
- Always use Alembic for DB changes
- Use model_dump() for Pydantic

---

## Frontend Standards

- Use App Router
- Client components must declare 'use client'
- JWT stored in localStorage
- Use axios instance from lib/api.ts
- Redirect to /login on 401
- Store org id in localStorage as currentOrgId

---

## Safety

- Never remove working endpoints
- Never hardcode secrets
- Never change DB schema without migration

---

## Development Priority

1. Organization Members
2. Attendance improvements
3. Ledger improvements
4. Draft Live
5. Marketplace
6. Centers / Courts