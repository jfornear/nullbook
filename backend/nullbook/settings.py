import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR.parent / ".env")

_default_key = "dev-insecure-key-change-in-production"
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", _default_key)

DEBUG = os.environ.get("DJANGO_DEBUG", "True").lower() in ("true", "1", "yes")

if not DEBUG and SECRET_KEY == _default_key:
    raise RuntimeError(
        "DJANGO_SECRET_KEY must be set to a unique, unpredictable value in production. "
        "Generate one with: python -c \"from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())\""
    )

ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third party
    "rest_framework",
    "corsheaders",
    "django_filters",
    # Local apps
    "core",
    "accounts",
    "transactions",
    "portfolio",
    "taxes",
    "news",
    "imports",
    "chat",
    "integrations",
    "email_sync",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "nullbook.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "nullbook.wsgi.application"

# Database — SQLite by default, set DATABASE_URL for Postgres
DATABASE_URL = os.environ.get("DATABASE_URL")
if DATABASE_URL:
    import re
    m = re.match(r"postgres(?:ql)?://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)", DATABASE_URL)
    if m:
        DATABASES = {
            "default": {
                "ENGINE": "django.db.backends.postgresql",
                "USER": m.group(1),
                "PASSWORD": m.group(2),
                "HOST": m.group(3),
                "PORT": m.group(4),
                "NAME": m.group(5),
            }
        }
    else:
        raise RuntimeError(
            "DATABASE_URL is set but could not be parsed. "
            "Expected format: postgres://USER:PASSWORD@HOST:PORT/DBNAME"
        )
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

