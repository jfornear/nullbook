import re

# Map Plaid account types/subtypes to local Account.ACCOUNT_TYPES
PLAID_ACCOUNT_TYPE_MAP = {
    # Depository
    "checking": "checking",
    "savings": "savings",
    "hsa": "savings",
    "cd": "savings",
    "money market": "savings",
    "paypal": "checking",
    "prepaid": "checking",
    "cash management": "checking",
    "ebt": "checking",
    # Credit
    "credit card": "credit_card",
    # Loan
    "auto": "loan",
    "business": "loan",
    "commercial": "loan",
    "construction": "loan",
    "consumer": "loan",
    "home equity": "loan",
    "line of credit": "loan",
    "loan": "loan",
    "mortgage": "mortgage",
    "overdraft": "loan",
    "student": "loan",
    # Investment
    "401a": "investment",
    "401k": "investment",
    "403B": "investment",
    "457b": "investment",
    "529": "investment",
    "brokerage": "investment",
    "cash isa": "investment",
    "crypto exchange": "investment",
    "education savings account": "investment",
    "fixed annuity": "investment",
    "gic": "investment",
    "health reimbursement arrangement": "investment",
    "ira": "investment",
    "isa": "investment",
    "keogh": "investment",
    "lif": "investment",
    "life insurance": "investment",
    "lira": "investment",
    "lrif": "investment",
    "lrsp": "investment",
    "mutual fund": "investment",
    "non-custodial wallet": "investment",
    "non-taxable brokerage account": "investment",
    "other": "investment",
    "other annuity": "investment",
    "other insurance": "investment",
    "pension": "investment",
    "prif": "investment",
    "profit sharing plan": "investment",
    "rdsp": "investment",
    "resp": "investment",
    "retirement": "investment",
    "rlif": "investment",
    "roth": "investment",
    "roth 401k": "investment",
    "rrif": "investment",
    "rrsp": "investment",
    "sarsep": "investment",
    "sep ira": "investment",
    "simple ira": "investment",
    "sipp": "investment",
    "stock plan": "investment",
    "tfsa": "investment",
    "trust": "investment",
    "ugma": "investment",
    "utma": "investment",
    "variable annuity": "investment",
}

# Map Plaid top-level account type to local type
PLAID_TYPE_FALLBACK_MAP = {
    "depository": "checking",
    "credit": "credit_card",
    "loan": "loan",
    "mortgage": "mortgage",
    "investment": "investment",
    "other": "other",
}

