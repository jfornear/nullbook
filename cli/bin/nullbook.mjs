#!/usr/bin/env node

import { execSync, spawn } from "child_process";
import { existsSync, mkdirSync, readFileSync, writeFileSync, copyFileSync } from "fs";
import { join, resolve } from "path";
import { homedir } from "os";
import { createInterface } from "readline";

// ── Colors ────────────────────────────────────────────
const c = {
  reset: "\x1b[0m",
  bold: "\x1b[1m",
  dim: "\x1b[2m",
  green: "\x1b[32m",
  yellow: "\x1b[33m",
  red: "\x1b[31m",
  cyan: "\x1b[36m",
};

const info = (msg) => console.log(`  ${c.cyan}[info]${c.reset}  ${msg}`);
const ok = (msg) => console.log(`  ${c.green}[ok]${c.reset}    ${msg}`);
const warn = (msg) => console.log(`  ${c.yellow}[warn]${c.reset}  ${msg}`);
const fail = (msg) => {
  console.log(`  ${c.red}[fail]${c.reset}  ${msg}`);
  process.exit(1);
};

// ── Config ────────────────────────────────────────────
const INSTALL_DIR = process.env.NULLBOOK_DIR || join(homedir(), "nullbook");
const REPO_URL = "https://github.com/jfornear/nullbook.git";

// ── Helpers ───────────────────────────────────────────
function run(cmd, opts = {}) {
  return execSync(cmd, { stdio: "pipe", encoding: "utf8", ...opts }).trim();
}

function hasCommand(cmd) {
  try {
    execSync(`command -v ${cmd}`, { stdio: "pipe" });
    return true;
  } catch {
    return false;
  }
}

function ask(question) {
  const rl = createInterface({ input: process.stdin, output: process.stdout });
  return new Promise((resolve) => {
    rl.question(`  ${question}`, (answer) => {
      rl.close();
      resolve(answer.trim());
    });
  });
}

