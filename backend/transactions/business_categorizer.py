"""Business expense categorizer for Schedule C / tax preparation.

Keyword-based rules for categorizing transactions into tax-relevant
categories. Ported from the ad-hoc 2025/process_expenses.py script
into a reusable module.
"""


def categorize_for_schedule_c(
    description: str,
    bank_category: str = "",
    amount: float = 0,
    date=None,
) -> str:
    """Categorize a transaction for Schedule C tax purposes.

    Args:
        description: Transaction description / merchant name.
        bank_category: Bank-provided category (e.g., Chase "Food & Drink").
        amount: Transaction amount (positive = income, negative = expense).
        date: Transaction date (unused currently, reserved for future rules).

    Returns:
        Tax category string (e.g., "Software & SaaS", "Travel - Airfare").
    """
    d = description.upper()

    # Skip non-expense rows
    if amount > 0:
        return "INCOME / PAYMENT"

    # -- Travel --
    if any(k in d for k in [
        "AIRLINE", "DELTA", "UNITED", "SOUTHWEST", "AMERICAN AIR",
        "FRONTIER", "JETBLUE", "SPIRIT", "ALLEGIANT", "TSA",
        "FLIGHT", "AVIANCA",
    ]):
        return "Travel - Airfare"

    if any(k in d for k in [
        "HOTEL", "MARRIOTT", "HILTON", "HYATT", "IHG", "MOTEL",
        "AIRBNB", "VRBO", "BOOKING.COM", "EXPEDIA", "BEST WESTERN",
        "HOLIDAY INN", "COMFORT INN", "HAMPTON", "RESIDENCE INN",
        "LODG", "SUPER 8",
    ]):
        return "Travel - Lodging"

    if any(k in d for k in [
        "UBER", "LYFT", "TAXI", "CAB ", "LIMOUSINE", "RENTAL CAR",
        "HERTZ", "ENTERPRISE", "AVIS", "BUDGET RENT", "NATIONAL CAR",
        "TURO",
    ]):
        return "Travel - Transport"

    if any(k in d for k in ["PARKING", "PARK "]) and "PARK CITY" not in d:
        return "Travel - Parking"

    if any(k in d for k in [
        "GAS ", "FUEL", "SHELL ", "CHEVRON", "EXXON", "BP ",
        "CIRCLE K", "LOVES ", "PILOT ", "KWICK", "SAMS FUEL",
        "COSTCO GAS", "CONOCO", "PHILLIPS 66", "SINCLAIR",
        "MAVERIK", "MARATHON", "WAWA", "QT ", "QUIKTRIP",
        "KWIK", "7-ELEVEN GAS", "RACETRAC", "SPEEDWAY",
        "CASEY", "MURPHYUSA", "MURPHY USA",
    ]):
        return "Travel - Gas/Fuel"

    # -- Meals --
    if any(k in d for k in [
        "RESTAURANT", "GRUBHUB", "DOORDASH", "UBER EATS",
        "MCDONALD", "STARBUCKS", "CHICK-FIL", "CHIPOTLE",
        "PANERA", "SUBWAY", "WENDY", "TACO BELL", "PIZZA",
        "BURGER", "DINER", "CAFE", "COFFEE", "BAKERY",
        "PANDA EXPRESS", "KFC", "POPEYES", "FIVE GUYS",
        "IN-N-OUT", "WHATABURGER", "ARBY", "SONIC ",
        "WAFFLE", "IHOP", "DENNY", "APPLEBEE", "CHILI",
        "OLIVE GARDEN", "OUTBACK", "RED ROBIN",
        "CANES", "BUFFALO WILD", "WINGSTOP", "NOODLES",
        "SWEETGREEN", "MOD PIZZA", "BLAZE PIZZA",
        "FIREHOUSE", "JERSEY MIKE", "JIMMY JOHN",
        "POTBELLY", "JASON DELI", "MCALISTER",
        "CRUMBL", "INSOMNIA COOKIE", "SMOOTHIE",
        "JAMBA", "TROPICAL SMOOTH", "DUTCH BROS",
        "SCOOTER", "BIGGBY", "CARIBOU", "PEET",
        "BREWPUB", "BREW PUB", "TAPROOM", "TAP ROOM",
        "GRILL", "EATERY", "KITCHEN", "BISTRO",
        "CANTINA", "TAQUERIA", "SUSHI", "RAMEN",
        "PHO ", "BOBA", "BUBBLE TEA",
        "SQ *", "TST*",
    ]) or bank_category == "Food & Drink":
        return "Meals & Entertainment"

    # -- Software / SaaS --
    if any(k in d for k in [
        "GITHUB", "DIGITALOCEAN", "AWS ", "AMAZON WEB",
        "HEROKU", "NETLIFY", "VERCEL", "FIREBASE",
        "GOOGLE *GSUITE", "GOOGLE *CLOUD", "OPENAI",
        "ANTHROPIC", "STRIPE", "TWILIO", "SENDGRID",
        "MAILGUN", "POSTMARK", "SENTRY", "DATADOG",
        "CLOUDFLARE", "NAMECHEAP", "DNSIMPLE", "GODADDY",
        "HOVER", "GANDI", "1PASSWORD", "LASTPASS",
        "BITWARDEN", "NORDVPN", "EXPRESSVPN", "SURFSHARK",
        "NOTION", "SLACK", "ZOOM", "FIGMA", "CANVA",
        "ADOBE", "JETBRAINS", "VSCODE", "CURSOR",
        "REPLIT", "CODESPACE", "COPILOT",
        "PADDLE.NET", "GUMROAD", "LEMON SQUEEZY",
        "RENDER", "RAILWAY", "FLY.IO", "SUPABASE",
        "PLANETSCALE", "NEON ", "MONGO", "REDIS",
        "ELASTIC", "ALGOLIA", "MAPBOX", "TWITCH",
        "SPOTIFY FOR", "CHATGPT", "PERPLEXITY",
        "LINEAR", "JIRA", "ASANA", "TRELLO",
        "AIRTABLE", "BASECAMP", "CLOCKIFY", "TOGGL",
        "FRESHBOOKS", "QUICKBOOKS", "XERO",
        "DROPBOX", "ICLOUD", "GOOGLE *STORAGE",
        "BACKBLAZE", "WASABI", "HETZNER",
        "LINODE", "VULTR", "CONTABO",
        "MOCKUUUPS", "SCREENSTUDIO",
    ]):
        return "Software & SaaS"

    # -- Internet / Phone --
    if any(k in d for k in [
        "COMCAST", "XFINITY", "SPECTRUM", "ATT ", "AT&T",
        "VERIZON", "T-MOBILE", "TMOBILE", "SPRINT",
        "CENTURYLINK", "LUMEN", "COX COMM",
        "GOOGLE FI", "MINT MOBILE", "VISIBLE",
        "CRICKET", "STARLINK",
    ]):
        return "Internet & Phone"

    # -- Office supplies / equipment --
    if any(k in d for k in [
        "APPLE.COM", "APPLE STORE", "BEST BUY",
        "MICRO CENTER", "B&H PHOTO", "NEWEGG",
        "AMAZON", "AMZN",
    ]) and bank_category in ["Shopping", "Electronics"]:
        return "Equipment & Supplies"

    # -- Subscriptions / media --
    if any(k in d for k in [
        "AUDIBLE", "KINDLE", "AMAZON PRIME",
        "YOUTUBE PREMIUM", "LINKEDIN PREMIUM",
        "MEDIUM.COM", "SUBSTACK", "OREILLY",
        "PLURALSIGHT", "UDEMY", "COURSERA",
        "SKILLSHARE", "MASTERCLASS", "EGGHEAD",
    ]):
        return "Education & Subscriptions"

    # -- Advertising / marketing --
    if any(k in d for k in [
        "FACEBOOK ADS", "META ADS", "GOOGLE ADS",
        "FACEBK", "INSTAGRAM", "TIKTOK ADS",
        "TWITTER ADS", "LINKEDIN ADS", "REDDIT ADS",
        "APPLE SEARCH", "BING ADS",
        "MAILCHIMP", "CONVERTKIT", "HUBSPOT",
        "BUFFER", "HOOTSUITE", "SPROUT SOCIAL",
    ]):
        return "Advertising & Marketing"

    # -- Insurance --
    if any(k in d for k in [
        "INSURANCE", "GEICO", "PROGRESSIVE", "STATE FARM",
        "ALLSTATE", "USAA", "LIBERTY MUTUAL",
        "NATIONWIDE", "TRAVELERS",
    ]):
        return "Insurance"

    # -- Professional services --
    if bank_category == "Professional Services" or any(k in d for k in [
        "LEGAL", "ATTORNEY", "LAW OFFICE", "CPA ", "ACCOUNTANT",
        "TAX PREP", "H&R BLOCK", "TURBOTAX", "INTUIT",
    ]):
        return "Professional Services"

    # -- Catch-all by bank category --
    cat_map = {
        "Bills & Utilities": "Bills & Utilities",
        "Entertainment": "Meals & Entertainment",
        "Gas": "Travel - Gas/Fuel",
        "Groceries": "Groceries (Review for Business Use)",
        "Health & Wellness": "Health & Wellness",
        "Home": "Home (Personal)",
        "Personal": "Personal",
        "Shopping": "Shopping (Review for Business Use)",
        "Travel": "Travel - Other",
        "Automotive": "Automotive",
        "Gifts & Donations": "Gifts & Donations",
        "Fees & Adjustments": "Fees & Adjustments",
    }
    return cat_map.get(bank_category, "Uncategorized (Review)")


