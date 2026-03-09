"""Tool functions wrapping existing querysets for the chat agent."""

import logging
from collections import defaultdict
from datetime import timedelta
from decimal import Decimal

from django.db.models import Sum
from django.utils import timezone

from accounts.models import Account
from news.models import NewsArticle
from portfolio.models import Holding
from taxes.models import DeductibleExpense, Receipt, TaxYear
from transactions.models import Transaction

logger = logging.getLogger(__name__)


# ---- Tool definitions for the LLM ----

TOOL_DEFINITIONS = [
    {
        "name": "get_accounts",
        "description": "Get all of the user's financial accounts (checking, savings, credit cards, investment, etc.) with balances.",
        "input_schema": {
            "type": "object",
            "properties": {
                "account_type": {
                    "type": "string",
                    "description": "Optional filter: checking, savings, credit_card, investment, loan, mortgage, cash, other",
                },
            },
            "required": [],
        },
    },
    {
        "name": "query_transactions",
        "description": "Query the user's transactions with optional filters for date range, account, category, type, and search text.",
        "input_schema": {
            "type": "object",
            "properties": {
                "date_from": {
                    "type": "string",
                    "description": "Start date (YYYY-MM-DD)",
                },
                "date_to": {
                    "type": "string",
                    "description": "End date (YYYY-MM-DD)",
                },
                "account_id": {
                    "type": "integer",
                    "description": "Filter by account ID",
                },
                "transaction_type": {
                    "type": "string",
                    "description": "Filter: income, expense, or transfer",
                },
                "search": {
                    "type": "string",
                    "description": "Search in transaction descriptions",
                },
                "limit": {
                    "type": "integer",
                    "description": "Max results to return (default 20)",
                },
            },
            "required": [],
        },
    },
    {
        "name": "get_spending_summary",
        "description": "Get spending totals grouped by category for a date range.",
        "input_schema": {
            "type": "object",
            "properties": {
                "date_from": {
                    "type": "string",
                    "description": "Start date (YYYY-MM-DD). Defaults to 30 days ago.",
                },
                "date_to": {
                    "type": "string",
                    "description": "End date (YYYY-MM-DD). Defaults to today.",
                },
            },
            "required": [],
        },
    },
    {
        "name": "get_dashboard_summary",
        "description": "Get a high-level financial dashboard: net worth, account count, recent transaction count, portfolio value.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "get_portfolio_holdings",
        "description": "Get all of the user's investment holdings with symbols, shares, and cost basis.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "get_portfolio_allocation",
        "description": "Get portfolio allocation breakdown by security type (stock, ETF, crypto, etc.).",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "get_news_articles",
        "description": "Get recent financial news articles from the user's configured sources.",
        "input_schema": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Max articles to return (default 10)",
                },
            },
            "required": [],
        },
    },
    {
        "name": "search_security",
        "description": "Look up a stock, ETF, or crypto by ticker symbol. Returns current price and info.",
        "input_schema": {
            "type": "object",
            "properties": {
                "symbol": {
                    "type": "string",
                    "description": "Ticker symbol (e.g. AAPL, BTC-USD)",
                },
            },
            "required": ["symbol"],
        },
    },
    {
        "name": "get_tax_years",
        "description": "Get the user's tax years with filing status, document counts, and deduction totals.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    # --- Phase 1: Receipt & Expense tools ---
    {
        "name": "get_receipts",
        "description": "Get the user's uploaded receipts with OCR status, merchant, date, and amounts. Filter by status, date range, or merchant.",
        "input_schema": {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "description": "Filter by status: pending, processing, completed, failed",
                },
                "date_from": {
                    "type": "string",
                    "description": "Filter receipts from this date (YYYY-MM-DD)",
                },
                "date_to": {
                    "type": "string",
                    "description": "Filter receipts until this date (YYYY-MM-DD)",
                },
                "merchant": {
                    "type": "string",
                    "description": "Search by merchant name",
                },
            },
            "required": [],
        },
    },
    {
        "name": "create_expense_from_receipt",
        "description": "Create a DeductibleExpense from a processed receipt. Links the receipt to a tax year as a deduction.",
        "input_schema": {
            "type": "object",
            "properties": {
                "receipt_id": {
                    "type": "integer",
                    "description": "The ID of the processed receipt",
                },
                "tax_year": {
                    "type": "integer",
                    "description": "The tax year (e.g. 2025)",
                },
                "deduction_type": {
                    "type": "string",
                    "description": "Deduction category: business, medical, charitable, education, home_office, vehicle, insurance, retirement, other",
                },
            },
            "required": ["receipt_id", "tax_year"],
        },
    },
    {
        "name": "generate_expense_report",
        "description": "Generate an expense/deduction report for a tax year, grouped by category with totals.",
        "input_schema": {
            "type": "object",
            "properties": {
                "tax_year": {
                    "type": "integer",
                    "description": "The tax year (e.g. 2025)",
                },
            },
            "required": ["tax_year"],
        },
    },
    # --- Phase 2: Tax Estimation tools ---
    {
        "name": "estimate_taxes",
        "description": "Calculate a detailed federal tax estimate for a given tax year based on the user's documents (W-2, 1099s) and deductions. Shows bracket breakdown, SE tax, QBI, AMT, and refund/amount owed.",
        "input_schema": {
            "type": "object",
            "properties": {
                "tax_year": {
                    "type": "integer",
                    "description": "The tax year to estimate (e.g. 2025)",
                },
            },
            "required": ["tax_year"],
        },
    },
    {
        "name": "compare_filing_statuses",
        "description": "Compare tax estimates across different filing statuses to find the optimal one for the user.",
        "input_schema": {
            "type": "object",
            "properties": {
                "tax_year": {
                    "type": "integer",
                    "description": "The tax year to compare (e.g. 2025)",
                },
            },
            "required": ["tax_year"],
        },
    },
    # --- Phase 3: Tax Prep Assistant tools ---
    {
        "name": "scan_transactions_for_deductions",
        "description": "Scan the user's transactions for a tax year to find potentially deductible expenses that haven't been claimed yet.",
        "input_schema": {
            "type": "object",
            "properties": {
                "tax_year": {
                    "type": "integer",
                    "description": "The tax year to scan (e.g. 2025)",
                },
            },
            "required": ["tax_year"],
        },
    },
    {
        "name": "create_deduction_from_transactions",
        "description": "Create a DeductibleExpense by aggregating selected transactions into a single deduction entry.",
        "input_schema": {
            "type": "object",
            "properties": {
                "transaction_ids": {
                    "type": "array",
                    "items": {"type": "integer"},
                    "description": "List of transaction IDs to aggregate",
                },
                "tax_year": {
                    "type": "integer",
                    "description": "The tax year (e.g. 2025)",
                },
                "deduction_type": {
                    "type": "string",
                    "description": "Deduction category: business, medical, charitable, education, home_office, vehicle, insurance, retirement, other",
                },
                "description": {
                    "type": "string",
                    "description": "Description for the deduction entry",
                },
            },
            "required": ["transaction_ids", "tax_year", "deduction_type"],
        },
    },
    {
        "name": "get_tax_prep_checklist",
        "description": "Get a tax preparation checklist showing what documents and deductions exist vs. what's expected, with overall progress.",
        "input_schema": {
            "type": "object",
            "properties": {
                "tax_year": {
                    "type": "integer",
                    "description": "The tax year (e.g. 2025)",
                },
            },
            "required": ["tax_year"],
        },
    },
    # --- Phase 1A: Plaid/Bank Integration tools ---
    {
        "name": "link_bank_account",
        "description": "Guide the user through connecting a bank account via Plaid. Returns a link token to start the Plaid Link flow.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "sync_accounts",
        "description": "Trigger a manual sync of all connected bank accounts. Fetches new transactions and updates balances.",
        "input_schema": {
            "type": "object",
            "properties": {
                "plaid_item_id": {
                    "type": "integer",
                    "description": "Optional: sync a specific connected bank. If omitted, syncs all.",
                },
            },
            "required": [],
        },
    },
    # --- Phase 1B: Email Integration tools ---
    {
        "name": "connect_email",
        "description": "Guide the user through connecting their email account via IMAP for automatic receipt scanning.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "scan_email_now",
        "description": "Trigger a manual email scan to find receipts and financial documents in the user's connected email accounts.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "get_email_receipts",
        "description": "Show receipts that were found and extracted from the user's email.",
        "input_schema": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Max results (default 20)",
                },
            },
            "required": [],
        },
    },
    # --- Phase 2: Subscription tools ---
    {
        "name": "get_subscriptions",
        "description": "List all detected recurring subscriptions with amounts, frequency, annual cost, and status.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "get_subscription_spending",
        "description": "Get total monthly and annual subscription spending, broken down by subscription.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    # --- Phase 3: Cancellation tools ---
    {
        "name": "cancel_subscription",
        "description": "Draft a cancellation email for a subscription and send it with user confirmation. Shows the draft before sending.",
        "input_schema": {
            "type": "object",
            "properties": {
                "subscription_id": {
                    "type": "integer",
                    "description": "The subscription ID to cancel",
                },
                "confirm_send": {
                    "type": "boolean",
                    "description": "Set to true to actually send the cancellation email (after reviewing the draft)",
                },
            },
            "required": ["subscription_id"],
        },
    },
    {
        "name": "track_cancellation",
        "description": "Check the status of a pending subscription cancellation — whether final charges stopped.",
        "input_schema": {
            "type": "object",
            "properties": {
                "subscription_id": {
                    "type": "integer",
                    "description": "The subscription ID to track",
                },
            },
            "required": ["subscription_id"],
        },
    },
    # --- Phase 3: Tax Prep tools ---
    {
        "name": "prepare_tax_filing",
        "description": "Start a guided tax preparation workflow: collects all documents, calculates taxes, and generates a summary.",
        "input_schema": {
            "type": "object",
            "properties": {
                "tax_year": {
                    "type": "integer",
                    "description": "The tax year to prepare (e.g. 2025)",
                },
            },
            "required": ["tax_year"],
        },
    },
    {
        "name": "generate_schedule_c",
        "description": "Generate Schedule C (self-employment) summary from business income and expenses for a tax year.",
        "input_schema": {
            "type": "object",
            "properties": {
                "tax_year": {
                    "type": "integer",
                    "description": "The tax year (e.g. 2025)",
                },
            },
            "required": ["tax_year"],
        },
    },
    {
        "name": "find_missed_deductions",
        "description": "Scan all transactions for commonly missed deductions that haven't been claimed.",
        "input_schema": {
            "type": "object",
            "properties": {
                "tax_year": {
                    "type": "integer",
                    "description": "The tax year to scan (e.g. 2025)",
                },
            },
            "required": ["tax_year"],
        },
    },
    {
        "name": "export_tax_summary",
        "description": "Generate a complete tax filing summary with income, deductions, and tax calculation. Can export as CSV.",
        "input_schema": {
            "type": "object",
            "properties": {
                "tax_year": {
                    "type": "integer",
                    "description": "The tax year (e.g. 2025)",
                },
                "format": {
                    "type": "string",
                    "description": "Export format: summary (default) or csv",
                },
            },
            "required": ["tax_year"],
        },
    },
    # --- Phase 3: Alerts tool ---
    {
        "name": "get_alerts",
        "description": "Get the user's financial alerts and notifications (unusual spending, bill reminders, price changes, etc.).",
        "input_schema": {
            "type": "object",
            "properties": {
                "unread_only": {
                    "type": "boolean",
                    "description": "Only show unread alerts (default true)",
                },
                "alert_type": {
                    "type": "string",
                    "description": "Filter by type: unusual_spending, bill_due, low_balance, price_increase, large_transaction, new_fee, tax_reminder",
                },
            },
            "required": [],
        },
    },
    # --- Phase 2.4: Portfolio performance tool ---
    {
        "name": "get_portfolio_performance",
        "description": "Get portfolio performance with current market values, unrealized gains/losses, and day change for all holdings.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "get_weekly_summary",
        "description": "Get a weekly financial summary including spending comparison, top categories, notable transactions, and subscription costs.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "get_budgets",
        "description": "Get the user's budgets with current spending progress. Shows budget limits and how much has been spent in the current period.",
        "input_schema": {
            "type": "object",
            "properties": {
                "active_only": {
                    "type": "boolean",
                    "description": "Only return active budgets (default true)",
                },
            },
            "required": [],
        },
    },
    {
        "name": "get_goals",
        "description": "Get the user's financial goals with progress. Shows target amount, current amount, and percentage complete.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "create_goal",
        "description": "Create a new financial goal for the user.",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Goal name (e.g. 'Emergency fund', 'Vacation to Japan')",
                },
                "target_amount": {
                    "type": "number",
                    "description": "Target amount to save",
                },
                "current_amount": {
                    "type": "number",
                    "description": "Current amount saved (default 0)",
                },
                "target_date": {
                    "type": "string",
                    "description": "Target date (YYYY-MM-DD)",
                },
            },
            "required": ["name", "target_amount"],
        },
    },
    {
        "name": "set_budget",
        "description": "Create or update a budget for a spending category. Use category_name to find the category, or omit for a total spending budget.",
        "input_schema": {
            "type": "object",
            "properties": {
                "category_name": {
                    "type": "string",
                    "description": "Category name (e.g. 'Dining', 'Groceries'). Omit for total spending budget.",
                },
                "amount": {
                    "type": "number",
                    "description": "Budget limit amount",
                },
                "period": {
                    "type": "string",
                    "description": "Budget period: weekly, monthly, or annual",
                    "enum": ["weekly", "monthly", "annual"],
                },
            },
            "required": ["amount"],
        },
    },
]


