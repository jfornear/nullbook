# nullbook — Development Guide

## Project Overview

Local-first personal finance platform. Django backend + React frontend.

## Quick Start (Local)

```bash
make setup      # Creates venv, installs deps, runs migrations, seeds data
make dev        # Starts Redis (Docker), backend (8001), frontend (5173)
```

## Commands

- **Setup**: `make setup` (one-time: venv + npm install + migrate + seed)
- **Dev server**: `make dev` (starts all services)
- **LAN dev**: `make dev-lan` (binds to 0.0.0.0, prints LAN URL for phone access)
- **Backend only**: `make backend` (runs on port 8001)
- **Frontend only**: `make frontend` (runs on port 5173)
- **Tests**: `make test` (runs pytest)
- **Shell**: `make shell` (Django shell)
- **Migrations**: `make makemigrations && make migrate`
- **Reset DB**: `make reset-db`
- **Docker (full stack)**: `make up` / `make down`

## Backend

- Python venv at `backend/.venv/`
- Django 4.2 + DRF, SQLite default
- Apps: core, accounts, transactions, portfolio, taxes, news, imports
- Session auth (single local user, credentials auto-generated in .env)
- Celery + Redis for background tasks
- Run Django checks: `backend/.venv/bin/python backend/manage.py check`

## Frontend

- React + Vite + TypeScript at `frontend/`
- shadcn/ui (New York style, zinc theme) + Tailwind
- React Query for server state
- Recharts for charts
- react-router-dom for routing
- PWA enabled via vite-plugin-pwa (Add to Home Screen on mobile)

## Conventions

- Django viewsets in `views.py`, serializers in `serializers.py`
- Frontend pages in `src/pages/`, reusable components in `src/components/`
- API client in `src/lib/api.ts` with credentials: 'include'
- Use `lucide-react` for icons
