"""Validate the nullbook setup and print a status report."""

from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Check that nullbook is properly configured"

    def handle(self, *args, **options):
        self.stdout.write("\nnullbook setup check\n" + "=" * 40)
        all_ok = True

        # Database
        try:
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            self._ok("Database")
        except Exception as e:
            self._fail("Database", str(e))
            all_ok = False

        # Redis
        try:
            from nullbook.celery_app import app as celery_app
            conn = celery_app.connection()
            conn.ensure_connection(max_retries=1, timeout=2)
            conn.close()
            self._ok("Redis")
        except Exception:
            self._warn("Redis (optional for dev, required for background tasks)")

        # LLM provider
        llm_provider = getattr(settings, "LLM_PROVIDER", "anthropic")
        if llm_provider == "ollama":
            try:
                import urllib.request
                ollama_base = getattr(settings, "OLLAMA_BASE_URL", "http://localhost:11434/v1")
                ollama_host = ollama_base.replace("/v1", "")
                req = urllib.request.Request(f"{ollama_host}/api/tags", method="GET")
                with urllib.request.urlopen(req, timeout=3) as resp:
                    if resp.status == 200:
                        self._ok(f"Ollama running ({llm_provider})")
                    else:
                        self._warn("Ollama not responding")
            except Exception:
                self._warn("Ollama not running (chat agent disabled). Start with: ollama serve")
        elif llm_provider == "openai":
            if getattr(settings, "OPENAI_API_KEY", ""):
                self._ok("OpenAI API key configured")
            else:
                self._warn("OpenAI API key not set (chat agent disabled). Add OPENAI_API_KEY to .env")
        else:
            if settings.ANTHROPIC_API_KEY:
                self._ok("Anthropic API key configured")
            else:
                self._warn("Anthropic API key not set (chat agent disabled). Add ANTHROPIC_API_KEY to .env")

        # Plaid
        if settings.PLAID_CLIENT_ID:
            self._ok("Plaid credentials")
        else:
            self._info("Plaid not configured (bank syncing disabled)")

        # Email scanning
        from email_sync.models import EmailAccount
        if EmailAccount.objects.exists():
            self._ok("Email account connected")
        else:
            self._info("No email accounts connected (connect via Settings > Email)")

        # SMTP
        if settings.SMTP_HOST:
            self._ok("SMTP configured")
        else:
            self._info("SMTP not configured (cancellation emails disabled)")

        # Secret key
        if settings.SECRET_KEY == "dev-insecure-key-change-in-production":
            if not settings.DEBUG:
                self._fail("SECRET_KEY", "Using default key in production!")
                all_ok = False
            else:
                self._warn("SECRET_KEY is default (ok for dev)")
        else:
            self._ok("SECRET_KEY is set")

        self.stdout.write("\n" + "=" * 40)
        if all_ok:
            self.stdout.write(self.style.SUCCESS("All checks passed!"))
        else:
            self.stdout.write(self.style.ERROR("Some checks failed."))

    def _ok(self, label):
        self.stdout.write(self.style.SUCCESS(f"  [OK] {label}"))

    def _fail(self, label, detail=""):
        msg = f"  [FAIL] {label}"
        if detail:
            msg += f" — {detail}"
        self.stdout.write(self.style.ERROR(msg))

    def _warn(self, label):
        self.stdout.write(self.style.WARNING(f"  [WARN] {label}"))

    def _info(self, label):
        self.stdout.write(f"  [INFO] {label}")