# ---- Tool execution functions ----

def execute_tool(tool_name, tool_input, user):
    """Execute a tool by name and return the result dict."""
    handler = TOOL_HANDLERS.get(tool_name)
    if not handler:
        return {"error": f"Unknown tool: {tool_name}"}
    try:
        return handler(user, tool_input)
    except Exception:
        logger.exception("Tool execution error: %s", tool_name)
        return {"error": f"Tool '{tool_name}' failed to execute."}


def _get_accounts(user, params):
    qs = Account.objects.filter(user=user, is_active=True)
    if params.get("account_type"):
        qs = qs.filter(account_type=params["account_type"])

    accounts = []
    for a in qs:
        accounts.append({
            "id": a.id,
            "name": a.name,
            "account_type": a.account_type,
            "balance": str(a.balance),
            "currency": a.currency,
            "institution_name": a.institution.name if a.institution else None,
        })
    return {
        "accounts": accounts,
        "total": len(accounts),
        "component_type": "accounts_table",
    }


def _query_transactions(user, params):
    qs = Transaction.objects.filter(user=user).select_related("category", "account")
    if params.get("date_from"):
        qs = qs.filter(date__gte=params["date_from"])
    if params.get("date_to"):
        qs = qs.filter(date__lte=params["date_to"])
    if params.get("account_id"):
        qs = qs.filter(account_id=params["account_id"])
    if params.get("transaction_type"):
        qs = qs.filter(transaction_type=params["transaction_type"])
    if params.get("search"):
        qs = qs.filter(description__icontains=params["search"])

    limit = min(params.get("limit", 20), 50)
    qs = qs.order_by("-date")[:limit]

    transactions = []
    for t in qs:
        transactions.append({
            "id": t.id,
            "date": str(t.date),
            "description": t.description,
            "amount": str(t.amount),
            "transaction_type": t.transaction_type,
            "category_name": t.category.name if t.category else "Uncategorized",
            "account_name": t.account.name if t.account else None,
        })
    return {
        "transactions": transactions,
        "total": len(transactions),
        "component_type": "transactions_table",
    }


