# Changelog

## 0.3.0

- Add OpenAI as third LLM provider (`LLM_PROVIDER=openai`)
- Support switching between Anthropic, OpenAI, and Ollama via .env config

## 0.2.0

- Switch default LLM from Ollama to Anthropic/Claude (Opus 4.6 for chat, Haiku for categorization, Sonnet for vision)
- Ollama remains available as opt-in alternative (`LLM_PROVIDER=ollama`)
- Setup scripts now prompt for Anthropic API key instead of installing Ollama
- Remove automatic Ollama installation and model pulling from setup flow

## 0.1.0

Initial release.

- AI chat agent powered by Claude for natural language finance queries (Ollama available as local alternative)
- Bank account syncing via Plaid
- AI-powered transaction categorization
- Email receipt scanning via IMAP (Gmail, Outlook, Yahoo, etc.)
- Subscription detection and cancellation drafts
- Tax preparation with deduction tracking and Schedule C generation
- Portfolio tracking with real-time stock prices
- Data import from CSV, OFX, and QIF files
- Financial news watchlists
- Local-first architecture with SQLite
- Self-hosted — all data stays on your machine
