"""Pure Python federal tax calculation engine. No Django dependencies."""

from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP

D = Decimal


@dataclass
class TaxInput:
    filing_status: str = "single"
    tax_year: int = 2025

    # W-2 income
    w2_income: Decimal = D("0")
    federal_withheld: Decimal = D("0")
    state_withheld: Decimal = D("0")
    ss_withheld: Decimal = D("0")
    medicare_withheld: Decimal = D("0")

    # 1099 income
    interest_income: Decimal = D("0")          # 1099-INT
    ordinary_dividends: Decimal = D("0")       # 1099-DIV
    qualified_dividends: Decimal = D("0")      # 1099-DIV qualified portion
    short_term_gains: Decimal = D("0")         # 1099-B
    long_term_gains: Decimal = D("0")          # 1099-B
    self_employment_income: Decimal = D("0")   # 1099-NEC
    other_income: Decimal = D("0")             # 1099-MISC, K-1, etc.

    # Itemized deductions
    mortgage_interest: Decimal = D("0")
    state_local_tax: Decimal = D("0")
    charitable: Decimal = D("0")
    medical: Decimal = D("0")
    business_expenses: Decimal = D("0")
    education: Decimal = D("0")

    # Above-the-line deductions
    ira_contributions: Decimal = D("0")
    hsa_contributions: Decimal = D("0")
    se_health_insurance: Decimal = D("0")


@dataclass
class TaxBreakdown:
    gross_income: Decimal = D("0")
    agi: Decimal = D("0")
    taxable_income: Decimal = D("0")

    standard_deduction: Decimal = D("0")
    itemized_deduction: Decimal = D("0")
    deduction_used: str = "standard"  # "standard" or "itemized"

    bracket_details: list = field(default_factory=list)
    ordinary_tax: Decimal = D("0")
    ltcg_tax: Decimal = D("0")

    self_employment_tax: Decimal = D("0")
    qbi_deduction: Decimal = D("0")
    amt_estimate: Decimal = D("0")

    total_tax: Decimal = D("0")
    total_withheld: Decimal = D("0")
    amount_owed: Decimal = D("0")  # Negative means refund

    effective_rate: Decimal = D("0")
    marginal_rate: Decimal = D("0")


# --- 2025 Tax Constants ---

STANDARD_DEDUCTIONS = {
    "single": D("15000"),
    "married_joint": D("30000"),
    "married_separate": D("15000"),
    "head_of_household": D("22500"),
}

# Federal income tax brackets (2025)
BRACKETS = {
    "single": [
        (D("11925"), D("0.10")),
        (D("48475"), D("0.12")),
        (D("103350"), D("0.22")),
        (D("197300"), D("0.24")),
        (D("250525"), D("0.32")),
        (D("626350"), D("0.35")),
        (D("999999999"), D("0.37")),
    ],
    "married_joint": [
        (D("23850"), D("0.10")),
        (D("96950"), D("0.12")),
        (D("206700"), D("0.22")),
        (D("394600"), D("0.24")),
        (D("501050"), D("0.32")),
        (D("751600"), D("0.35")),
        (D("999999999"), D("0.37")),
    ],
    "married_separate": [
        (D("11925"), D("0.10")),
        (D("48475"), D("0.12")),
        (D("103350"), D("0.22")),
        (D("197300"), D("0.24")),
        (D("250525"), D("0.32")),
        (D("375800"), D("0.35")),
        (D("999999999"), D("0.37")),
    ],
    "head_of_household": [
        (D("17000"), D("0.10")),
        (D("64850"), D("0.12")),
        (D("103350"), D("0.22")),
        (D("197300"), D("0.24")),
        (D("250500"), D("0.32")),
        (D("626350"), D("0.35")),
        (D("999999999"), D("0.37")),
    ],
}

# Long-term capital gains brackets (2025)
LTCG_BRACKETS = {
    "single": [
        (D("48350"), D("0.00")),
        (D("533400"), D("0.15")),
        (D("999999999"), D("0.20")),
    ],
    "married_joint": [
        (D("96700"), D("0.00")),
        (D("600050"), D("0.15")),
        (D("999999999"), D("0.20")),
    ],
    "married_separate": [
        (D("48350"), D("0.00")),
        (D("300025"), D("0.15")),
        (D("999999999"), D("0.20")),
    ],
    "head_of_household": [
        (D("64750"), D("0.00")),
        (D("566700"), D("0.15")),
        (D("999999999"), D("0.20")),
    ],
}