def _get_spending_summary(user, params):
    qs = Transaction.objects.filter(user=user, transaction_type="expense")
    if params.get("date_from"):
        qs = qs.filter(date__gte=params["date_from"])
    else:
        qs = qs.filter(date__gte=timezone.now() - timedelta(days=30))
    if params.get("date_to"):
        qs = qs.filter(date__lte=params["date_to"])

    summary = (
        qs.values("category__name")
        .annotate(total=Sum("amount"))
        .order_by("-total")
    )

    categories = [
        {
            "category_name": entry["category__name"] or "Uncategorized",
            "total": str(entry["total"]),
        }
        for entry in summary
    ]
    return {
        "categories": categories,
        "component_type": "spending_chart",
    }


def _get_dashboard_summary(user, _params):
    accounts = Account.objects.filter(user=user)
    total_accounts = accounts.count()
    net_worth = sum(a.balance for a in accounts)

    thirty_days_ago = timezone.now() - timedelta(days=30)
    recent_transactions = Transaction.objects.filter(
        user=user, date__gte=thirty_days_ago
    ).count()

    holdings = Holding.objects.filter(user=user)
    portfolio_cost = sum(h.cost_basis for h in holdings)

    return {
        "total_accounts": total_accounts,
        "net_worth": str(net_worth),
        "recent_transactions": recent_transactions,
        "portfolio_value": str(portfolio_cost),
        "component_type": "dashboard_summary",
    }


def _get_portfolio_holdings(user, _params):
    qs = Holding.objects.filter(user=user).select_related("security", "account")
    holdings = []
    for h in qs:
        holdings.append({
            "id": h.id,
            "symbol": h.security.symbol,
            "name": h.security.name,
            "security_type": h.security.security_type,
            "shares": str(h.shares),
            "cost_basis": str(h.cost_basis),
            "account_name": h.account.name if h.account else None,
        })
    return {
        "holdings": holdings,
        "total": len(holdings),
        "component_type": "portfolio_holdings",
    }


def _get_portfolio_allocation(user, _params):
    qs = Holding.objects.filter(user=user).select_related("security")
    allocation = defaultdict(lambda: {"total_shares": Decimal("0"), "total_cost_basis": Decimal("0"), "count": 0})

    for h in qs:
        sec_type = h.security.security_type
        allocation[sec_type]["total_shares"] += h.shares
        allocation[sec_type]["total_cost_basis"] += h.cost_basis
        allocation[sec_type]["count"] += 1

    result = [
        {
            "security_type": sec_type,
            "count": data["count"],
            "total_shares": str(data["total_shares"]),
            "total_cost_basis": str(data["total_cost_basis"]),
        }
        for sec_type, data in allocation.items()
    ]
    return {
        "allocation": result,
        "component_type": "allocation_chart",
    }


def _get_news_articles(user, params):
    limit = min(params.get("limit", 10), 30)
    qs = NewsArticle.objects.select_related("source").order_by("-published_at")[:limit]

    articles = []
    for a in qs:
        articles.append({
            "id": a.id,
            "title": a.title,
            "source_name": a.source.name if a.source else "",
            "url": a.url,
            "summary": a.summary[:200] if a.summary else "",
            "published_at": a.published_at.isoformat() if a.published_at else None,
        })
    return {
        "articles": articles,
        "total": len(articles),
        "component_type": "news_articles",
    }


def _search_security(user, params):
    symbol = params.get("symbol", "").strip().upper()
    if not symbol:
        return {"error": "Symbol is required."}

    try:
        import yfinance as yf
        ticker = yf.Ticker(symbol)
        info = ticker.info
    except Exception:
        logger.exception("yfinance lookup failed for %s", symbol)
        return {"error": "Stock data service is temporarily unavailable."}

    if not info.get("shortName") and not info.get("longName"):
        return {"error": f"Unknown symbol: {symbol}"}

    quote_type_map = {
        "EQUITY": "stock",
        "ETF": "etf",
        "MUTUALFUND": "mutual_fund",
        "CRYPTOCURRENCY": "crypto",
    }
    security_type = quote_type_map.get(info.get("quoteType", ""), "other")
    name = info.get("longName") or info.get("shortName") or symbol
    current_price = info.get("currentPrice") or info.get("regularMarketPrice")

    return {
        "symbol": symbol,
        "name": name,
        "security_type": security_type,
        "exchange": info.get("exchange", ""),
        "current_price": str(current_price) if current_price else None,
        "market_cap": info.get("marketCap"),
        "pe_ratio": info.get("trailingPE"),
        "dividend_yield": info.get("dividendYield"),
        "component_type": "security_lookup",
    }


def _get_tax_years(user, _params):
    qs = TaxYear.objects.filter(user=user).prefetch_related("documents", "deductions")
    tax_years = []
    for ty in qs:
        docs = ty.documents.all()
        deductions = ty.deductions.all()
        total_income = sum(d.amount for d in docs)
        total_deductions = sum(d.amount for d in deductions)
        tax_years.append({
            "id": ty.id,
            "year": ty.year,
            "filing_status": ty.filing_status,
            "document_count": len(docs),
            "total_document_income": str(total_income),
            "deduction_count": len(deductions),
            "total_deductions": str(total_deductions),
        })
    return {
        "tax_years": tax_years,
        "total": len(tax_years),
        "component_type": "tax_years",
    }


# --- Phase 1: Receipt & Expense tool handlers ---

def _get_receipts(user, params):
    qs = Receipt.objects.filter(user=user)
    if params.get("status"):
        qs = qs.filter(status=params["status"])
    if params.get("date_from"):
        qs = qs.filter(date__gte=params["date_from"])
    if params.get("date_to"):
        qs = qs.filter(date__lte=params["date_to"])
    if params.get("merchant"):
        qs = qs.filter(merchant__icontains=params["merchant"])

    receipts = []
    for r in qs[:50]:
        receipts.append({
            "id": r.id,
            "merchant": r.merchant or "Unknown",
            "date": str(r.date) if r.date else None,
            "total_amount": str(r.total_amount) if r.total_amount else None,
            "category": r.category,
            "status": r.status,
            "image_url": r.image.url if r.image else None,
            "created_at": r.created_at.isoformat(),
        })
    return {
        "receipts": receipts,
        "total": len(receipts),
        "component_type": "receipts_list",
    }


def _create_expense_from_receipt(user, params):
    receipt_id = params.get("receipt_id")
    year = params.get("tax_year")
    deduction_type = params.get("deduction_type", "business")

    try:
        receipt = Receipt.objects.get(id=receipt_id, user=user)
    except Receipt.DoesNotExist:
        return {"error": "Receipt not found."}

    if receipt.status != "completed":
        return {"error": f"Receipt is not processed yet (status: {receipt.status})."}

    tax_year, _ = TaxYear.objects.get_or_create(
        user=user, year=year, defaults={"filing_status": "single"}
    )

    expense = DeductibleExpense.objects.create(
        tax_year=tax_year,
        receipt=receipt,
        deduction_type=deduction_type,
        description=f"{receipt.merchant} - {receipt.date or 'no date'}",
        amount=receipt.total_amount or 0,
    )
    receipt.deductible_expense = expense
    receipt.tax_year = tax_year
    receipt.save(update_fields=["deductible_expense", "tax_year"])

    line_items = []
    for li in receipt.line_items.all():
        line_items.append({
            "description": li.description,
            "total_price": str(li.total_price),
        })

    return {
        "expense_id": expense.id,
        "receipt_id": receipt.id,
        "merchant": receipt.merchant,
        "date": str(receipt.date) if receipt.date else None,
        "total_amount": str(receipt.total_amount) if receipt.total_amount else None,
        "deduction_type": deduction_type,
        "tax_year": year,
        "line_items": line_items,
        "component_type": "receipt_card",
    }