AUTH_PASSWORD_VALIDATORS = (
    []
    if DEBUG
    else [
        {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
        {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
        {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
        {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
    ]
)

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Upload limits
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10 MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10 MB
DATA_UPLOAD_MAX_NUMBER_FIELDS = 1000

# DRF
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 50,
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "20/minute",
        "user": "200/minute",
    },
}

# CORS
CORS_ALLOW_ALL_ORIGINS = os.environ.get("CORS_ALLOW_ALL", "").lower() in ("true", "1", "yes")
if CORS_ALLOW_ALL_ORIGINS and not DEBUG:
    raise RuntimeError(
        "CORS_ALLOW_ALL=true is not allowed in production (with credentials enabled, "
        "this allows any website to make authenticated requests). "
        "Set CORS_ALLOWED_ORIGINS to specific origins instead."
    )
if not CORS_ALLOW_ALL_ORIGINS:
    _vite_cors = ",".join(
        f"http://{host}:{port}"
        for host in ("localhost", "127.0.0.1")
        for port in range(5173, 5190)
    )
    _default_cors = f"{_vite_cors},http://localhost:8001"
    CORS_ALLOWED_ORIGINS = os.environ.get("CORS_ALLOWED_ORIGINS", _default_cors).split(",")
CORS_ALLOW_CREDENTIALS = True

# CSRF — include a range of Vite dev ports (auto-increments when 5173 is busy)
_vite_origins = ",".join(
    f"http://{host}:{port}"
    for host in ("localhost", "127.0.0.1")
    for port in range(5173, 5190)
)
_default_csrf = f"{_vite_origins},http://localhost:8001"
CSRF_TRUSTED_ORIGINS = os.environ.get("CSRF_TRUSTED_ORIGINS", _default_csrf).split(",")
CSRF_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_DOMAIN = None
SESSION_COOKIE_DOMAIN = None

# Production security — enabled when DEBUG is False
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_HSTS_SECONDS = int(os.environ.get("SECURE_HSTS_SECONDS", "31536000"))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = os.environ.get("SECURE_HSTS_PRELOAD", "false").lower() == "true"
    SECURE_SSL_REDIRECT = os.environ.get("SECURE_SSL_REDIRECT", "false").lower() == "true"
    SECURE_BROWSER_XSS_FILTER = True
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True
    X_FRAME_OPTIONS = "DENY"

# Celery
CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_RESULT_EXPIRES = 3600
CELERY_TASK_TIME_LIMIT = 600
CELERY_TASK_SOFT_TIME_LIMIT = 540

# Celery Beat Schedule
from celery.schedules import crontab  # noqa: E402

CELERY_BEAT_SCHEDULE = {
    "sync-plaid-transactions": {
        "task": "integrations.tasks.sync_all_plaid_items",
        "schedule": crontab(minute=0, hour="*/4"),  # Every 4 hours
    },
    "scan-email-receipts": {
        "task": "email_sync.tasks.scan_email_for_receipts",
        "schedule": crontab(minute=0, hour="*/2"),  # Every 2 hours
    },
    "detect-subscriptions": {
        "task": "transactions.tasks.detect_subscriptions",
        "schedule": crontab(minute=0, hour=2),  # Daily at 2 AM
    },
    "auto-categorize": {
        "task": "transactions.tasks.auto_categorize_transactions",
        "schedule": crontab(minute=30, hour=2),  # Daily at 2:30 AM
    },
    "auto-match-receipts": {
        "task": "taxes.tasks.auto_match_receipts",
        "schedule": crontab(minute=0, hour=3),  # Daily at 3 AM
    },
    "update-security-prices": {
        "task": "portfolio.tasks.update_security_prices",
        "schedule": crontab(minute=0, hour=18),  # Daily at 6 PM (after market close)
    },
    "generate-daily-alerts": {
        "task": "core.tasks.generate_daily_alerts",
        "schedule": crontab(minute=0, hour=8),  # Daily at 8 AM
    },
    "fetch-news": {
        "task": "news.tasks.fetch_news_articles",
        "schedule": crontab(minute=0, hour="*/6"),  # Every 6 hours
    },
    "quarterly-tax-reminder": {
        "task": "taxes.tasks.quarterly_tax_reminder",
        "schedule": crontab(minute=0, hour=9, day_of_month="8-15"),  # Week before quarterly deadlines
    },
    "auto-detect-deductions": {
        "task": "taxes.tasks.auto_detect_deductions",
        "schedule": crontab(minute=0, hour=4, day_of_week=0),  # Weekly on Sunday at 4 AM
    },
    "weekly-summary": {
        "task": "core.tasks.generate_weekly_summary",
        "schedule": crontab(minute=0, hour=19, day_of_week=0),  # Sunday at 7 PM
    },
}

# Plaid (optional — bank account syncing)
PLAID_CLIENT_ID = os.environ.get("PLAID_CLIENT_ID", "")
PLAID_SECRET = os.environ.get("PLAID_SECRET", "")
PLAID_ENV = os.environ.get("PLAID_ENV", "sandbox")  # sandbox, production
PLAID_CLIENT_NAME = "nullbook"

# Email sending (optional — subscription cancellation)
SMTP_HOST = os.environ.get("SMTP_HOST", "")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")

# LLM provider: 'anthropic' (default), 'openai', or 'ollama' (local, opt-in)
LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "anthropic")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
CHAT_MODEL = os.environ.get("CHAT_MODEL", "claude-opus-4-6")
CHAT_MODEL_FAST = os.environ.get("CHAT_MODEL_FAST", "claude-haiku-4-5-20251001")
VISION_MODEL = os.environ.get("VISION_MODEL", "claude-sonnet-4-6")
# OpenAI (only used when LLM_PROVIDER=openai)
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
# Ollama (only used when LLM_PROVIDER=ollama)
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434/v1")

# Logging
LOG_DIR = BASE_DIR.parent / "logs"
try:
    LOG_DIR.mkdir(exist_ok=True)
except OSError:
    # Fall back to a writable location (e.g. inside the app dir in Docker)
    LOG_DIR = BASE_DIR / "logs"
    LOG_DIR.mkdir(exist_ok=True)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{asctime} {levelname} {name} {message}",
            "style": "{",
        },
        "json": {
            "format": "{asctime} {levelname} {name} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose" if DEBUG else "json",
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": str(LOG_DIR / "nullbook.log"),
            "maxBytes": 10 * 1024 * 1024,  # 10 MB
            "backupCount": 5,
            "formatter": "json",
        },
    },
    "root": {
        "handlers": ["console", "file"],
        "level": "INFO",
    },
    "loggers": {
        "django": {"level": "WARNING"},
        "chat": {"level": "DEBUG" if DEBUG else "INFO"},
        "transactions": {"level": "INFO"},
        "core": {"level": "INFO"},
    },
}
