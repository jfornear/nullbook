# Integrations Setup Guide

All integrations are **opt-in**. nullbook works without any of them — you can always add transactions manually or import files. Enable only what you need.

| Integration                                      | Setup time | What you need                       |
| ------------------------------------------------ | ---------- | ----------------------------------- |
| [AI Chat](#ai-chat)                              | 2 min      | API key (or Ollama for fully local) |
| [Gmail Receipts](#gmail-receipt-scanning)        | 2 min      | Gmail App Password                  |
| [Bank Syncing (Plaid)](#bank-syncing-plaid)      | 5 min      | Free Plaid developer account        |
| [Bank File Import](#bank-file-import)            | 0 min      | Nothing — just drag and drop        |
| [Cancellation Emails](#cancellation-emails-smtp) | 2 min      | Email provider SMTP credentials     |

---

## AI Chat

nullbook's AI agent can use Anthropic (Claude), OpenAI, or Ollama (fully local).

### Option A: Anthropic (default)

1. Go to [console.anthropic.com/settings/keys](https://console.anthropic.com/settings/keys)
2. Create an API key
3. Add to `.env`:

```env
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...
```

### Option B: OpenAI

1. Go to [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
2. Create an API key
3. Add to `.env`:

```env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
```

### Option C: Ollama (fully local, no data leaves your machine)

1. Install [Ollama](https://ollama.com)
2. Pull a model: `ollama pull qwen3:8b`
3. Add to `.env`:

```env
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434/v1
CHAT_MODEL=qwen3:8b
CHAT_MODEL_FAST=qwen3:4b
VISION_MODEL=qwen3:8b
```

---

## Gmail Receipt Scanning

nullbook connects to your Gmail over IMAP to find purchase confirmations, digital receipts, and bills. No Google Cloud project or OAuth app required — just a Gmail App Password.

### Step 1: Enable 2-Step Verification

You need 2FA enabled on your Google account to use App Passwords.

1. Go to [myaccount.google.com/security](https://myaccount.google.com/security)
2. Under "How you sign in to Google", click **2-Step Verification**
3. Follow the prompts to enable it (if not already on)

### Step 2: Generate an App Password

1. Go to [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
2. Enter a name (e.g. "nullbook")
3. Click **Create**
4. Copy the 16-character password (spaces don't matter)

### Step 3: Add to your `.env`

```env
IMAP_HOST=imap.gmail.com
IMAP_PORT=993
IMAP_USER=you@gmail.com
IMAP_PASSWORD=abcd efgh ijkl mnop
```

### Other email providers

Any IMAP-compatible provider works. Use your provider's IMAP settings:

| Provider        | IMAP Host               | Port |
| --------------- | ----------------------- | ---- |
| Gmail           | `imap.gmail.com`        | 993  |
| Outlook/Hotmail | `outlook.office365.com` | 993  |
| Yahoo           | `imap.mail.yahoo.com`   | 993  |
| Fastmail        | `imap.fastmail.com`     | 993  |
| iCloud          | `imap.mail.me.com`      | 993  |

For non-Gmail providers, use your regular email password (or an app password if your provider supports them).

---

## Bank Syncing (Plaid)

Plaid connects to your bank to automatically import transactions. Each user creates their own free Plaid developer account — no hosted service needed.

### Step 1: Create a Plaid account

1. Go to [dashboard.plaid.com/signup](https://dashboard.plaid.com/signup)
2. Sign up for a free account
3. You'll start in **Sandbox** mode (test data, no real banks)

### Step 2: Get your API keys

1. Go to [dashboard.plaid.com/developers/keys](https://dashboard.plaid.com/developers/keys)
2. Copy your **Client ID** and **Sandbox Secret**

### Step 3: Add to your `.env`

```env
PLAID_CLIENT_ID=your-client-id
PLAID_SECRET=your-sandbox-secret
PLAID_ENV=sandbox
```

### Connecting real bank accounts

To connect real banks, you need to upgrade from Sandbox:

1. In the Plaid dashboard, apply for **Development** access (free, up to 100 linked accounts)
2. Once approved, copy your **Development Secret** from the keys page
3. Update `.env`:

```env
PLAID_SECRET=your-development-secret
PLAID_ENV=development
```

> **Note:** Plaid Development is free for up to 100 linked accounts. Production access requires a paid plan.

---

## Bank File Import

No setup required. nullbook supports importing transaction files directly:

- **CSV** — most banks offer CSV export
- **OFX** (Open Financial Exchange) — standard format supported by most banks
- **QIF** (Quicken Interchange Format) — legacy format, still widely supported

To import: go to **Accounts** in nullbook, click **Import**, and select your file.

---

## Cancellation Emails (SMTP)

nullbook can send subscription cancellation emails on your behalf. You provide SMTP credentials for your email account.

### Gmail SMTP

Use the same App Password from the Gmail setup above:

```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=you@gmail.com
SMTP_PASSWORD=abcd efgh ijkl mnop
```

### Other providers

| Provider        | SMTP Host             | Port |
| --------------- | --------------------- | ---- |
| Gmail           | `smtp.gmail.com`      | 587  |
| Outlook/Hotmail | `smtp.office365.com`  | 587  |
| Yahoo           | `smtp.mail.yahoo.com` | 587  |
| Fastmail        | `smtp.fastmail.com`   | 587  |
| iCloud          | `smtp.mail.me.com`    | 587  |

---

## Troubleshooting

### Gmail: "Application-specific password required"

You need to generate an App Password. Regular Gmail passwords won't work with IMAP when 2FA is enabled. See [Step 2 above](#step-2-generate-an-app-password).

### Gmail: "Web login required" or "Please log in via your web browser"

Go to [accounts.google.com/DisplayUnlockCaptcha](https://accounts.google.com/DisplayUnlockCaptcha) and click "Allow", then try again.

### Plaid: Sandbox vs Development

In Sandbox mode, you connect to test institutions with test credentials (user: `user_good`, password: `pass_good`). Switch to Development to connect real banks.

### Plaid: "Access denied" or "Invalid credentials"

Make sure `PLAID_SECRET` matches the environment set in `PLAID_ENV`. Sandbox and Development use different secrets.