def _generate_expense_report(user, params):
    year = params.get("tax_year")
    try:
        tax_year = TaxYear.objects.get(user=user, year=year)
    except TaxYear.DoesNotExist:
        return {"error": f"No tax year found for {year}."}

    deductions = tax_year.deductions.all()
    categories = defaultdict(lambda: {"items": [], "total": Decimal("0")})

    for d in deductions:
        cat = d.get_deduction_type_display()
        categories[cat]["items"].append({
            "id": d.id,
            "description": d.description,
            "amount": str(d.amount),
            "is_verified": d.is_verified,
        })
        categories[cat]["total"] += d.amount

    report_categories = []
    grand_total = Decimal("0")
    for cat_name, data in sorted(categories.items(), key=lambda x: x[1]["total"], reverse=True):
        report_categories.append({
            "category": cat_name,
            "total": str(data["total"]),
            "count": len(data["items"]),
            "items": data["items"],
        })
        grand_total += data["total"]

    return {
        "tax_year": year,
        "filing_status": tax_year.filing_status,
        "categories": report_categories,
        "grand_total": str(grand_total),
        "component_type": "expense_report",
    }


# --- Phase 2: Tax Estimation tool handlers ---

def _estimate_taxes(user, params):
    from taxes.tax_engine import calculate_taxes

    year = params.get("tax_year")
    try:
        tax_year = TaxYear.objects.get(user=user, year=year)
    except TaxYear.DoesNotExist:
        return {"error": f"No tax year found for {year}. Create one first."}

    tax_input = _build_tax_input(tax_year)
    result = calculate_taxes(tax_input)

    return {
        **_serialize_tax_breakdown(result),
        "tax_year": year,
        "filing_status": tax_year.filing_status,
        "component_type": "tax_estimate",
    }


def _compare_filing_statuses(user, params):
    from taxes.tax_engine import calculate_taxes

    year = params.get("tax_year")
    try:
        tax_year = TaxYear.objects.get(user=user, year=year)
    except TaxYear.DoesNotExist:
        return {"error": f"No tax year found for {year}. Create one first."}

    statuses = ["single", "married_joint", "married_separate", "head_of_household"]
    comparisons = []
    for fs in statuses:
        tax_input = _build_tax_input(tax_year, filing_status_override=fs)
        result = calculate_taxes(tax_input)
        comparisons.append({
            "filing_status": fs,
            "filing_status_display": dict(TaxYear._meta.get_field("filing_status").choices).get(fs, fs),
            **_serialize_tax_breakdown(result),
        })

    # Find optimal
    best = min(comparisons, key=lambda c: float(c["total_tax"]))

    return {
        "tax_year": year,
        "comparisons": comparisons,
        "optimal_status": best["filing_status"],
        "component_type": "filing_comparison",
    }


def _build_tax_input(tax_year, filing_status_override=None):
    """Build a TaxInput dataclass from a TaxYear's documents and deductions."""
    from taxes.tax_engine import TaxInput

    docs = tax_year.documents.all()
    deductions = tax_year.deductions.all()
    filing_status = filing_status_override or tax_year.filing_status

    # Map documents to income fields
    w2_income = Decimal("0")
    federal_withheld = Decimal("0")
    state_withheld = Decimal("0")
    ss_withheld = Decimal("0")
    medicare_withheld = Decimal("0")
    interest_income = Decimal("0")
    ordinary_dividends = Decimal("0")
    qualified_dividends = Decimal("0")
    short_term_gains = Decimal("0")
    long_term_gains = Decimal("0")
    self_employment_income = Decimal("0")
    other_income = Decimal("0")
    k1_income = Decimal("0")

    for doc in docs:
        details = doc.details or {}
        if doc.document_type == "w2":
            w2_income += doc.amount
            federal_withheld += Decimal(str(details.get("federal_withheld", 0)))
            state_withheld += Decimal(str(details.get("state_withheld", 0)))
            ss_withheld += Decimal(str(details.get("ss_withheld", 0)))
            medicare_withheld += Decimal(str(details.get("medicare_withheld", 0)))
        elif doc.document_type == "1099_int":
            interest_income += doc.amount
        elif doc.document_type == "1099_div":
            ordinary_dividends += doc.amount
            qualified_dividends += Decimal(str(details.get("qualified_dividends", 0)))
        elif doc.document_type == "1099_b":
            st = Decimal(str(details.get("short_term", 0)))
            lt = Decimal(str(details.get("long_term", 0)))
            if st == 0 and lt == 0:
                # Default: treat entire amount as long-term
                long_term_gains += doc.amount
            else:
                short_term_gains += st
                long_term_gains += lt
        elif doc.document_type == "1099_nec":
            self_employment_income += doc.amount
        elif doc.document_type == "1099_misc":
            other_income += doc.amount
        elif doc.document_type == "k1":
            k1_income += doc.amount
        elif doc.document_type == "1098":
            pass  # Mortgage interest handled via deductions
        else:
            other_income += doc.amount

    # Map deductions
    mortgage_interest = Decimal("0")
    state_local_tax = Decimal("0")
    charitable = Decimal("0")
    medical = Decimal("0")
    business_expenses = Decimal("0")
    education = Decimal("0")
    ira_contributions = Decimal("0")
    hsa_contributions = Decimal("0")

    for d in deductions:
        if d.deduction_type == "mortgage_interest":
            mortgage_interest += d.amount
        elif d.deduction_type == "state_local_tax":
            state_local_tax += d.amount
        elif d.deduction_type == "charitable":
            charitable += d.amount
        elif d.deduction_type == "medical":
            medical += d.amount
        elif d.deduction_type in ("business", "home_office", "vehicle"):
            business_expenses += d.amount
        elif d.deduction_type == "education":
            education += d.amount
        elif d.deduction_type == "retirement":
            ira_contributions += d.amount
        elif d.deduction_type == "insurance":
            pass  # SE health insurance handled separately if needed

    return TaxInput(
        filing_status=filing_status,
        tax_year=tax_year.year,
        w2_income=w2_income,
        federal_withheld=federal_withheld,
        state_withheld=state_withheld,
        ss_withheld=ss_withheld,
        medicare_withheld=medicare_withheld,
        interest_income=interest_income,
        ordinary_dividends=ordinary_dividends,
        qualified_dividends=qualified_dividends,
        short_term_gains=short_term_gains,
        long_term_gains=long_term_gains,
        self_employment_income=self_employment_income,
        other_income=other_income + k1_income,
        mortgage_interest=mortgage_interest,
        state_local_tax=state_local_tax,
        charitable=charitable,
        medical=medical,
        business_expenses=business_expenses,
        education=education,
        ira_contributions=ira_contributions,
        hsa_contributions=hsa_contributions,
    )


def _serialize_tax_breakdown(result):
    """Convert a TaxBreakdown to a serializable dict."""
    return {
        "gross_income": str(result.gross_income),
        "agi": str(result.agi),
        "taxable_income": str(result.taxable_income),
        "standard_deduction": str(result.standard_deduction),
        "itemized_deduction": str(result.itemized_deduction),
        "deduction_used": result.deduction_used,
        "bracket_details": [
            {"bracket": str(b["bracket"]), "rate": str(b["rate"]), "tax": str(b["tax"])}
            for b in result.bracket_details
        ],
        "ordinary_tax": str(result.ordinary_tax),
        "ltcg_tax": str(result.ltcg_tax),
        "self_employment_tax": str(result.self_employment_tax),
        "qbi_deduction": str(result.qbi_deduction),
        "amt_estimate": str(result.amt_estimate),
        "total_tax": str(result.total_tax),
        "total_withheld": str(result.total_withheld),
        "amount_owed": str(result.amount_owed),
        "effective_rate": str(result.effective_rate),
        "marginal_rate": str(result.marginal_rate),
    }


# --- Phase 3: Tax Prep Assistant tool handlers ---

# Maps transaction category names to potential deduction types
CATEGORY_DEDUCTION_MAP = {
    "Medical": "medical",
    "Healthcare": "medical",
    "Doctor": "medical",
    "Pharmacy": "medical",
    "Dentist": "medical",
    "Charitable": "charitable",
    "Donations": "charitable",
    "Charity": "charitable",
    "Education": "education",
    "Tuition": "education",
    "Books": "education",
    "Office": "business",
    "Office Supplies": "business",
    "Software": "business",
    "Business": "business",
    "Professional Services": "business",
    "Home Improvement": "home_office",
    "Home Office": "home_office",
    "Gas": "vehicle",
    "Auto": "vehicle",
    "Car Maintenance": "vehicle",
    "Parking": "vehicle",
    "Insurance": "insurance",
}