SALT_CAP = D("10000")
SS_WAGE_BASE = D("176100")
SS_RATE = D("0.124")
MEDICARE_RATE = D("0.029")
ADDITIONAL_MEDICARE_RATE = D("0.009")
ADDITIONAL_MEDICARE_THRESHOLDS = {
    "single": D("200000"),
    "married_joint": D("250000"),
    "married_separate": D("125000"),
    "head_of_household": D("200000"),
}
SE_TAX_FACTOR = D("0.9235")  # 92.35% of SE income is taxable
SE_DEDUCTION_FACTOR = D("0.5")  # Deduct half of SE tax

# QBI (Section 199A) thresholds
QBI_THRESHOLDS = {
    "single": D("191950"),
    "married_joint": D("383900"),
    "married_separate": D("191950"),
    "head_of_household": D("191950"),
}

# AMT
AMT_EXEMPTIONS = {
    "single": D("88100"),
    "married_joint": D("137000"),
    "married_separate": D("68500"),
    "head_of_household": D("88100"),
}
AMT_PHASEOUT = {
    "single": D("609350"),
    "married_joint": D("1047200"),
    "married_separate": D("523600"),
    "head_of_household": D("609350"),
}


def _round(amount: Decimal) -> Decimal:
    return amount.quantize(D("0.01"), rounding=ROUND_HALF_UP)


def _apply_brackets(taxable: Decimal, brackets: list) -> tuple[Decimal, list]:
    """Apply progressive tax brackets. Returns (total_tax, bracket_details)."""
    tax = D("0")
    details = []
    prev_limit = D("0")

    for limit, rate in brackets:
        bracket_income = min(taxable, limit) - prev_limit
        if bracket_income <= 0:
            break
        bracket_tax = _round(bracket_income * rate)
        tax += bracket_tax
        details.append({
            "bracket": _round(bracket_income),
            "rate": rate,
            "tax": bracket_tax,
        })
        prev_limit = limit

    return tax, details


