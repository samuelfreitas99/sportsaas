# Sport SaaS

A SaaS web application for sports management.

## Stack

- **Backend**: FastAPI (Python 3.11)
- **Database**: PostgreSQL + SQLAlchemy 2.0 + Alembic
- **Frontend**: Next.js 14 + TypeScript + Tailwind
- **Infrastructure**: Docker Compose

## Prerequisites

- Docker & Docker Compose
- Node.js 18+ (for frontend)
- Python 3.11+ (for local backend dev if needed)

## Getting Started

### 1. Start the Backend and Database

```bash
docker compose up --build
```

### 2. Run Migrations

Open a new terminal and run:

```bash
# Enter the api container
docker compose exec api alembic upgrade head
```

### 3. Start the Frontend

```bash
cd apps/web
npm install
npm run dev
```

The frontend will be available at http://localhost:3000.
The backend API is at http://localhost:8000.
API Documentation (Swagger UI) is at http://localhost:8000/docs.

## Features

- **Multi-tenant**: Organization-based structure.
- **RBAC**: Owner, Admin, Member roles.
- **Auth**: JWT Authentication (Login, Register, Refresh).
- **Games**: Create, list, edit, and delete games.
- **Attendance**: Mark presence (Going, Maybe, Not Going).
- **Ledger**: Simple financial system for organizations.

## Project Structure

- `apps/api`: FastAPI backend.
- `apps/web`: Next.js frontend.

## Example Usage (cURL)

See `apps/api/README.md` for detailed API usage or use the Swagger UI.