def _scan_transactions_for_deductions(user, params):
    year = params.get("tax_year")

    try:
        tax_year = TaxYear.objects.get(user=user, year=year)
    except TaxYear.DoesNotExist:
        return {"error": f"No tax year found for {year}. Create one first."}

    # Get all expense transactions for the year
    qs = Transaction.objects.filter(
        user=user,
        transaction_type="expense",
        date__year=year,
    ).select_related("category")

    # Get existing deduction amounts by type
    existing = defaultdict(Decimal)
    for d in tax_year.deductions.all():
        existing[d.deduction_type] += d.amount

    suggestions = defaultdict(lambda: {"transactions": [], "total": Decimal("0"), "existing_total": Decimal("0")})

    for t in qs:
        cat_name = t.category.name if t.category else ""
        deduction_type = None
        # Check category name against map
        for pattern, dtype in CATEGORY_DEDUCTION_MAP.items():
            if pattern.lower() in cat_name.lower():
                deduction_type = dtype
                break
        # Also check description
        if not deduction_type:
            desc_lower = t.description.lower()
            for pattern, dtype in CATEGORY_DEDUCTION_MAP.items():
                if pattern.lower() in desc_lower:
                    deduction_type = dtype
                    break

        if deduction_type:
            suggestions[deduction_type]["transactions"].append({
                "id": t.id,
                "date": str(t.date),
                "description": t.description,
                "amount": str(t.amount),
                "category_name": cat_name,
            })
            suggestions[deduction_type]["total"] += t.amount
            suggestions[deduction_type]["existing_total"] = existing.get(deduction_type, Decimal("0"))

    result_suggestions = []
    for dtype, data in sorted(suggestions.items(), key=lambda x: x[1]["total"], reverse=True):
        unclaimed = data["total"] - data["existing_total"]
        if unclaimed > 0:
            result_suggestions.append({
                "deduction_type": dtype,
                "deduction_type_display": dict(DeductibleExpense.DEDUCTION_TYPES).get(dtype, dtype),
                "transaction_count": len(data["transactions"]),
                "total_amount": str(data["total"]),
                "existing_claimed": str(data["existing_total"]),
                "unclaimed_amount": str(unclaimed),
                "transactions": data["transactions"][:10],  # Limit to 10 per category
            })

    return {
        "tax_year": year,
        "suggestions": result_suggestions,
        "total_unclaimed": str(sum(
            Decimal(s["unclaimed_amount"]) for s in result_suggestions
        )),
        "component_type": "deduction_suggestions",
    }


def _create_deduction_from_transactions(user, params):
    transaction_ids = params.get("transaction_ids", [])
    year = params.get("tax_year")
    deduction_type = params.get("deduction_type", "business")
    description = params.get("description", "")

    if not transaction_ids:
        return {"error": "No transaction IDs provided."}

    tax_year, _ = TaxYear.objects.get_or_create(
        user=user, year=year, defaults={"filing_status": "single"}
    )

    transactions = Transaction.objects.filter(
        id__in=transaction_ids, user=user
    ).select_related("category")

    if not transactions.exists():
        return {"error": "No matching transactions found."}

    total = sum(t.amount for t in transactions)

    if not description:
        descriptions = [t.description for t in transactions[:3]]
        description = ", ".join(descriptions)
        if len(transactions) > 3:
            description += f" (+{len(transactions) - 3} more)"

    expense = DeductibleExpense.objects.create(
        tax_year=tax_year,
        deduction_type=deduction_type,
        description=description,
        amount=total,
    )

    return {
        "expense_id": expense.id,
        "deduction_type": deduction_type,
        "description": description,
        "amount": str(total),
        "transaction_count": len(transactions),
        "tax_year": year,
        "component_type": "expense_report",
    }


def _get_tax_prep_checklist(user, params):
    year = params.get("tax_year")

    try:
        tax_year = TaxYear.objects.get(user=user, year=year)
    except TaxYear.DoesNotExist:
        return {"error": f"No tax year found for {year}. Create one first."}

    docs = list(tax_year.documents.all())
    deductions = list(tax_year.deductions.all())
    doc_types = {d.document_type for d in docs}

    # Check user's accounts to infer expected documents
    accounts = Account.objects.filter(user=user, is_active=True)
    account_types = {a.account_type for a in accounts}

    checklist_sections = []

    # Section 1: Filing Status
    checklist_sections.append({
        "section": "Filing Status",
        "items": [{
            "label": "Filing status selected",
            "status": "complete" if tax_year.filing_status else "incomplete",
            "detail": tax_year.get_filing_status_display() if tax_year.filing_status else "Not set",
        }],
    })

    # Section 2: Income Documents
    doc_items = []
    # Always expect W-2 if there are checking/savings accounts (employment likely)
    doc_items.append({
        "label": "W-2 (Employment Income)",
        "status": "complete" if "w2" in doc_types else "incomplete",
        "detail": f"{sum(1 for d in docs if d.document_type == 'w2')} uploaded" if "w2" in doc_types else "Not uploaded",
    })

    if "investment" in account_types:
        for dt, label in [("1099_b", "1099-B (Investment Sales)"), ("1099_div", "1099-DIV (Dividends)"), ("1099_int", "1099-INT (Interest)")]:
            doc_items.append({
                "label": label,
                "status": "complete" if dt in doc_types else "review",
                "detail": f"{sum(1 for d in docs if d.document_type == dt)} uploaded" if dt in doc_types else "Check if applicable",
            })

    if "1099_nec" in doc_types:
        doc_items.append({
            "label": "1099-NEC (Self-Employment)",
            "status": "complete",
            "detail": f"{sum(1 for d in docs if d.document_type == '1099_nec')} uploaded",
        })

    if "mortgage" in account_types or "loan" in account_types:
        doc_items.append({
            "label": "1098 (Mortgage Interest)",
            "status": "complete" if "1098" in doc_types else "review",
            "detail": f"{sum(1 for d in docs if d.document_type == '1098')} uploaded" if "1098" in doc_types else "Check if applicable",
        })

    checklist_sections.append({
        "section": "Income Documents",
        "items": doc_items,
    })

    # Section 3: Deductions
    deduction_items = []
    deduction_types = {d.deduction_type for d in deductions}
    deduction_totals = defaultdict(Decimal)
    for d in deductions:
        deduction_totals[d.deduction_type] += d.amount

    for dt, label in [
        ("mortgage_interest", "Mortgage Interest"),
        ("state_local_tax", "State & Local Taxes"),
        ("charitable", "Charitable Donations"),
        ("medical", "Medical Expenses"),
        ("business", "Business Expenses"),
    ]:
        if dt in deduction_types:
            deduction_items.append({
                "label": label,
                "status": "complete",
                "detail": f"${deduction_totals[dt]:,.2f} claimed",
            })
        else:
            deduction_items.append({
                "label": label,
                "status": "review",
                "detail": "Not yet reviewed",
            })

    checklist_sections.append({
        "section": "Deductions",
        "items": deduction_items,
    })

    # Section 4: Review
    has_all_docs = len(doc_items) > 0 and all(i["status"] == "complete" for i in doc_items)
    has_deductions = len(deductions) > 0

    review_items = [
        {
            "label": "All income documents uploaded",
            "status": "complete" if has_all_docs else "incomplete",
            "detail": f"{len(docs)} documents" if docs else "No documents yet",
        },
        {
            "label": "Deductions reviewed",
            "status": "complete" if has_deductions else "incomplete",
            "detail": f"${sum(d.amount for d in deductions):,.2f} total" if deductions else "No deductions yet",
        },
        {
            "label": "Transaction scan for missed deductions",
            "status": "review",
            "detail": "Run scan_transactions_for_deductions to check",
        },
    ]

    checklist_sections.append({
        "section": "Review",
        "items": review_items,
    })

    # Calculate overall progress
    all_items = [item for section in checklist_sections for item in section["items"]]
    complete_count = sum(1 for i in all_items if i["status"] == "complete")
    total_count = len(all_items)

    return {
        "tax_year": year,
        "sections": checklist_sections,
        "progress": {
            "complete": complete_count,
            "total": total_count,
            "percentage": round(complete_count / total_count * 100) if total_count > 0 else 0,
        },
        "component_type": "tax_checklist",
    }


