#!/usr/bin/env bash
# nullbook installer — curl -fsSL https://nullbook.ai/install.sh | bash
set -euo pipefail

# ── Colors ────────────────────────────────────────────
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
BOLD='\033[1m'
DIM='\033[2m'
NC='\033[0m'

info()    { echo -e "${CYAN}  [info]${NC}  $1"; }
success() { echo -e "${GREEN}  [ok]${NC}    $1"; }
warn()    { echo -e "${YELLOW}  [warn]${NC}  $1"; }
fail()    { echo -e "${RED}  [fail]${NC}  $1"; exit 1; }

INSTALL_DIR="${NULLBOOK_DIR:-$HOME/nullbook}"
REPO_URL="https://github.com/jfornear/nullbook.git"

# ── Header ────────────────────────────────────────────
echo ""
echo -e "  ${BOLD}nullbook Installer${NC}"
echo -e "  ${DIM}The AI agent for your personal finances.${NC}"
echo ""

# ── OS Detection ──────────────────────────────────────
OS="unknown"
ARCH="$(uname -m)"
case "$(uname -s)" in
  Darwin)  OS="macos" ;;
  Linux)   OS="linux" ;;
  MINGW*|MSYS*|CYGWIN*) OS="windows" ;;
esac

if [ "$OS" = "unknown" ]; then
  fail "Unsupported operating system: $(uname -s)"
fi

info "Detected ${BOLD}$OS${NC} ($ARCH)"

# ── Windows Redirect ─────────────────────────────────
if [ "$OS" = "windows" ]; then
  echo ""
  warn "This bash installer doesn't support Windows natively."
  echo ""
  echo -e "  ${BOLD}Option 1: Use PowerShell (recommended)${NC}"
  echo -e "  ${DIM}Open PowerShell and run:${NC}"
  echo -e "    irm https://nullbook.ai/install.ps1 | iex"
  echo ""
  echo -e "  ${BOLD}Option 2: Use WSL${NC}"
  echo -e "  ${DIM}Install WSL, then re-run this script inside it:${NC}"
  echo -e "    wsl --install"
  echo ""
  exit 0
fi

# ── Dependency Installer ──────────────────────────────
install_dep() {
  local name="$1"
  local brew_pkg="${2:-$1}"
  local apt_pkg="${3:-$1}"

  if [ "$OS" = "macos" ]; then
    if command -v brew &>/dev/null; then
      info "Installing $name via Homebrew..."
      brew install "$brew_pkg" --quiet 2>/dev/null
    else
      fail "$name not found. Install Homebrew first: https://brew.sh"
    fi
  elif [ "$OS" = "linux" ]; then
    if command -v apt-get &>/dev/null; then
      info "Installing $name via apt..."
      sudo apt-get update -qq && sudo apt-get install -y -qq "$apt_pkg"
    elif command -v dnf &>/dev/null; then
      info "Installing $name via dnf..."
      sudo dnf install -y -q "$apt_pkg"
    elif command -v pacman &>/dev/null; then
      info "Installing $name via pacman..."
      sudo pacman -S --noconfirm "$apt_pkg"
    else
      fail "$name not found and no package manager detected. Install $name manually."
    fi
  fi
}

# ── Check / Install Python ────────────────────────────
if command -v python3 &>/dev/null; then
  PY_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
  PY_MINOR=$(echo "$PY_VERSION" | cut -d. -f2)
  if [ "$PY_MINOR" -ge 12 ]; then
    success "Python $PY_VERSION"
  else
    warn "Python 3.12+ required (found $PY_VERSION)"
    install_dep "Python" "python@3.12" "python3"
    success "Python installed"
  fi
else
  warn "Python not found"
  install_dep "Python" "python@3.12" "python3"
  success "Python installed"
fi

# ── Check / Install Node.js ───────────────────────────
if command -v node &>/dev/null; then
  NODE_VERSION=$(node -v | sed 's/v//')
  NODE_MAJOR=$(echo "$NODE_VERSION" | cut -d. -f1)
  if [ "$NODE_MAJOR" -ge 18 ]; then
    success "Node.js $NODE_VERSION"
  else
    warn "Node.js 18+ required (found $NODE_VERSION)"
    install_dep "Node.js" "node" "nodejs"
    success "Node.js installed"
  fi
else
  warn "Node.js not found"
  install_dep "Node.js" "node" "nodejs"
  success "Node.js installed"
fi

# ── Check / Install Git ───────────────────────────────
if command -v git &>/dev/null; then
  success "Git $(git --version | awk '{print $3}')"
else
  warn "Git not found"
  install_dep "Git" "git" "git"
  success "Git installed"
fi

# ── Check Docker (for Redis) ──────────────────────────
if command -v redis-cli &>/dev/null; then
  if redis-cli ping 2>/dev/null | grep -q PONG; then
    success "Redis is running"
  else
    success "Redis installed (not running — will start later)"
  fi