// ── Commands ──────────────────────────────────────────
const commands = {
  async install() {
    console.log();
    console.log(`  ${c.bold}⚡ nullbook Installer${c.reset}`);
    console.log(`  ${c.dim}The AI agent for your personal finances.${c.reset}`);
    console.log();

    // Check Python
    if (hasCommand("python3")) {
      const ver = run("python3 -c 'import sys; print(f\"{sys.version_info.major}.{sys.version_info.minor}\")'");
      const minor = parseInt(ver.split(".")[1]);
      if (minor >= 11) {
        ok(`Python ${ver}`);
      } else {
        fail(`Python 3.11+ required (found ${ver}). Install it and try again.`);
      }
    } else {
      fail("Python 3 not found. Install Python 3.11+ and try again.");
    }

    // Check Node (we know it exists since we're running in it)
    const nodeVer = process.version.slice(1);
    ok(`Node.js ${nodeVer}`);

    // Check Git
    if (hasCommand("git")) {
      ok(`Git ${run("git --version").split(" ")[2]}`);
    } else {
      fail("Git not found. Install Git and try again.");
    }

    // Check Redis/Docker
    if (hasCommand("redis-cli")) {
      try {
        const pong = run("redis-cli ping 2>/dev/null");
        if (pong === "PONG") ok("Redis is running");
        else ok("Redis installed (start with: redis-server)");
      } catch {
        ok("Redis installed (start with: redis-server)");
      }
    } else if (hasCommand("docker")) {
      ok("Docker available (will use for Redis)");
    } else {
      warn("Redis/Docker not found — background tasks won't work until one is installed");
    }

    console.log();

    // Clone
    if (existsSync(join(INSTALL_DIR, ".git"))) {
      info(`nullbook already at ${INSTALL_DIR}`);
      info("Pulling latest...");
      run("git pull --quiet", { cwd: INSTALL_DIR });
      ok("Updated");
    } else {
      info(`Cloning to ${INSTALL_DIR}...`);
      run(`git clone --depth 1 ${REPO_URL} ${INSTALL_DIR}`);
      ok("Cloned");
    }

    console.log();

    // .env
    const envFile = join(INSTALL_DIR, ".env");
    const envExample = join(INSTALL_DIR, ".env.example");
    if (!existsSync(envFile) && existsSync(envExample)) {
      copyFileSync(envExample, envFile);
      info("Created .env from template");
    }

    // Anthropic API key
    console.log(`  ${c.bold}AI Setup${c.reset}`);
    console.log(`  ${c.dim}nullbook uses Claude (Anthropic) for AI features.${c.reset}`);
    console.log();

    let existingKey = "";
    if (existsSync(envFile)) {
      const envContent = readFileSync(envFile, "utf8");
      const match = envContent.match(/^ANTHROPIC_API_KEY=(.+)$/m);
      if (match) existingKey = match[1];
    }

    if (existingKey && existingKey !== "your-anthropic-api-key") {
      ok("Anthropic API key already configured");
    } else {
      console.log(`  Get an API key at: ${c.cyan}https://console.anthropic.com/settings/keys${c.reset}`);
      console.log();
      const apiKey = await ask("Anthropic API key (or press Enter to skip): ");
      if (apiKey) {
        const envContent = readFileSync(envFile, "utf8");
        writeFileSync(envFile, envContent.replace(/^ANTHROPIC_API_KEY=.*$/m, `ANTHROPIC_API_KEY=${apiKey}`));
        ok("Anthropic API key saved");
      } else {
        warn("Skipped — add ANTHROPIC_API_KEY to .env before using chat");
      }
    }

    console.log();

    // Install deps
    console.log(`  ${c.bold}Installing dependencies...${c.reset}`);
    console.log();

    info("Creating Python virtual environment...");
    if (!existsSync(join(INSTALL_DIR, "backend", ".venv"))) {
      run("python3 -m venv backend/.venv", { cwd: INSTALL_DIR });
    }

    info("Installing Python packages...");
    run("backend/.venv/bin/pip install --upgrade pip --quiet", { cwd: INSTALL_DIR });
    run("backend/.venv/bin/pip install -r backend/requirements.txt --quiet", { cwd: INSTALL_DIR });
    ok("Python packages installed");

    info("Installing Node packages...");
    run("npm install --silent", { cwd: join(INSTALL_DIR, "frontend") });
    ok("Node packages installed");

    console.log();

    // Database
    console.log(`  ${c.bold}Setting up database...${c.reset}`);
    console.log();

    const py = join(INSTALL_DIR, "backend", ".venv", "bin", "python");
    run(`${py} manage.py migrate --verbosity=0`, { cwd: join(INSTALL_DIR, "backend") });
    ok("Migrations complete");

    run(`${py} manage.py seed_categories`, { cwd: join(INSTALL_DIR, "backend") });
    run(`${py} manage.py seed_institutions`, { cwd: join(INSTALL_DIR, "backend") });
    run(`${py} manage.py create_local_user`, { cwd: join(INSTALL_DIR, "backend") });
    ok("Database seeded");

    console.log();
    console.log(`  ────────────────────────────────────────`);
    console.log();
    console.log(`  ${c.green}${c.bold}nullbook is ready!${c.reset}`);
    console.log();
    console.log(`  ${c.bold}Start it:${c.reset}`);
    console.log(`    cd ${INSTALL_DIR} && make dev`);
    console.log(`    ${c.dim}— or —${c.reset}`);
    console.log(`    npx nullbook start`);
    console.log();
    console.log(`  ${c.bold}Then open:${c.reset}  http://localhost:5173`);
    console.log(`  ${c.bold}Log in:${c.reset}     credentials are in your .env file`);
    console.log();
  },

  start() {
    if (!existsSync(INSTALL_DIR)) {
      fail(`nullbook not installed. Run: npx nullbook install`);
    }

    console.log();
    console.log(`  ${c.bold}⚡ Starting nullbook...${c.reset}`);
    console.log();

    const child = spawn("make", ["dev"], {
      cwd: INSTALL_DIR,
      stdio: "inherit",
      shell: true,
    });

    child.on("close", (code) => process.exit(code || 0));
  },

  stop() {
    info("Stopping nullbook services...");
    try {
      // Kill backend
      run("lsof -ti :8001 | xargs kill -9 2>/dev/null || true");
      // Kill frontend
      run("lsof -ti :5173 | xargs kill -9 2>/dev/null || true");
      ok("Services stopped");
    } catch {
      warn("No running services found");
    }
  },

  status() {
    console.log();
    console.log(`  ${c.bold}nullbook Status${c.reset}`);
    console.log();

    // Install dir
    if (existsSync(INSTALL_DIR)) {
      ok(`Installed at ${INSTALL_DIR}`);
    } else {
      warn("Not installed");
      return;
    }

    // Backend
    try {
      run("lsof -ti :8001 >/dev/null 2>&1");
      ok("Backend running on :8001");
    } catch {
      warn("Backend not running");
    }

    // Frontend
    try {
      run("lsof -ti :5173 >/dev/null 2>&1");
      ok("Frontend running on :5173");
    } catch {
      warn("Frontend not running");
    }

    // Redis
    try {
      const pong = run("redis-cli ping 2>/dev/null");
      if (pong === "PONG") ok("Redis connected");
      else warn("Redis not responding");
    } catch {
      warn("Redis not reachable");
    }

    // AI check
    const installEnv = join(INSTALL_DIR, ".env");
    if (existsSync(installEnv)) {
      const envContent = readFileSync(installEnv, "utf8");
      const match = envContent.match(/^ANTHROPIC_API_KEY=(.+)$/m);
      const key = match ? match[1] : "";
      if (key && key !== "your-anthropic-api-key") {
        ok("Anthropic API key configured");
      } else {
        warn("Anthropic API key not set — add ANTHROPIC_API_KEY to .env");
      }
    }

    console.log();
  },

  update() {
    if (!existsSync(INSTALL_DIR)) {
      fail(`nullbook not installed. Run: npx nullbook install`);
    }

    console.log();
    console.log(`  ${c.bold}⚡ Updating nullbook...${c.reset}`);
    console.log();

    run("git pull --quiet", { cwd: INSTALL_DIR });
    ok("Code updated");

    info("Updating Python packages...");
    run("backend/.venv/bin/pip install -r backend/requirements.txt --quiet", { cwd: INSTALL_DIR });
    ok("Python packages updated");

    info("Updating Node packages...");
    run("npm install --silent", { cwd: join(INSTALL_DIR, "frontend") });
    ok("Node packages updated");

    info("Running migrations...");
    const py = join(INSTALL_DIR, "backend", ".venv", "bin", "python");
    run(`${py} manage.py migrate --verbosity=0`, { cwd: join(INSTALL_DIR, "backend") });
    ok("Migrations complete");

    console.log();
    console.log(`  ${c.green}${c.bold}Updated!${c.reset} Run ${c.cyan}npx nullbook start${c.reset} to launch.`);
    console.log();
  },

  help() {
    console.log();
    console.log(`  ${c.bold}⚡ nullbook${c.reset} — The AI agent for your personal finances.`);
    console.log();
    console.log(`  ${c.bold}Usage:${c.reset}`);
    console.log(`    npx nullbook ${c.dim}<command>${c.reset}`);
    console.log();
    console.log(`  ${c.bold}Commands:${c.reset}`);
    console.log(`    install   Clone, configure, and set up nullbook`);
    console.log(`    start     Start all services (backend, frontend, Redis)`);
    console.log(`    stop      Stop all running services`);
    console.log(`    status    Check if services are running`);
    console.log(`    update    Pull latest code and update dependencies`);
    console.log(`    help      Show this help message`);
    console.log();
    console.log(`  ${c.bold}Options:${c.reset}`);
    console.log(`    NULLBOOK_DIR=~/my-dir   Custom install directory`);
    console.log();
    console.log(`  ${c.dim}https://github.com/jfornear/nullbook${c.reset}`);
    console.log();
  },
};

// ── Main ──────────────────────────────────────────────
const cmd = process.argv[2] || "install";

if (commands[cmd]) {
  const result = commands[cmd]();
  if (result instanceof Promise) result.catch((e) => fail(e.message));
} else {
  console.log(`  Unknown command: ${cmd}`);
  commands.help();
}