def batch_categorize_for_taxes(user, tax_year: int, limit: int = 5000) -> dict:
    """Run business categorization on all uncategorized expense transactions for a tax year.

    Returns:
        dict with categorized count and category summary.
    """
    from collections import defaultdict

    from transactions.models import Transaction

    transactions = Transaction.objects.filter(
        user=user,
        transaction_type="expense",
        date__year=tax_year,
    ).select_related("category")[:limit]

    categorized = 0
    category_counts = defaultdict(int)
    category_totals = defaultdict(float)

    for txn in transactions:
        # Use bank category from the transaction's notes or category name
        bank_cat = txn.category.name if txn.category else ""
        tax_cat = categorize_for_schedule_c(
            txn.description,
            bank_category=bank_cat,
            amount=-float(txn.amount),  # expenses stored as positive
        )
        if tax_cat not in ("INCOME / PAYMENT", "Uncategorized (Review)"):
            categorized += 1
            category_counts[tax_cat] += 1
            category_totals[tax_cat] += float(txn.amount)

    summary = [
        {"category": cat, "count": category_counts[cat], "total": f"{category_totals[cat]:.2f}"}
        for cat in sorted(category_counts, key=lambda c: category_totals[c], reverse=True)
    ]

    return {
        "tax_year": tax_year,
        "total_transactions": len(transactions),
        "categorized": categorized,
        "categories": summary,
    }