# Map Plaid personal_finance_category to local Category names
PLAID_CATEGORY_MAP = {
    "INCOME": "Income",
    "INCOME_DIVIDENDS": "Dividends",
    "INCOME_INTEREST_EARNED": "Interest",
    "INCOME_RETIREMENT_PENSION": "Retirement Income",
    "INCOME_TAX_REFUND": "Tax Refund",
    "INCOME_UNEMPLOYMENT": "Income",
    "INCOME_WAGES": "Salary",
    "INCOME_OTHER_INCOME": "Income",
    "TRANSFER_IN": "Transfer",
    "TRANSFER_OUT": "Transfer",
    "TRANSFER_IN_ACCOUNT_TRANSFER": "Transfer",
    "TRANSFER_OUT_ACCOUNT_TRANSFER": "Transfer",
    "TRANSFER_IN_CASH_ADVANCES_AND_LOANS": "Transfer",
    "TRANSFER_OUT_CASH_ADVANCES_AND_LOANS": "Transfer",
    "TRANSFER_IN_DEPOSIT": "Transfer",
    "TRANSFER_OUT_WITHDRAWAL": "Transfer",
    "TRANSFER_IN_INVESTMENT_AND_RETIREMENT_FUNDS": "Transfer",
    "TRANSFER_OUT_INVESTMENT_AND_RETIREMENT_FUNDS": "Transfer",
    "TRANSFER_IN_SAVINGS": "Transfer",
    "TRANSFER_OUT_SAVINGS": "Transfer",
    "TRANSFER_IN_OTHER_TRANSFER_IN": "Transfer",
    "TRANSFER_OUT_OTHER_TRANSFER_OUT": "Transfer",
    "LOAN_PAYMENTS": "Loan Payment",
    "LOAN_PAYMENTS_CAR_PAYMENT": "Auto Payment",
    "LOAN_PAYMENTS_CREDIT_CARD_PAYMENT": "Credit Card Payment",
    "LOAN_PAYMENTS_MORTGAGE_PAYMENT": "Mortgage Payment",
    "LOAN_PAYMENTS_STUDENT_LOAN_PAYMENT": "Student Loan Payment",
    "LOAN_PAYMENTS_OTHER_PAYMENT": "Loan Payment",
    "BANK_FEES": "Bank Fees",
    "BANK_FEES_ATM_FEES": "ATM Fees",
    "BANK_FEES_FOREIGN_TRANSACTION_FEES": "Bank Fees",
    "BANK_FEES_INSUFFICIENT_FUNDS": "Bank Fees",
    "BANK_FEES_INTEREST_CHARGE": "Interest",
    "BANK_FEES_OVERDRAFT_FEES": "Bank Fees",
    "BANK_FEES_OTHER_BANK_FEES": "Bank Fees",
    "ENTERTAINMENT": "Entertainment",
    "ENTERTAINMENT_CASINOS_AND_GAMBLING": "Entertainment",
    "ENTERTAINMENT_MUSIC_AND_AUDIO": "Entertainment",
    "ENTERTAINMENT_SPORTING_EVENTS_AMUSEMENT_PARKS_AND_MUSEUMS": "Entertainment",
    "ENTERTAINMENT_TV_AND_MOVIES": "Entertainment",
    "ENTERTAINMENT_VIDEO_GAMES": "Entertainment",
    "ENTERTAINMENT_OTHER_ENTERTAINMENT": "Entertainment",
    "FOOD_AND_DRINK": "Food & Drink",
    "FOOD_AND_DRINK_BEER_WINE_AND_LIQUOR": "Food & Drink",
    "FOOD_AND_DRINK_COFFEE": "Coffee",
    "FOOD_AND_DRINK_FAST_FOOD": "Fast Food",
    "FOOD_AND_DRINK_GROCERIES": "Groceries",
    "FOOD_AND_DRINK_RESTAURANT": "Restaurants",
    "FOOD_AND_DRINK_VENDING_MACHINES": "Food & Drink",
    "FOOD_AND_DRINK_OTHER_FOOD_AND_DRINK": "Food & Drink",
    "GENERAL_MERCHANDISE": "Shopping",
    "GENERAL_MERCHANDISE_BOOKSTORES_AND_NEWSSTANDS": "Shopping",
    "GENERAL_MERCHANDISE_CLOTHING_AND_ACCESSORIES": "Clothing",
    "GENERAL_MERCHANDISE_CONVENIENCE_STORES": "Shopping",
    "GENERAL_MERCHANDISE_DEPARTMENT_STORES": "Shopping",
    "GENERAL_MERCHANDISE_DISCOUNT_STORES": "Shopping",
    "GENERAL_MERCHANDISE_ELECTRONICS": "Electronics",
    "GENERAL_MERCHANDISE_GIFTS_AND_NOVELTIES": "Gifts",
    "GENERAL_MERCHANDISE_OFFICE_SUPPLIES": "Office Supplies",
    "GENERAL_MERCHANDISE_ONLINE_MARKETPLACES": "Shopping",
    "GENERAL_MERCHANDISE_PET_SUPPLIES": "Pets",
    "GENERAL_MERCHANDISE_SPORTING_GOODS": "Shopping",
    "GENERAL_MERCHANDISE_SUPERSTORES": "Shopping",
    "GENERAL_MERCHANDISE_TOBACCO_AND_VAPE": "Shopping",
    "GENERAL_MERCHANDISE_OTHER_GENERAL_MERCHANDISE": "Shopping",
    "HOME_IMPROVEMENT": "Home Improvement",
    "HOME_IMPROVEMENT_FURNITURE": "Furniture",
    "HOME_IMPROVEMENT_HARDWARE": "Home Improvement",
    "HOME_IMPROVEMENT_REPAIR_AND_MAINTENANCE": "Home Maintenance",
    "HOME_IMPROVEMENT_SECURITY": "Home Improvement",
    "HOME_IMPROVEMENT_OTHER_HOME_IMPROVEMENT": "Home Improvement",
    "MEDICAL": "Medical",
    "MEDICAL_DENTAL_CARE": "Dental",
    "MEDICAL_EYE_CARE": "Medical",
    "MEDICAL_NURSING_CARE": "Medical",
    "MEDICAL_PHARMACIES_AND_SUPPLEMENTS": "Pharmacy",
    "MEDICAL_PRIMARY_CARE": "Medical",
    "MEDICAL_VETERINARY_SERVICES": "Veterinary",
    "MEDICAL_OTHER_MEDICAL": "Medical",
    "PERSONAL_CARE": "Personal Care",
    "PERSONAL_CARE_GYMS_AND_FITNESS_CENTERS": "Fitness",
    "PERSONAL_CARE_HAIR_AND_BEAUTY": "Personal Care",
    "PERSONAL_CARE_LAUNDRY_AND_DRY_CLEANING": "Personal Care",
    "PERSONAL_CARE_OTHER_PERSONAL_CARE": "Personal Care",
    "GENERAL_SERVICES": "Services",
    "GENERAL_SERVICES_ACCOUNTING_AND_FINANCIAL_PLANNING": "Financial Services",
    "GENERAL_SERVICES_AUTOMOTIVE": "Auto Services",
    "GENERAL_SERVICES_CHILDCARE": "Childcare",
    "GENERAL_SERVICES_CONSULTING_AND_LEGAL": "Legal",
    "GENERAL_SERVICES_EDUCATION": "Education",
    "GENERAL_SERVICES_INSURANCE": "Insurance",
    "GENERAL_SERVICES_POSTAGE_AND_SHIPPING": "Shipping",
    "GENERAL_SERVICES_STORAGE": "Storage",
    "GENERAL_SERVICES_OTHER_GENERAL_SERVICES": "Services",
    "GOVERNMENT_AND_NON_PROFIT": "Government",
    "GOVERNMENT_AND_NON_PROFIT_DONATIONS": "Donations",
    "GOVERNMENT_AND_NON_PROFIT_GOVERNMENT_DEPARTMENTS_AND_AGENCIES": "Government",
    "GOVERNMENT_AND_NON_PROFIT_TAX_PAYMENT": "Taxes",
    "GOVERNMENT_AND_NON_PROFIT_OTHER_GOVERNMENT_AND_NON_PROFIT": "Government",
    "TRANSPORTATION": "Transportation",
    "TRANSPORTATION_BIKES_AND_SCOOTERS": "Transportation",
    "TRANSPORTATION_GAS": "Gas",
    "TRANSPORTATION_PARKING": "Parking",
    "TRANSPORTATION_PUBLIC_TRANSIT": "Public Transit",
    "TRANSPORTATION_TAXIS_AND_RIDE_SHARES": "Rideshare",
    "TRANSPORTATION_TOLLS": "Tolls",
    "TRANSPORTATION_OTHER_TRANSPORTATION": "Transportation",
    "TRAVEL": "Travel",
    "TRAVEL_FLIGHTS": "Flights",
    "TRAVEL_LODGING": "Hotels",
    "TRAVEL_RENTAL_CARS": "Rental Cars",
    "TRAVEL_OTHER_TRAVEL": "Travel",
    "RENT_AND_UTILITIES": "Bills & Utilities",
    "RENT_AND_UTILITIES_GAS_AND_ELECTRICITY": "Utilities",
    "RENT_AND_UTILITIES_INTERNET_AND_CABLE": "Internet",
    "RENT_AND_UTILITIES_RENT": "Rent",
    "RENT_AND_UTILITIES_SEWAGE_AND_WASTE_MANAGEMENT": "Utilities",
    "RENT_AND_UTILITIES_TELEPHONE": "Phone",
    "RENT_AND_UTILITIES_WATER": "Utilities",
    "RENT_AND_UTILITIES_OTHER_UTILITIES": "Utilities",
}

