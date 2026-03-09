BACKEND_DIR = backend
FRONTEND_DIR = frontend
VENV = $(BACKEND_DIR)/.venv
BACKEND_PORT = 8001

ifeq ($(OS),Windows_NT)
  PY = $(VENV)/Scripts/python.exe
  PIP = $(VENV)/Scripts/pip.exe
  PYTHON = python
else
  PY = $(VENV)/bin/python
  PIP = $(VENV)/bin/pip
  PYTHON = python3
endif

.PHONY: setup setup-backend setup-frontend dev dev-lan backend frontend ollama-serve ollama-setup redis worker beat catchup test shell migrate seed seed-demo reset-db check backup restore up down build logs prod-up prod-down screenshots

# ── Local Development ──────────────────────────────────

setup: setup-backend setup-frontend

setup-backend:
	$(PYTHON) -m venv $(VENV)
	$(PIP) install -r $(BACKEND_DIR)/requirements.txt
	cd $(BACKEND_DIR) && $(CURDIR)/$(PY) manage.py migrate
	cd $(BACKEND_DIR) && $(CURDIR)/$(PY) manage.py seed_categories
	cd $(BACKEND_DIR) && $(CURDIR)/$(PY) manage.py seed_institutions
	cd $(BACKEND_DIR) && $(CURDIR)/$(PY) manage.py seed_email_rules
	cd $(BACKEND_DIR) && $(CURDIR)/$(PY) manage.py create_local_user

setup-frontend:
	cd $(FRONTEND_DIR) && npm install

dev:
	@echo "Starting Redis, backend (:$(BACKEND_PORT)), frontend, Celery worker & beat..."
	@make redis &
	@make backend &
	@make frontend &
	@make worker &
	@make beat &
	@sleep 5 && make catchup &
	@wait

dev-lan:
	@echo "Access from your phone: http://$$(ipconfig getifaddr en0):5173"
	VITE_HOST=0.0.0.0 BACKEND_HOST=0.0.0.0 ALLOWED_HOSTS=* CORS_ALLOW_ALL=true $(MAKE) dev

backend:
	@# Kill any existing process on the backend port
ifeq ($(OS),Windows_NT)
	@powershell -Command "Get-NetTCPConnection -LocalPort $(BACKEND_PORT) -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $$_.OwningProcess -Force -ErrorAction SilentlyContinue }" 2>NUL || ver>NUL
else
	@lsof -ti :$(BACKEND_PORT) | xargs kill -9 2>/dev/null || true
	@sleep 0.5
endif
	cd $(BACKEND_DIR) && $(CURDIR)/$(PY) manage.py migrate --run-syncdb 2>&1 | grep -v "No migrations to apply" || true
	cd $(BACKEND_DIR) && $(CURDIR)/$(PY) manage.py runserver $(or $(BACKEND_HOST),127.0.0.1):$(BACKEND_PORT)

frontend:
	cd $(FRONTEND_DIR) && npm run dev

ollama-serve:
ifeq ($(OS),Windows_NT)
	@where ollama >NUL 2>&1 && ( \
		echo Starting Ollama... && start /B ollama serve \
	) || echo Ollama not installed. Run: make ollama-setup
else
	@if curl -sf http://localhost:11434/api/tags >/dev/null 2>&1; then \
		echo "Ollama already running on :11434"; \
	elif command -v ollama >/dev/null 2>&1; then \
		echo "Starting Ollama..."; \
		ollama serve; \
	else \
		echo "Ollama not installed. Run: make ollama-setup"; \
	fi
endif

redis:
	@# Skip if Redis is already accessible on port 6379
	@if redis-cli -p 6379 ping 2>/dev/null | grep -q PONG; then \
		echo "Redis already running on :6379"; \
	else \
		docker run --rm -p 6379:6379 redis:7-alpine; \
	fi

worker:
	cd $(BACKEND_DIR) && $(CURDIR)/$(VENV)/bin/celery -A nullbook worker -l info --concurrency=2

beat:
	cd $(BACKEND_DIR) && $(CURDIR)/$(VENV)/bin/celery -A nullbook beat -l info

catchup:
	cd $(BACKEND_DIR) && $(CURDIR)/$(PY) manage.py catchup

test:
	cd $(BACKEND_DIR) && $(CURDIR)/$(VENV)/bin/pytest

shell:
	cd $(BACKEND_DIR) && $(CURDIR)/$(PY) manage.py shell

migrate:
	cd $(BACKEND_DIR) && $(CURDIR)/$(PY) manage.py migrate

makemigrations:
	cd $(BACKEND_DIR) && $(CURDIR)/$(PY) manage.py makemigrations

seed:
	cd $(BACKEND_DIR) && $(CURDIR)/$(PY) manage.py seed_categories
	cd $(BACKEND_DIR) && $(CURDIR)/$(PY) manage.py seed_institutions
	cd $(BACKEND_DIR) && $(CURDIR)/$(PY) manage.py seed_email_rules
	cd $(BACKEND_DIR) && $(CURDIR)/$(PY) manage.py create_local_user

seed-demo:
	cd $(BACKEND_DIR) && $(CURDIR)/$(PY) manage.py seed_demo_data

reset-db:
	rm -f $(BACKEND_DIR)/db.sqlite3
	$(MAKE) migrate
	$(MAKE) seed

check:
	cd $(BACKEND_DIR) && $(CURDIR)/$(PY) manage.py check_setup

backup:
	cd $(BACKEND_DIR) && $(CURDIR)/$(PY) manage.py backup

restore:
	@echo "Usage: make restore ARCHIVE=path/to/backup.tar.gz"
	cd $(BACKEND_DIR) && $(CURDIR)/$(PY) manage.py restore $(ARCHIVE)

ollama-setup:
ifeq ($(OS),Windows_NT)
	@where ollama >NUL 2>&1 || ( \
		echo Install Ollama from https://ollama.com/download && exit /B 1 \
	)
	ollama pull qwen3:8b
	ollama pull qwen3:4b
else
	@if ! command -v ollama >/dev/null 2>&1; then \
		echo "Installing Ollama..."; \
		if [ "$$(uname)" = "Darwin" ] && command -v brew >/dev/null 2>&1; then \
			brew install ollama; \
		else \
			curl -fsSL https://ollama.com/install.sh | sh; \
		fi; \
	else \
		echo "Ollama already installed"; \
	fi
	@if ! curl -sf http://localhost:11434/api/tags >/dev/null 2>&1; then \
		echo "Starting Ollama..."; \
		ollama serve &>/dev/null & \
		sleep 3; \
	else \
		echo "Ollama already running"; \
	fi
	ollama pull qwen3:8b
	ollama pull qwen3:4b
endif

# ── Docker (full stack) ───────────────────────────────

up:
	docker compose up -d

down:
	docker compose down

build:
	docker compose build

logs:
	docker compose logs -f

prod-up:
	docker compose -f docker-compose.prod.yml up -d --build

prod-down:
	docker compose -f docker-compose.prod.yml down

# ── Screenshots ───────────────────────────────────
# Requires `make dev` running in another terminal.
# Seeds demo data, then captures screenshots of every view.

screenshots:
	$(MAKE) seed-demo
	npx playwright test