# --- Phase 1A: Plaid/Bank Integration tool handlers ---

def _link_bank_account(user, _params):
    try:
        from integrations.plaid_client import create_link_token
        link_token = create_link_token(user)
        return {
            "link_token": link_token,
            "message": "Use the Plaid Link component with this token to connect your bank account.",
            "component_type": "sync_status",
        }
    except Exception as e:
        if "PLAID_CLIENT_ID" in str(e) or not __import__("django").conf.settings.PLAID_CLIENT_ID:
            return {"error": "Plaid is not configured. Add PLAID_CLIENT_ID and PLAID_SECRET to your .env file."}
        return {"error": f"Failed to create link token: {str(e)}"}


def _sync_accounts(user, params):
    from integrations.models import PlaidItem

    plaid_item_id = params.get("plaid_item_id")
    if plaid_item_id:
        items = PlaidItem.objects.filter(id=plaid_item_id, user=user, status="active")
    else:
        items = PlaidItem.objects.filter(user=user, status="active")

    if not items.exists():
        return {"error": "No connected bank accounts found. Use link_bank_account to connect one."}

    results = []
    for item in items:
        from integrations.tasks import sync_plaid_transactions
        from core.task_utils import run_task
        run_task(sync_plaid_transactions, item.id)
        results.append({
            "institution": item.institution_name,
            "status": "sync_started",
        })

    return {
        "synced_items": results,
        "message": f"Started syncing {len(results)} connected account(s). Transactions will update shortly.",
        "component_type": "sync_status",
    }


# --- Phase 1B: Email Integration tool handlers ---

def _connect_email(user, params):
    return {
        "provider": "imap",
        "message": "To connect your email, go to Settings > Email and enter your IMAP server details. For Gmail, use an App Password (generate one at myaccount.google.com/apppasswords).",
        "fields_needed": ["email_address", "imap_host", "imap_port", "username", "password"],
        "component_type": "email_connect",
    }


def _scan_email_now(user, _params):
    from email_sync.models import EmailAccount

    accounts = EmailAccount.objects.filter(user=user, status="active")
    if not accounts.exists():
        return {"error": "No email accounts connected. Use connect_email to set one up."}

    results = []
    for account in accounts:
        from email_sync.tasks import scan_single_email_account
        from core.task_utils import run_task
        run_task(scan_single_email_account, account.id)
        results.append({
            "email": account.email_address,
            "provider": account.provider,
            "status": "scan_started",
        })

    return {
        "scanned_accounts": results,
        "message": f"Started scanning {len(results)} email account(s) for receipts.",
        "component_type": "sync_status",
    }


def _get_email_receipts(user, params):
    limit = min(params.get("limit", 20), 50)

    from email_sync.models import EmailAttachment

    attachments = (
        EmailAttachment.objects.filter(
            email_message__email_account__user=user,
            receipt__isnull=False,
        )
        .select_related("receipt", "email_message")
        .order_by("-created_at")[:limit]
    )

    receipts = []
    for att in attachments:
        r = att.receipt
        receipts.append({
            "id": r.id,
            "merchant": r.merchant or "Unknown",
            "total_amount": str(r.total_amount) if r.total_amount else None,
            "date": str(r.date) if r.date else None,
            "status": r.status,
            "email_subject": att.email_message.subject,
            "email_from": att.email_message.from_address,
            "email_date": att.email_message.date.isoformat(),
        })

    return {
        "receipts": receipts,
        "total": len(receipts),
        "component_type": "receipts_list",
    }


# --- Phase 2: Subscription tool handlers ---

def _get_subscriptions(user, _params):
    from transactions.models import Subscription

    subs = Subscription.objects.filter(user=user)

    if not subs.exists():
        # Try to detect on the fly
        from transactions.subscriptions import detect_subscriptions
        detected = detect_subscriptions(user)
        if detected:
            return {
                "subscriptions": detected,
                "total": len(detected),
                "total_monthly": str(sum(
                    float(s["amount"]) for s in detected if s["frequency"] == "monthly"
                )),
                "total_annual": str(sum(s["annual_cost"] for s in detected)),
                "source": "detected",
                "component_type": "subscriptions_table",
            }
        return {"subscriptions": [], "total": 0, "message": "No subscriptions detected yet."}

    subscriptions = []
    total_monthly = Decimal("0")
    total_annual = Decimal("0")

    for s in subs:
        subscriptions.append({
            "id": s.id,
            "merchant": s.merchant,
            "amount": str(s.amount),
            "frequency": s.frequency,
            "status": s.status,
            "last_charged": str(s.last_charged) if s.last_charged else None,
            "next_expected": str(s.next_expected) if s.next_expected else None,
            "annual_cost": round(s.annual_cost, 2),
            "cancellation_url": s.cancellation_url,
            "cancellation_method": s.cancellation_method,
        })
        total_annual += Decimal(str(s.annual_cost))
        if s.frequency == "monthly":
            total_monthly += s.amount

    return {
        "subscriptions": subscriptions,
        "total": len(subscriptions),
        "total_monthly": str(total_monthly),
        "total_annual": str(total_annual),
        "component_type": "subscriptions_table",
    }


def _get_subscription_spending(user, _params):
    from transactions.models import Subscription

    subs = Subscription.objects.filter(user=user, status="active")

    if not subs.exists():
        return {"error": "No active subscriptions found. Run get_subscriptions first to detect them."}

    monthly_total = Decimal("0")
    annual_total = Decimal("0")
    by_frequency = defaultdict(lambda: {"count": 0, "total": Decimal("0")})

    for s in subs:
        annual = Decimal(str(s.annual_cost))
        monthly = annual / 12
        monthly_total += monthly
        annual_total += annual
        by_frequency[s.frequency]["count"] += 1
        by_frequency[s.frequency]["total"] += s.amount

    return {
        "monthly_total": str(monthly_total.quantize(Decimal("0.01"))),
        "annual_total": str(annual_total.quantize(Decimal("0.01"))),
        "subscription_count": subs.count(),
        "by_frequency": {
            freq: {"count": data["count"], "total": str(data["total"])}
            for freq, data in by_frequency.items()
        },
        "component_type": "subscription_spending",
    }


# --- Phase 3: Cancellation tool handlers ---

def _cancel_subscription(user, params):
    from transactions.models import Subscription

    sub_id = params.get("subscription_id")
    confirm = params.get("confirm_send", False)

    try:
        sub = Subscription.objects.get(id=sub_id, user=user)
    except Subscription.DoesNotExist:
        return {"error": "Subscription not found."}

    if sub.status == "cancelled":
        return {"error": f"{sub.merchant} is already cancelled."}

    from email_sync.sender import generate_cancellation_email
    email_draft = generate_cancellation_email(
        merchant=sub.merchant,
        subscription_amount=str(sub.amount),
        user_name=user.get_full_name() or user.username,
    )

    if not confirm:
        return {
            "subscription_id": sub.id,
            "merchant": sub.merchant,
            "amount": str(sub.amount),
            "draft_subject": email_draft["subject"],
            "draft_body": email_draft["body"],
            "cancellation_url": sub.cancellation_url,
            "cancellation_method": sub.cancellation_method or "email",
            "message": "Review the cancellation email draft above. Call this tool again with confirm_send=true to send it.",
            "component_type": "cancellation_draft",
        }

    # User confirmed — attempt to send
    from email_sync.models import EmailAccount
    email_account = EmailAccount.objects.filter(user=user, status="active").first()

    if email_account:
        from email_sync.sender import send_cancellation_email
        # Use the cancellation URL domain if available, otherwise prompt user
        to_email = params.get("to_email", "")
        if not to_email:
            return {
                "subscription_id": sub.id,
                "merchant": sub.merchant,
                "cancellation_url": sub.cancellation_url,
                "draft_subject": email_draft["subject"],
                "draft_body": email_draft["body"],
                "message": (
                    f"I don't have a verified email address for {sub.merchant}'s support team. "
                    f"Please provide the email address to send the cancellation to, "
                    f"or visit their cancellation page directly"
                    + (f": {sub.cancellation_url}" if sub.cancellation_url else ".")
                ),
                "component_type": "cancellation_manual",
            }

        result = send_cancellation_email(
            to_email=to_email,
            subject=email_draft["subject"],
            body=email_draft["body"],
            email_account=email_account,
        )

        if result["success"]:
            sub.status = "cancellation_pending"
            sub.notes = f"Cancellation email sent to {to_email}"
            sub.save(update_fields=["status", "notes", "updated_at"])
            return {
                "subscription_id": sub.id,
                "merchant": sub.merchant,
                "status": "cancellation_pending",
                "email_sent_to": to_email,
                "message": f"Cancellation email sent to {to_email}. I'll monitor for any further charges.",
                "component_type": "cancellation_sent",
            }
        else:
            return {"error": f"Failed to send email: {result['error']}"}
    else:
        # No email account connected — provide manual instructions
        sub.status = "cancellation_pending"
        sub.save(update_fields=["status", "updated_at"])
        return {
            "subscription_id": sub.id,
            "merchant": sub.merchant,
            "status": "cancellation_pending",
            "cancellation_url": sub.cancellation_url,
            "draft_subject": email_draft["subject"],
            "draft_body": email_draft["body"],
            "message": "No email account connected. Here's the cancellation email text you can copy and send manually.",
            "component_type": "cancellation_manual",
        }


