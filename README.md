# Sport SaaS

A multi-tenant SaaS platform for sports management.

---

## Stack

- Backend: FastAPI (Python 3.11)
- Database: PostgreSQL 15
- ORM: SQLAlchemy 2.0
- Migrations: Alembic
- Frontend: Next.js 14 (App Router) + TypeScript + Tailwind
- Infrastructure: Docker Compose

---

## Architecture

- Multi-tenant (organization-based isolation)
- JWT Authentication
- RBAC (Owner / Admin / Member)
- Games + Attendance
- Ledger (Income / Expense per organization)

---

## 🚀 Running the Project (Docker Only)

### 1. Start everything

```bash
docker compose up --build
2. Run migrations
docker compose exec api alembic upgrade head
URLs
Frontend: http://localhost:3000

Backend API: http://localhost:8000

Swagger Docs: http://localhost:8000/docs

Development Rules
Always use Alembic for DB changes.

Never modify models without migration.

All protected routes require JWT.

All org routes must validate membership.

Never break working authentication.