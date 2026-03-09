#!/usr/bin/env bash
set -euo pipefail

# ── Colors ────────────────────────────────────────────
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

info()    { echo -e "${CYAN}[info]${NC}  $1"; }
success() { echo -e "${GREEN}[ok]${NC}    $1"; }
warn()    { echo -e "${YELLOW}[warn]${NC}  $1"; }
error()   { echo -e "${RED}[error]${NC} $1"; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"
FRONTEND_DIR="$SCRIPT_DIR/frontend"
VENV_DIR="$BACKEND_DIR/.venv"
ENV_FILE="$SCRIPT_DIR/.env"
ENV_EXAMPLE="$SCRIPT_DIR/.env.example"

# ── Header ────────────────────────────────────────────
echo ""
echo -e "${BOLD}nullbook setup wizard${NC}"
echo -e "────────────────────────────────────────"
echo ""

# ── Dependency Checks ─────────────────────────────────
info "Checking dependencies..."

# Python 3.12+
if command -v python3 &>/dev/null; then
    PY_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    PY_MAJOR=$(echo "$PY_VERSION" | cut -d. -f1)
    PY_MINOR=$(echo "$PY_VERSION" | cut -d. -f2)
    if [ "$PY_MAJOR" -ge 3 ] && [ "$PY_MINOR" -ge 12 ]; then
        success "Python $PY_VERSION"
    else
        error "Python 3.12+ required (found $PY_VERSION)"
        exit 1
    fi
else
    error "Python 3 not found. Install Python 3.12+ and try again."
    exit 1
fi

# Node.js 18+
if command -v node &>/dev/null; then
    NODE_VERSION=$(node -v | sed 's/v//')
    NODE_MAJOR=$(echo "$NODE_VERSION" | cut -d. -f1)
    if [ "$NODE_MAJOR" -ge 18 ]; then
        success "Node.js $NODE_VERSION"
    else
        error "Node.js 18+ required (found $NODE_VERSION)"
        exit 1
    fi
else
    error "Node.js not found. Install Node.js 18+ and try again."
    exit 1
fi

# Redis (optional, warn if missing)
if command -v redis-cli &>/dev/null; then
    if redis-cli ping 2>/dev/null | grep -q PONG; then
        success "Redis is running"
    else
        warn "Redis is installed but not running. Celery tasks will not work until Redis is started."
    fi
else
    warn "Redis not found. Background tasks (Celery) require Redis."
    warn "Install with: brew install redis (macOS) or apt install redis-server (Linux)"
fi

echo ""

# ── .env Setup ────────────────────────────────────────
if [ -f "$ENV_FILE" ]; then
    info ".env file already exists, keeping current values."
else
    info "Creating .env from .env.example..."
    cp "$ENV_EXAMPLE" "$ENV_FILE"
    success "Created .env"
fi

echo ""
echo -e "${BOLD}AI Setup${NC}"
echo -e "────────────────────────────────────────"
echo ""

# Anthropic API key
EXISTING_KEY=""
if [ -f "$ENV_FILE" ]; then
    EXISTING_KEY=$(grep -E "^ANTHROPIC_API_KEY=" "$ENV_FILE" 2>/dev/null | cut -d= -f2-)
fi

if [ -n "$EXISTING_KEY" ] && [ "$EXISTING_KEY" != "your-anthropic-api-key" ]; then
    success "Anthropic API key already configured"
else
    info "nullbook uses Claude (Anthropic) for AI features."
    info "Get an API key at: https://console.anthropic.com/settings/keys"
    echo ""
    read -rp "  Anthropic API key (or press Enter to skip): " api_key
    if [ -n "$api_key" ]; then
        sed -i.bak "s|^ANTHROPIC_API_KEY=.*|ANTHROPIC_API_KEY=$api_key|" "$ENV_FILE"
        rm -f "$ENV_FILE.bak"
        success "Anthropic API key saved"
    else
        warn "Skipped — add ANTHROPIC_API_KEY to .env before using chat"
    fi
fi

echo ""

# Plaid credentials (optional)
read -rp "Configure Plaid for bank syncing? (y/N): " configure_plaid
if [[ "$configure_plaid" =~ ^[Yy]$ ]]; then
    read -rp "  Plaid Client ID: " plaid_client_id
    read -rp "  Plaid Secret: " plaid_secret
    read -rp "  Plaid Environment (sandbox/development/production) [sandbox]: " plaid_env
    plaid_env="${plaid_env:-sandbox}"

    sed -i.bak "s|^PLAID_CLIENT_ID=.*|PLAID_CLIENT_ID=$plaid_client_id|" "$ENV_FILE"
    sed -i.bak "s|^PLAID_SECRET=.*|PLAID_SECRET=$plaid_secret|" "$ENV_FILE"
    sed -i.bak "s|^PLAID_ENV=.*|PLAID_ENV=$plaid_env|" "$ENV_FILE"
    rm -f "$ENV_FILE.bak"
    success "Plaid credentials saved"
else
    info "Skipping Plaid (you can add credentials to .env later)"
fi

echo ""

# Google OAuth (optional)
read -rp "Configure Google OAuth for Gmail scanning? (y/N): " configure_google
if [[ "$configure_google" =~ ^[Yy]$ ]]; then
    read -rp "  Google Client ID: " google_client_id
    read -rp "  Google Client Secret: " google_client_secret

    sed -i.bak "s|^GOOGLE_CLIENT_ID=.*|GOOGLE_CLIENT_ID=$google_client_id|" "$ENV_FILE"
    sed -i.bak "s|^GOOGLE_CLIENT_SECRET=.*|GOOGLE_CLIENT_SECRET=$google_client_secret|" "$ENV_FILE"
    rm -f "$ENV_FILE.bak"
    success "Google OAuth credentials saved"
else
    info "Skipping Google OAuth (you can add credentials to .env later)"
fi

echo ""
echo -e "${BOLD}Installing Dependencies${NC}"
echo -e "────────────────────────────────────────"
echo ""

# Python venv + requirements
if [ ! -d "$VENV_DIR" ]; then
    info "Creating Python virtual environment..."
    python3 -m venv "$VENV_DIR"
    success "Virtual environment created at backend/.venv/"
else
    success "Virtual environment already exists"
fi

info "Installing Python dependencies..."
"$VENV_DIR/bin/pip" install --upgrade pip --quiet
"$VENV_DIR/bin/pip" install -r "$BACKEND_DIR/requirements.txt" --quiet
success "Python dependencies installed"

echo ""

# Frontend dependencies
info "Installing frontend dependencies..."
cd "$FRONTEND_DIR" && npm install --silent 2>/dev/null
success "Frontend dependencies installed"

echo ""

echo -e "${BOLD}Database Setup${NC}"
echo -e "────────────────────────────────────────"
echo ""

# Run migrations
info "Running database migrations..."
cd "$BACKEND_DIR" && "$VENV_DIR/bin/python" manage.py migrate --verbosity=0
success "Migrations complete"

# Seed data
info "Seeding categories..."
cd "$BACKEND_DIR" && "$VENV_DIR/bin/python" manage.py seed_categories > /dev/null
success "Categories seeded"

info "Seeding institutions..."
cd "$BACKEND_DIR" && "$VENV_DIR/bin/python" manage.py seed_institutions > /dev/null
success "Institutions seeded"

info "Creating local dev user..."
cd "$BACKEND_DIR" && "$VENV_DIR/bin/python" manage.py create_local_user > /dev/null
success "Local user ready"

# ── Done ──────────────────────────────────────────────
echo ""
echo -e "────────────────────────────────────────"
echo -e "${GREEN}${BOLD}Setup complete!${NC}"
echo ""
echo -e "To start the dev servers:"
echo ""
echo -e "  ${CYAN}make dev${NC}"
echo ""
echo -e "This starts Redis, the backend (:8001), and the frontend (:5173)."
echo -e "Login credentials are in your ${BOLD}.env${NC} file."
echo ""
echo -e "Or use Docker:"
echo ""
echo -e "  ${CYAN}docker compose up${NC}"
echo ""