def _track_cancellation(user, params):
    from transactions.models import Subscription

    sub_id = params.get("subscription_id")
    try:
        sub = Subscription.objects.get(id=sub_id, user=user)
    except Subscription.DoesNotExist:
        return {"error": "Subscription not found."}

    from transactions.models import Transaction

    # Check for charges after the cancellation was requested
    if sub.last_charged:
        recent_charges = Transaction.objects.filter(
            user=user,
            transaction_type="expense",
            description__icontains=sub.merchant,
            date__gt=sub.last_charged,
        ).order_by("-date")

        if recent_charges.exists():
            latest = recent_charges.first()
            return {
                "subscription_id": sub.id,
                "merchant": sub.merchant,
                "status": sub.status,
                "last_charge_date": str(latest.date),
                "last_charge_amount": str(latest.amount),
                "message": f"A charge of ${latest.amount} was found on {latest.date}. The subscription may not be cancelled yet.",
                "component_type": "cancellation_tracking",
            }

    # No charges found after cancellation
    if sub.status == "cancellation_pending":
        return {
            "subscription_id": sub.id,
            "merchant": sub.merchant,
            "status": "cancellation_pending",
            "message": f"No new charges detected for {sub.merchant} since cancellation was requested. Will continue monitoring.",
            "component_type": "cancellation_tracking",
        }

    return {
        "subscription_id": sub.id,
        "merchant": sub.merchant,
        "status": sub.status,
        "message": f"Subscription status: {sub.get_status_display()}",
        "component_type": "cancellation_tracking",
    }


# --- Phase 3: Tax Prep tool handlers ---

def _prepare_tax_filing(user, params):
    year = params.get("tax_year")

    try:
        tax_year = TaxYear.objects.get(user=user, year=year)
    except TaxYear.DoesNotExist:
        tax_year = TaxYear.objects.create(user=user, year=year, filing_status="single")

    # Gather comprehensive summary
    docs = list(tax_year.documents.all())
    deductions = list(tax_year.deductions.all())
    total_income = sum(d.amount for d in docs)
    total_deductions = sum(d.amount for d in deductions)

    # Check Plaid connection for auto-populated data
    from integrations.models import PlaidItem
    plaid_connected = PlaidItem.objects.filter(user=user, status="active").exists()

    # Run deduction scan
    try:
        scan_result = _scan_transactions_for_deductions(user, {"tax_year": year})
        unclaimed = scan_result.get("total_unclaimed", "0")
    except Exception:
        unclaimed = "0"

    # Calculate tax estimate
    try:
        from taxes.tax_engine import calculate_taxes
        tax_input = _build_tax_input(tax_year)
        tax_result = calculate_taxes(tax_input)
    except Exception:
        tax_result = None

    return {
        "tax_year": year,
        "filing_status": tax_year.get_filing_status_display(),
        "documents": {
            "count": len(docs),
            "total_income": str(total_income),
            "types": list({d.document_type for d in docs}),
        },
        "deductions": {
            "count": len(deductions),
            "total": str(total_deductions),
            "unclaimed_potential": unclaimed,
        },
        "tax_estimate": {
            "total_tax": str(tax_result.total_tax) if tax_result else "0",
            "amount_owed": str(tax_result.amount_owed) if tax_result else "0",
            "effective_rate": str(tax_result.effective_rate) if tax_result else "0",
        } if tax_result else None,
        "plaid_connected": plaid_connected,
        "next_steps": _get_tax_next_steps(docs, deductions, unclaimed),
        "component_type": "tax_filing_prep",
    }


def _get_tax_next_steps(docs, deductions, unclaimed):
    steps = []
    doc_types = {d.document_type for d in docs}
    if not docs:
        steps.append("Upload your W-2 and 1099 forms")
    if "w2" not in doc_types:
        steps.append("Add your W-2 (employment income)")
    if unclaimed and Decimal(unclaimed) > 0:
        steps.append(f"Review ${unclaimed} in potential unclaimed deductions")
    if not deductions:
        steps.append("Review and add deductible expenses")
    steps.append("Run compare_filing_statuses to find optimal filing status")
    return steps


def _generate_schedule_c(user, params):
    from taxes.schedule_c import generate_schedule_c

    year = params.get("tax_year")
    try:
        result = generate_schedule_c(user, year)
        result["component_type"] = "schedule_c"
        return result
    except Exception as e:
        return {"error": f"Failed to generate Schedule C: {str(e)}"}


def _find_missed_deductions(user, params):
    """Enhanced version of scan_transactions that also checks common missed deductions."""
    result = _scan_transactions_for_deductions(user, params)
    if "error" in result:
        return result

    # Add commonly missed deduction categories
    commonly_missed = [
        {"category": "Home office expenses", "description": "If you work from home, a portion of rent/mortgage, utilities, and internet may be deductible."},
        {"category": "Vehicle mileage", "description": "Track business miles for a standard mileage deduction of $0.67/mile (2025)."},
        {"category": "Health insurance premiums", "description": "Self-employed individuals can deduct health insurance premiums."},
        {"category": "Professional development", "description": "Books, courses, conferences, and certifications related to your work."},
        {"category": "Bank & service fees", "description": "Business-related bank fees, credit card processing fees, and software subscriptions."},
        {"category": "State/local tax payments", "description": "State income tax or sales tax payments (SALT deduction up to $10,000)."},
    ]

    result["commonly_missed"] = commonly_missed
    result["component_type"] = "missed_deductions"
    return result


def _export_tax_summary(user, params):
    fmt = params.get("format", "summary")
    year = params.get("tax_year")

    if fmt == "csv":
        from taxes.export import export_tax_csv
        csv_data = export_tax_csv(user, year)
        if not csv_data:
            return {"error": f"No tax year found for {year}."}
        return {
            "tax_year": year,
            "format": "csv",
            "csv_data": csv_data,
            "message": "CSV export generated. Copy the data above or download it.",
            "component_type": "tax_csv_export",
        }

    from taxes.export import generate_tax_summary
    try:
        result = generate_tax_summary(user, year)
        if isinstance(result, dict):
            result["component_type"] = "tax_summary_export"
        return result
    except Exception as e:
        return {"error": f"Failed to generate tax summary: {str(e)}"}


# --- Alerts tool handler ---

