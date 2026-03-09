import shutil
from pathlib import Path

from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Interactive setup wizard for nullbook"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.backend_dir = Path(__file__).resolve().parent.parent.parent.parent
        self.project_root = self.backend_dir.parent
        self.env_file = self.project_root / ".env"
        self.env_example = self.project_root / ".env.example"

    def handle(self, *args, **options):
        self.stdout.write("")
        self.stdout.write(self.style.MIGRATE_HEADING("nullbook Setup Wizard"))
        self.stdout.write("=" * 40)
        self.stdout.write("")

        self._setup_env_file()
        self._prompt_api_keys()
        self._run_migrations()
        self._seed_data()
        self._create_user()

        self.stdout.write("")
        self.stdout.write("=" * 40)
        self.stdout.write(self.style.SUCCESS("Setup complete!"))
        self.stdout.write("")
        self.stdout.write("To start the dev servers:")
        self.stdout.write("  make dev")
        self.stdout.write("")
        self.stdout.write("Login credentials are in your .env file.")
        self.stdout.write("")

    def _setup_env_file(self):
        """Create .env from .env.example if it doesn't exist."""
        self.stdout.write(self.style.MIGRATE_HEADING("Environment Configuration"))
        self.stdout.write("")

        if self.env_file.exists():
            self.stdout.write(self.style.SUCCESS("  .env file already exists, keeping current values."))
        elif self.env_example.exists():
            shutil.copy2(self.env_example, self.env_file)
            self.stdout.write(self.style.SUCCESS("  Created .env from .env.example"))
        else:
            self.stdout.write(self.style.WARNING(
                "  .env.example not found. Create a .env file manually."
            ))

    def _read_env_value(self, key):
        """Read a value from the .env file."""
        if not self.env_file.exists():
            return ""
        with open(self.env_file) as f:
            for line in f:
                line = line.strip()
                if line.startswith(f"{key}="):
                    return line.split("=", 1)[1]
        return ""

    def _write_env_value(self, key, value):
        """Update a key in the .env file."""
        if not self.env_file.exists():
            return

        lines = self.env_file.read_text().splitlines()
        updated = False
        for i, line in enumerate(lines):
            if line.strip().startswith(f"{key}="):
                lines[i] = f"{key}={value}"
                updated = True
                break

        if not updated:
            lines.append(f"{key}={value}")

        self.env_file.write_text("\n".join(lines) + "\n")

    def _prompt_api_keys(self):
        """Prompt for LLM setup and optional API keys."""
        self.stdout.write("")
        self.stdout.write(self.style.MIGRATE_HEADING("AI Setup"))
        self.stdout.write("")

        # Check LLM provider
        provider = self._read_env_value("LLM_PROVIDER") or "anthropic"
        if provider == "ollama":
            import shutil as _shutil
            if _shutil.which("ollama"):
                self.stdout.write(self.style.SUCCESS("  Ollama is installed."))
            else:
                self.stdout.write("  Ollama is required when LLM_PROVIDER=ollama.")
                self.stdout.write("  Install from: https://ollama.com/download")
                self.stdout.write("  Then run: make ollama-setup")
        elif provider == "openai":
            current = self._read_env_value("OPENAI_API_KEY")
            if current and current != "your-openai-api-key":
                self.stdout.write(self.style.SUCCESS("  OpenAI API key already configured."))
            else:
                self.stdout.write("  An OpenAI API key is required for the AI chat agent.")
                self.stdout.write("  Get one at: https://platform.openai.com/api-keys")
                self.stdout.write("")
                while True:
                    key = input("  OpenAI API key: ").strip()
                    if key:
                        self._write_env_value("OPENAI_API_KEY", key)
                        self.stdout.write(self.style.SUCCESS("  OpenAI API key saved."))
                        break
                    else:
                        self.stdout.write(self.style.WARNING(
                            "  This key is required. Please enter a valid API key."
                        ))
        else:
            current = self._read_env_value("ANTHROPIC_API_KEY")
            if current and current != "your-anthropic-api-key":
                self.stdout.write(self.style.SUCCESS("  Anthropic API key already configured."))
            else:
                self.stdout.write("  An Anthropic API key is required for the AI chat agent.")
                self.stdout.write("  Get one at: https://console.anthropic.com/settings/keys")
                self.stdout.write("")
                while True:
                    key = input("  Anthropic API key: ").strip()
                    if key:
                        self._write_env_value("ANTHROPIC_API_KEY", key)
                        self.stdout.write(self.style.SUCCESS("  Anthropic API key saved."))
                        break
                    else:
                        self.stdout.write(self.style.WARNING(
                            "  This key is required. Please enter a valid API key."
                        ))

        self.stdout.write("")

        # Plaid (optional)
        configure_plaid = input("  Configure Plaid for bank syncing? (y/N): ").strip().lower()
        if configure_plaid == "y":
            client_id = input("    Plaid Client ID: ").strip()
            secret = input("    Plaid Secret: ").strip()
            env = input("    Plaid Environment (sandbox/development/production) [sandbox]: ").strip()
            env = env or "sandbox"

            self._write_env_value("PLAID_CLIENT_ID", client_id)
            self._write_env_value("PLAID_SECRET", secret)
            self._write_env_value("PLAID_ENV", env)
            self.stdout.write(self.style.SUCCESS("  Plaid credentials saved."))
        else:
            self.stdout.write("  Skipping Plaid (add credentials to .env later).")

        self.stdout.write("")

        # Email scanning (optional)
        self.stdout.write("  Email scanning uses IMAP — connect your email in Settings after setup.")
        self.stdout.write("  For Gmail, generate an App Password at myaccount.google.com/apppasswords")

    def _run_migrations(self):
        """Run Django migrations."""
        self.stdout.write("")
        self.stdout.write(self.style.MIGRATE_HEADING("Database Setup"))
        self.stdout.write("")
        self.stdout.write("  Running migrations...")
        call_command("migrate", verbosity=0)
        self.stdout.write(self.style.SUCCESS("  Migrations complete."))

    def _seed_data(self):
        """Seed categories and institutions."""
        self.stdout.write("")
        self.stdout.write("  Seeding categories...")
        call_command("seed_categories")
        self.stdout.write(self.style.SUCCESS("  Categories seeded."))

        self.stdout.write("  Seeding institutions...")
        call_command("seed_institutions")
        self.stdout.write(self.style.SUCCESS("  Institutions seeded."))

    def _create_user(self):
        """Create the local dev user."""
        self.stdout.write("")
        self.stdout.write("  Creating local dev user...")
        call_command("create_local_user")
        self.stdout.write(self.style.SUCCESS("  Local user ready."))