elif command -v docker &>/dev/null; then
  success "Docker available (will use for Redis)"
else
  warn "Neither Redis nor Docker found."
  warn "Install Docker or Redis for background task support."
  if [ "$OS" = "macos" ]; then
    warn "  brew install redis  OR  brew install --cask docker"
  else
    warn "  apt install redis-server  OR  install Docker"
  fi
fi

echo ""

# ── Clone Repository ──────────────────────────────────
if [ -d "$INSTALL_DIR/.git" ]; then
  info "nullbook already cloned at $INSTALL_DIR"
  cd "$INSTALL_DIR"
  info "Pulling latest..."
  git pull --quiet
  success "Updated to latest version"
else
  info "Cloning nullbook to $INSTALL_DIR..."
  git clone --depth 1 "$REPO_URL" "$INSTALL_DIR"
  success "Cloned to $INSTALL_DIR"
  cd "$INSTALL_DIR"
fi

echo ""

# ── Environment Setup ─────────────────────────────────
ENV_FILE="$INSTALL_DIR/.env"
if [ ! -f "$ENV_FILE" ] && [ -f "$INSTALL_DIR/.env.example" ]; then
  cp "$INSTALL_DIR/.env.example" "$ENV_FILE"
  info "Created .env from template"
fi

# ── Anthropic API Key ────────────────────────────────
echo -e "  ${BOLD}AI Setup${NC}"
echo -e "  ${DIM}nullbook uses Claude (Anthropic) for AI features.${NC}"
echo ""

# Check if .env already has a real API key
EXISTING_KEY=""
if [ -f "$ENV_FILE" ]; then
  EXISTING_KEY=$(grep -E "^ANTHROPIC_API_KEY=" "$ENV_FILE" 2>/dev/null | cut -d= -f2-)
fi

if [ -n "$EXISTING_KEY" ] && [ "$EXISTING_KEY" != "your-anthropic-api-key" ]; then
  success "Anthropic API key already configured"
elif [ -t 0 ] || [ -e /dev/tty ]; then
  echo -e "  Get an API key at: ${CYAN}https://console.anthropic.com/settings/keys${NC}"
  echo ""
  read -rp "  Anthropic API key (or press Enter to skip): " api_key < /dev/tty
  if [ -n "$api_key" ]; then
    sed -i.bak "s|^ANTHROPIC_API_KEY=.*|ANTHROPIC_API_KEY=$api_key|" "$ENV_FILE"
    rm -f "$ENV_FILE.bak"
    success "Anthropic API key saved"
  else
    warn "Skipped — add ANTHROPIC_API_KEY to .env before using chat"
  fi
else
  warn "Non-interactive shell — add ANTHROPIC_API_KEY to .env before using chat"
fi

echo ""

# ── Install Dependencies ──────────────────────────────
echo -e "  ${BOLD}Installing dependencies...${NC}"
echo ""

# Python venv
if [ ! -d "$INSTALL_DIR/backend/.venv" ]; then
  info "Creating Python virtual environment..."
  python3 -m venv "$INSTALL_DIR/backend/.venv"
fi

info "Installing Python packages..."
"$INSTALL_DIR/backend/.venv/bin/pip" install --upgrade pip --quiet 2>/dev/null
"$INSTALL_DIR/backend/.venv/bin/pip" install -r "$INSTALL_DIR/backend/requirements.txt" --quiet 2>/dev/null
success "Python packages installed"

info "Installing Node packages..."
cd "$INSTALL_DIR/frontend" && npm install --silent
success "Node packages installed"

echo ""

# ── Database Setup ────────────────────────────────────
echo -e "  ${BOLD}Setting up database...${NC}"
echo ""

cd "$INSTALL_DIR/backend"
PY="$INSTALL_DIR/backend/.venv/bin/python"

"$PY" manage.py migrate --verbosity=0 2>/dev/null
success "Migrations complete"

"$PY" manage.py seed_categories > /dev/null 2>&1
"$PY" manage.py seed_institutions > /dev/null 2>&1
success "Database seeded"

"$PY" manage.py create_local_user > /dev/null
success "Account created"

# ── Done ──────────────────────────────────────────────
echo ""
echo -e "  ────────────────────────────────────────"
echo ""
echo -e "  ${GREEN}${BOLD}nullbook is ready!${NC}"
echo ""
echo -e "  ${BOLD}Start it:${NC}"
echo -e "    cd $INSTALL_DIR && make dev"
echo ""
echo -e "  ${BOLD}Then open:${NC}"
echo -e "    http://localhost:5173"
echo ""
echo -e "  ${DIM}Edit $INSTALL_DIR/.env to configure"
echo -e "  Plaid, Gmail, and other integrations.${NC}"
echo ""