def _get_alerts(user, params):
    from core.models import Alert

    qs = Alert.objects.filter(user=user)
    if params.get("unread_only", True):
        qs = qs.filter(is_read=False)
    if params.get("alert_type"):
        qs = qs.filter(alert_type=params["alert_type"])

    alerts = []
    for a in qs[:30]:
        alerts.append({
            "id": a.id,
            "type": a.alert_type,
            "severity": a.severity,
            "title": a.title,
            "message": a.message,
            "is_read": a.is_read,
            "created_at": a.created_at.isoformat(),
            "action_url": a.action_url,
        })

    # Mark as read
    qs.update(is_read=True)

    return {
        "alerts": alerts,
        "total": len(alerts),
        "component_type": "alerts_list",
    }


# --- Portfolio performance tool handler ---

def _get_portfolio_performance(user, _params):
    from portfolio.performance import calculate_portfolio_performance
    result = calculate_portfolio_performance(user)
    result["component_type"] = "portfolio_performance"
    return result


def _get_weekly_summary(user, _params):
    """Get the latest weekly financial summary."""
    from datetime import timedelta
    from decimal import Decimal

    from django.db.models import Sum
    from django.utils import timezone

    from accounts.models import Account
    from transactions.models import Subscription, Transaction

    now = timezone.now()
    week_start = (now - timedelta(days=7)).date()
    prev_week_start = (now - timedelta(days=14)).date()

    this_week = Transaction.objects.filter(
        user=user, transaction_type="expense", date__gte=week_start,
    ).aggregate(total=Sum("amount"))["total"] or Decimal("0")

    last_week = Transaction.objects.filter(
        user=user, transaction_type="expense",
        date__gte=prev_week_start, date__lt=week_start,
    ).aggregate(total=Sum("amount"))["total"] or Decimal("0")

    top_categories = list(
        Transaction.objects.filter(
            user=user, transaction_type="expense", date__gte=week_start,
        )
        .values("category__name")
        .annotate(total=Sum("amount"))
        .order_by("-total")[:5]
    )

    notable = list(
        Transaction.objects.filter(
            user=user, date__gte=week_start, amount__gte=100,
        ).order_by("-amount")[:5]
    )

    net_worth = sum(a.balance for a in Account.objects.filter(user=user))

    sub_monthly = Decimal("0")
    for s in Subscription.objects.filter(user=user, status="active"):
        sub_monthly += s.annual_cost / 12

    change_pct = (
        round(float((this_week - last_week) / last_week * 100), 1)
        if last_week > 0
        else 0
    )

    return {
        "week_ending": now.date().isoformat(),
        "spending": {
            "this_week": str(this_week),
            "last_week": str(last_week),
            "change_pct": str(change_pct),
        },
        "top_categories": [
            {"name": c["category__name"] or "Uncategorized", "amount": str(c["total"])}
            for c in top_categories
        ],
        "notable_transactions": [
            {"description": t.description, "amount": str(t.amount), "date": t.date.isoformat()}
            for t in notable
        ],
        "net_worth": str(net_worth),
        "subscription_monthly": str(sub_monthly.quantize(Decimal("0.01"))),
        "component_type": "weekly_summary",
    }


def _get_goals(user, params):
    from transactions.models import Goal
    goals = Goal.objects.filter(user=user)
    return {
        "goals": [
            {
                "id": g.id,
                "name": g.name,
                "target_amount": str(g.target_amount),
                "current_amount": str(g.current_amount),
                "target_date": g.target_date.isoformat() if g.target_date else None,
                "progress_pct": round(g.progress_pct, 1),
            }
            for g in goals
        ],
        "count": goals.count(),
    }


def _create_goal(user, params):
    from transactions.models import Goal
    goal = Goal.objects.create(
        user=user,
        name=params["name"],
        target_amount=params["target_amount"],
        current_amount=params.get("current_amount", 0),
        target_date=params.get("target_date"),
    )
    return {
        "goal": {
            "id": goal.id,
            "name": goal.name,
            "target_amount": str(goal.target_amount),
            "current_amount": str(goal.current_amount),
            "target_date": goal.target_date.isoformat() if goal.target_date else None,
        },
        "message": f"Created goal '{goal.name}' with target ${goal.target_amount}",
    }


def _get_budgets(user, params):
    from datetime import timedelta

    from django.db.models import Sum
    from django.utils import timezone

    from transactions.models import Budget, Transaction
    from transactions.serializers import BudgetSerializer

    qs = Budget.objects.filter(user=user).select_related("category")
    if params.get("active_only", True):
        qs = qs.filter(is_active=True)

    # Precompute spent amounts to avoid N+1 queries in the serializer
    now = timezone.now()
    budgets_list = list(qs)
    for budget in budgets_list:
        if budget.period == "weekly":
            start = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
        elif budget.period == "annual":
            start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        txn_qs = Transaction.objects.filter(
            user=user, transaction_type="expense", date__gte=start.date(),
        )
        if budget.category:
            txn_qs = txn_qs.filter(category=budget.category)
        budget._precomputed_spent = txn_qs.aggregate(total=Sum("amount"))["total"] or 0

    serializer = BudgetSerializer(budgets_list, many=True)
    budgets = serializer.data
    return {
        "budgets": budgets,
        "count": len(budgets),
    }


def _set_budget(user, params):
    from transactions.models import Budget, Category
    amount = params.get("amount")
    period = params.get("period", "monthly")
    category_name = params.get("category_name")

    category = None
    if category_name:
        category = Category.objects.filter(name__iexact=category_name).first()
        if not category:
            return {"error": f"Category '{category_name}' not found. Use get_spending_summary to see available categories."}

    budget, created = Budget.objects.update_or_create(
        user=user,
        category=category,
        defaults={"amount": amount, "period": period, "is_active": True},
    )
    from transactions.serializers import BudgetSerializer
    return {
        "budget": BudgetSerializer(budget).data,
        "created": created,
        "message": f"{'Created' if created else 'Updated'} {category.name if category else 'total'} budget: ${amount}/{period}",
    }


TOOL_HANDLERS = {
    "get_accounts": _get_accounts,
    "query_transactions": _query_transactions,
    "get_spending_summary": _get_spending_summary,
    "get_dashboard_summary": _get_dashboard_summary,
    "get_portfolio_holdings": _get_portfolio_holdings,
    "get_portfolio_allocation": _get_portfolio_allocation,
    "get_news_articles": _get_news_articles,
    "search_security": _search_security,
    "get_tax_years": _get_tax_years,
    # Phase 1: Receipts & Expenses
    "get_receipts": _get_receipts,
    "create_expense_from_receipt": _create_expense_from_receipt,
    "generate_expense_report": _generate_expense_report,
    # Phase 2: Tax Estimation
    "estimate_taxes": _estimate_taxes,
    "compare_filing_statuses": _compare_filing_statuses,
    # Phase 3: Tax Prep
    "scan_transactions_for_deductions": _scan_transactions_for_deductions,
    "create_deduction_from_transactions": _create_deduction_from_transactions,
    "get_tax_prep_checklist": _get_tax_prep_checklist,
    # Phase 1A: Plaid/Bank Integration
    "link_bank_account": _link_bank_account,
    "sync_accounts": _sync_accounts,
    # Phase 1B: Email Integration
    "connect_email": _connect_email,
    "scan_email_now": _scan_email_now,
    "get_email_receipts": _get_email_receipts,
    # Phase 2: Subscriptions
    "get_subscriptions": _get_subscriptions,
    "get_subscription_spending": _get_subscription_spending,
    # Phase 3: Cancellation
    "cancel_subscription": _cancel_subscription,
    "track_cancellation": _track_cancellation,
    # Phase 3: Tax Prep Automation
    "prepare_tax_filing": _prepare_tax_filing,
    "generate_schedule_c": _generate_schedule_c,
    "find_missed_deductions": _find_missed_deductions,
    "export_tax_summary": _export_tax_summary,
    # Alerts
    "get_alerts": _get_alerts,
    # Portfolio Performance
    "get_portfolio_performance": _get_portfolio_performance,
    # Weekly Summary
    "get_weekly_summary": _get_weekly_summary,
    # Budgets
    "get_budgets": _get_budgets,
    "set_budget": _set_budget,
    # Goals
    "get_goals": _get_goals,
    "create_goal": _create_goal,
}
