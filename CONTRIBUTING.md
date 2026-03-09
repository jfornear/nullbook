# Contributing to nullbook

Thanks for your interest in contributing to nullbook! This guide covers everything you need to get started.

## Development Setup

### Quick Start (Local)

```bash
# Clone the repo
git clone https://github.com/jfornear/nullbook.git
cd nullbook

# Option A: Interactive setup wizard
./setup.sh

# Option B: Makefile
make setup
make dev
```

### Quick Start (Docker)

```bash
cp .env.example .env
docker compose up
```

The backend runs on `http://localhost:8001` and the frontend on `http://localhost:5173`.

Login credentials are auto-generated during setup — check your `.env` file.

## Code Style

### Backend (Python)

- Formatter/linter: **ruff**
- Run `ruff check backend/` before committing
- Follow existing patterns: viewsets in `views.py`, serializers in `serializers.py`
- Django 4.2 + Django REST Framework

### Frontend (TypeScript/React)

- Linter: **eslint**
- Run `npx eslint .` from the `frontend/` directory
- Type-check with `npx tsc --noEmit`
- UI components: shadcn/ui (New York style, zinc theme) + Tailwind
- Icons: `lucide-react`

## Pull Request Process

1. **Fork and branch.** Create a feature branch from `main`:

   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Write tests.** Backend changes should include pytest tests. Run the full suite:

   ```bash
   make test
   ```

3. **Lint before pushing.**

   ```bash
   # Backend
   ruff check backend/

   # Frontend
   cd frontend && npx tsc --noEmit && npx eslint .
   ```

4. **Open a PR against `main`.** Include:
   - A clear description of what changed and why
   - Screenshots for UI changes
   - Any migration notes if you added/changed models

5. **CI must pass.** The GitHub Actions workflow runs linting and tests automatically.

## Testing

### Backend

```bash
# Run all tests
make test

# Run a specific test file
cd backend && .venv/bin/pytest core/tests/test_views.py -v
```

### Frontend

```bash
cd frontend
npx tsc --noEmit   # Type checking
npx eslint .       # Linting
```

## Project Structure

```
nullbook/
  backend/           # Django 4.2 + DRF
    core/            # Users, settings, shared models
    accounts/        # Bank accounts, institutions
    transactions/    # Transaction tracking
    portfolio/       # Investment portfolio
    taxes/           # Tax calculations
    news/            # Financial news
    imports/         # Data import utilities
    chat/            # AI chat assistant
  frontend/          # React + Vite + TypeScript
    src/
      pages/         # Route pages
      components/    # Reusable UI components
      lib/           # API client, utilities
```

## Questions?

Open an issue or start a discussion on GitHub. We're happy to help!