def calculate_taxes(ti: TaxInput) -> TaxBreakdown:
    """Calculate federal taxes for a given TaxInput."""
    result = TaxBreakdown()
    fs = ti.filing_status

    # --- Gross Income ---
    result.gross_income = (
        ti.w2_income
        + ti.interest_income
        + ti.ordinary_dividends
        + ti.short_term_gains
        + ti.long_term_gains
        + ti.self_employment_income
        + ti.other_income
    )

    # --- Self-Employment Tax ---
    se_taxable = _round(ti.self_employment_income * SE_TAX_FACTOR)
    ss_base = min(se_taxable, SS_WAGE_BASE)

    # If also has W-2, reduce SS base by W-2 wages (SS wage base is shared)
    ss_remaining = max(SS_WAGE_BASE - ti.w2_income, D("0"))
    ss_base = min(se_taxable, ss_remaining)

    se_ss_tax = _round(ss_base * SS_RATE)
    se_medicare_tax = _round(se_taxable * MEDICARE_RATE)
    result.self_employment_tax = se_ss_tax + se_medicare_tax

    # Additional Medicare on SE income
    medicare_threshold = ADDITIONAL_MEDICARE_THRESHOLDS.get(fs, D("200000"))
    combined_wages = ti.w2_income + se_taxable
    if combined_wages > medicare_threshold:
        additional_medicare_base = min(se_taxable, combined_wages - medicare_threshold)
        additional_medicare_base = max(additional_medicare_base, D("0"))
        result.self_employment_tax += _round(additional_medicare_base * ADDITIONAL_MEDICARE_RATE)

    se_deduction = _round(result.self_employment_tax * SE_DEDUCTION_FACTOR)

    # --- AGI ---
    above_the_line = (
        se_deduction
        + ti.ira_contributions
        + ti.hsa_contributions
        + ti.se_health_insurance
    )
    result.agi = max(result.gross_income - above_the_line, D("0"))

    # --- Deductions ---
    result.standard_deduction = STANDARD_DEDUCTIONS.get(fs, D("15000"))

    # Itemized deductions
    salt_deduction = min(ti.state_local_tax, SALT_CAP)
    medical_floor = _round(result.agi * D("0.075"))
    medical_deduction = max(ti.medical - medical_floor, D("0"))

    result.itemized_deduction = (
        ti.mortgage_interest
        + salt_deduction
        + ti.charitable
        + medical_deduction
        + ti.business_expenses
        + ti.education
    )

    if result.itemized_deduction > result.standard_deduction:
        deduction = result.itemized_deduction
        result.deduction_used = "itemized"
    else:
        deduction = result.standard_deduction
        result.deduction_used = "standard"

    # --- QBI Deduction ---
    qbi_threshold = QBI_THRESHOLDS.get(fs, D("191950"))
    if ti.self_employment_income > 0 and result.agi <= qbi_threshold:
        qbi_income = ti.self_employment_income - se_deduction
        result.qbi_deduction = _round(max(qbi_income * D("0.20"), D("0")))
    else:
        result.qbi_deduction = D("0")

    # --- Taxable Income ---
    # Separate ordinary income from LTCG/qualified dividends for preferential rates
    ordinary_income = (
        result.agi
        - ti.long_term_gains
        - ti.qualified_dividends
        - deduction
        - result.qbi_deduction
    )
    ordinary_income = max(ordinary_income, D("0"))

    result.taxable_income = max(result.agi - deduction - result.qbi_deduction, D("0"))

    # --- Ordinary Income Tax ---
    brackets = BRACKETS.get(fs, BRACKETS["single"])
    result.ordinary_tax, result.bracket_details = _apply_brackets(ordinary_income, brackets)

    # --- LTCG + Qualified Dividends Tax ---
    preferential_income = ti.long_term_gains + ti.qualified_dividends
    if preferential_income > 0:
        ltcg_brackets = LTCG_BRACKETS.get(fs, LTCG_BRACKETS["single"])
        # LTCG brackets are based on total taxable income
        # The preferential income "stacks" on top of ordinary income
        ltcg_tax = D("0")
        prev_limit = D("0")
        for limit, rate in ltcg_brackets:
            # How much room is left in this bracket after ordinary income
            bracket_start = max(ordinary_income, prev_limit)
            bracket_end = limit
            if bracket_start >= bracket_end:
                prev_limit = limit
                continue
            room = bracket_end - bracket_start
            preferential_in_bracket = min(preferential_income, room)
            if preferential_in_bracket <= 0:
                prev_limit = limit
                continue
            ltcg_tax += _round(preferential_in_bracket * rate)
            preferential_income -= preferential_in_bracket
            prev_limit = limit
            if preferential_income <= 0:
                break
        result.ltcg_tax = ltcg_tax

    # --- AMT Estimate ---
    amt_exemption = AMT_EXEMPTIONS.get(fs, D("88100"))
    amt_phaseout = AMT_PHASEOUT.get(fs, D("609350"))
    amti = result.agi - deduction + salt_deduction  # Add back SALT for AMT
    if amti > amt_phaseout:
        exemption_reduction = _round((amti - amt_phaseout) * D("0.25"))
        amt_exemption = max(amt_exemption - exemption_reduction, D("0"))
    amt_taxable = max(amti - amt_exemption, D("0"))
    if amt_taxable > D("239100"):
        amt_tax = _round(D("239100") * D("0.26") + (amt_taxable - D("239100")) * D("0.28"))
    else:
        amt_tax = _round(amt_taxable * D("0.26"))
    regular_tax = result.ordinary_tax + result.ltcg_tax
    result.amt_estimate = max(amt_tax - regular_tax, D("0"))

    # --- Total Tax ---
    result.total_tax = _round(
        result.ordinary_tax
        + result.ltcg_tax
        + result.self_employment_tax
        + result.amt_estimate
    )

    # --- Withholding & Balance ---
    result.total_withheld = (
        ti.federal_withheld
        + ti.ss_withheld
        + ti.medicare_withheld
    )
    result.amount_owed = _round(result.total_tax - result.total_withheld)

    # --- Rates ---
    if result.gross_income > 0:
        result.effective_rate = _round(result.total_tax / result.gross_income * 100)
    # Marginal rate: the bracket rate of the last dollar
    if result.bracket_details:
        result.marginal_rate = result.bracket_details[-1]["rate"] * 100

    return result
