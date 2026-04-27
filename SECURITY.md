# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in nullbook, please report it responsibly by opening a GitHub issue or contacting the maintainer.

Please include:

- A description of the vulnerability
- Steps to reproduce
- Potential impact

We will acknowledge receipt within 48 hours and aim to provide a fix within 7 days for critical issues.

## Scope

nullbook is designed for **single-user, self-hosted** use on a trusted machine. The threat model assumes:

- The machine running nullbook is not shared with untrusted users
- Network access is restricted to localhost (or behind a reverse proxy with TLS)
- The `.env` file and database are protected by filesystem permissions

## Security Measures

- **Encryption at rest**: Plaid access tokens and IMAP credentials are encrypted using Fernet (AES-128-CBC), keyed from `DJANGO_SECRET_KEY`
- **Session authentication** with CSRF protection on all state-changing endpoints
- **No default credentials in production**: `DJANGO_SECRET_KEY` and `NULLBOOK_ADMIN_PASSWORD` are required when `DEBUG=False`
- **Upload limits**: 10 MB max file size, 1000 max form fields
- **Rate limiting**: Anonymous (20/min) and authenticated (200/min) request throttling
- **Admin disabled in production**: Django admin is only available when `DEBUG=True`
- **Security headers**: HSTS, X-Frame-Options DENY, X-Content-Type-Options nosniff (production)
- **Read-only shared data**: Categories, institutions, securities, and news articles cannot be modified via API

## Supported Versions

| Version | Supported |
| ------- | --------- |
| Latest  | Yes       |

## Known Limitations

- SQLite does not support concurrent writes well. For multi-process deployments (backend + Celery), use PostgreSQL via `DATABASE_URL`.
- The app binds to localhost by default. If exposed to a network, use a reverse proxy with TLS.