# Merchant name prefixes to strip
MERCHANT_PREFIXES = [
    r"^SQ \*",
    r"^SQC\*",
    r"^TST\*",
    r"^TST \*",
    r"^PAYPAL \*",
    r"^PP\*",
    r"^VENMO \*",
    r"^ZELLE \*",
    r"^CASH APP\*",
    r"^GOOGLE \*",
    r"^APPLE\.COM/",
    r"^AMZN Mktp ",
    r"^Amazon\.com\*",
    r"^AMAZON\.COM\*",
    r"^CKE\*",
    r"^IN \*",
    r"^SP \*",
    r"^DoorDash\*",
    r"^DD \*",
    r"^UBER \*TRIP",
    r"^UBER \*EATS",
    r"^LYF\*",
]
_PREFIX_RE = re.compile("|".join(MERCHANT_PREFIXES), re.IGNORECASE)


def map_plaid_account_type(plaid_type, plaid_subtype=None):
    """Map a Plaid account type/subtype to a local Account account_type.

    Args:
        plaid_type: Plaid account type string (e.g. "depository", "credit").
        plaid_subtype: Plaid account subtype string (e.g. "checking", "savings").

    Returns:
        str: One of the Account.ACCOUNT_TYPES values.
    """
    if plaid_subtype:
        subtype_lower = str(plaid_subtype).lower()
        if subtype_lower in PLAID_ACCOUNT_TYPE_MAP:
            return PLAID_ACCOUNT_TYPE_MAP[subtype_lower]

    type_lower = str(plaid_type).lower()
    return PLAID_TYPE_FALLBACK_MAP.get(type_lower, "other")


def map_plaid_category(plaid_category):
    """Map a Plaid personal_finance_category to a local Category name.

    Args:
        plaid_category: Plaid personal_finance_category dict with
            'primary' and optional 'detailed' keys.

    Returns:
        str: Local category name, or "Uncategorized" if no match.
    """
    if not plaid_category:
        return "Uncategorized"

    # Try detailed category first (e.g. "FOOD_AND_DRINK_GROCERIES")
    detailed = plaid_category.get("detailed", "")
    if detailed and detailed in PLAID_CATEGORY_MAP:
        return PLAID_CATEGORY_MAP[detailed]

    # Fall back to primary category (e.g. "FOOD_AND_DRINK")
    primary = plaid_category.get("primary", "")
    if primary and primary in PLAID_CATEGORY_MAP:
        return PLAID_CATEGORY_MAP[primary]

    return "Uncategorized"


def normalize_merchant_name(name):
    """Clean up a merchant name by stripping common POS/payment prefixes.

    Args:
        name: Raw merchant name string.

    Returns:
        str: Cleaned merchant name.
    """
    if not name:
        return ""

    cleaned = _PREFIX_RE.sub("", name).strip()

    # Remove trailing transaction IDs (common pattern: "STORE NAME #1234")
    # but keep meaningful store numbers
    cleaned = re.sub(r"\s+#\d{6,}$", "", cleaned)

    # Collapse multiple spaces
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    return cleaned
