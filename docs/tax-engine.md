# Tax Calculation Engine

Pure Python 2025 federal tax calculator with no Django dependencies. Located at `backend/taxes/tax_engine.py`.

## TaxInput

Dataclass holding all input fields for a tax calculation.

```python
@dataclass
class TaxInput:
    filing_status: str = "single"
    tax_year: int = 2025

    # W-2 income
    w2_income: Decimal = 0
    federal_withheld: Decimal = 0
    state_withheld: Decimal = 0
    ss_withheld: Decimal = 0
    medicare_withheld: Decimal = 0

    # 1099 income
    interest_income: Decimal = 0          # 1099-INT
    ordinary_dividends: Decimal = 0       # 1099-DIV
    qualified_dividends: Decimal = 0      # 1099-DIV qualified portion
    short_term_gains: Decimal = 0         # 1099-B
    long_term_gains: Decimal = 0          # 1099-B
    self_employment_income: Decimal = 0   # 1099-NEC
    other_income: Decimal = 0             # 1099-MISC, K-1, etc.

    # Itemized deductions
    mortgage_interest: Decimal = 0
    state_local_tax: Decimal = 0
    charitable: Decimal = 0
    medical: Decimal = 0
    business_expenses: Decimal = 0
    education: Decimal = 0

    # Above-the-line deductions
    ira_contributions: Decimal = 0
    hsa_contributions: Decimal = 0
    se_health_insurance: Decimal = 0
```

## TaxBreakdown

Dataclass returned by `calculate_taxes()` with all computed results.

| Field                 | Description                                                    |
| --------------------- | -------------------------------------------------------------- |
| `gross_income`        | Sum of all income sources                                      |
| `agi`                 | Gross income minus above-the-line deductions                   |
| `taxable_income`      | AGI minus the better of standard/itemized deduction, minus QBI |
| `standard_deduction`  | Standard deduction for filing status                           |
| `itemized_deduction`  | Computed itemized total                                        |
| `deduction_used`      | `"standard"` or `"itemized"`                                   |
| `bracket_details`     | List of `{bracket, rate, tax}` for each bracket used           |
| `ordinary_tax`        | Tax on ordinary income                                         |
| `ltcg_tax`            | Tax on long-term gains + qualified dividends                   |
| `self_employment_tax` | SS + Medicare on SE income                                     |
| `qbi_deduction`       | Section 199A deduction                                         |
| `amt_estimate`        | Alternative Minimum Tax if applicable                          |
| `total_tax`           | ordinary + LTCG + SE + AMT                                     |
| `total_withheld`      | federal + SS + Medicare withholding                            |
| `amount_owed`         | total_tax - total_withheld (negative = refund)                 |
| `effective_rate`      | total_tax / gross_income as percentage                         |
| `marginal_rate`       | Rate of the highest bracket reached                            |

## 2025 Tax Brackets

### Ordinary Income

| Bracket | Single              | Married Joint       | Married Separate    | Head of Household   |
| ------- | ------------------- | ------------------- | ------------------- | ------------------- |
| 10%     | $0 – $11,925        | $0 – $23,850        | $0 – $11,925        | $0 – $17,000        |
| 12%     | $11,925 – $48,475   | $23,850 – $96,950   | $11,925 – $48,475   | $17,000 – $64,850   |
| 22%     | $48,475 – $103,350  | $96,950 – $206,700  | $48,475 – $103,350  | $64,850 – $103,350  |
| 24%     | $103,350 – $197,300 | $206,700 – $394,600 | $103,350 – $197,300 | $103,350 – $197,300 |
| 32%     | $197,300 – $250,525 | $394,600 – $501,050 | $197,300 – $250,525 | $197,300 – $250,500 |
| 35%     | $250,525 – $626,350 | $501,050 – $751,600 | $250,525 – $375,800 | $250,500 – $626,350 |
| 37%     | $626,350+           | $751,600+           | $375,800+           | $626,350+           |

### Standard Deductions

| Filing Status             | Amount  |
| ------------------------- | ------- |
| Single                    | $15,000 |
| Married Filing Jointly    | $30,000 |
| Head of Household         | $22,500 |
| Married Filing Separately | $15,000 |

### Long-Term Capital Gains / Qualified Dividends

| Rate | Single             | Married Joint      | Married Separate   | Head of Household  |
| ---- | ------------------ | ------------------ | ------------------ | ------------------ |
| 0%   | $0 – $48,350       | $0 – $96,700       | $0 – $48,350       | $0 – $64,750       |
| 15%  | $48,350 – $533,400 | $96,700 – $600,050 | $48,350 – $300,025 | $64,750 – $566,700 |
| 20%  | $533,400+          | $600,050+          | $300,025+          | $566,700+          |

LTCG/qualified dividends "stack" on top of ordinary income when applying bracket thresholds.

## Calculation Details

### Self-Employment Tax

- **Taxable base**: 92.35% of SE income (`SE_TAX_FACTOR = 0.9235`)
- **Social Security**: 12.4% on taxable base up to SS wage base ($176,100), reduced by any W-2 wages
- **Medicare**: 2.9% on full taxable base
- **Additional Medicare**: 0.9% on combined wages + SE income above threshold ($200k single, $250k MFJ, $125k MFS)
- **SE deduction**: Half of total SE tax is deducted above-the-line from AGI

### QBI Deduction (Section 199A)

- 20% of qualified business income (SE income minus half of SE tax)
- Only applies when AGI is at or below the threshold:
  - $191,950 for single/HoH/MFS
  - $383,900 for MFJ
- Not calculated above the threshold (simplified; doesn't implement phase-out)

### Itemized Deductions

- **SALT cap**: State & local tax deduction capped at $10,000
- **Medical floor**: Only amounts exceeding 7.5% of AGI are deductible
- **Other**: Mortgage interest, charitable, business expenses, and education are taken at face value
- Engine automatically picks the higher of standard vs. itemized

### Alternative Minimum Tax (AMT)

| Constant        | Single   | Married Joint | Married Separate | Head of Household |
| --------------- | -------- | ------------- | ---------------- | ----------------- |
| Exemption       | $88,100  | $137,000      | $68,500          | $88,100           |
| Phaseout starts | $609,350 | $1,047,200    | $523,600         | $609,350          |

- AMTI = AGI - deduction + SALT add-back
- Exemption phases out at 25 cents per dollar above phaseout threshold
- AMT rates: 26% on first $239,100, then 28%
- AMT = max(AMT tax - regular tax, 0)

### Above-the-Line Deductions

Subtracted from gross income to calculate AGI:

- Half of SE tax (auto-calculated)
- IRA contributions
- HSA contributions
- Self-employed health insurance

## How Documents Map to TaxInput

The `_build_tax_input()` function in `backend/chat/tools.py` maps stored `TaxDocument` and `DeductibleExpense` records to `TaxInput` fields:

| Document Type | TaxInput Field(s)                                    | Details JSON Keys                                                        |
| ------------- | ---------------------------------------------------- | ------------------------------------------------------------------------ |
| W-2           | `w2_income` (amount), withholding fields             | `federal_withheld`, `state_withheld`, `ss_withheld`, `medicare_withheld` |
| 1099-INT      | `interest_income`                                    | —                                                                        |
| 1099-DIV      | `ordinary_dividends` (amount), `qualified_dividends` | `qualified_dividends`                                                    |
| 1099-B        | `short_term_gains`, `long_term_gains`                | `short_term`, `long_term` (defaults to all long-term if both zero)       |
| 1099-NEC      | `self_employment_income`                             | —                                                                        |
| 1099-MISC     | `other_income`                                       | —                                                                        |
| K-1           | `other_income`                                       | —                                                                        |
| 1098          | (not mapped to income)                               | Mortgage interest handled via deductions                                 |

| Deduction Type                       | TaxInput Field                                       |
| ------------------------------------ | ---------------------------------------------------- |
| `mortgage_interest`                  | `mortgage_interest`                                  |
| `state_local_tax`                    | `state_local_tax`                                    |
| `charitable`                         | `charitable`                                         |
| `medical`                            | `medical`                                            |
| `business`, `home_office`, `vehicle` | `business_expenses`                                  |
| `education`                          | `education`                                          |
| `retirement`                         | `ira_contributions`                                  |
| `insurance`                          | (not mapped; SE health insurance handled separately) |

## Chat Tools

### `estimate_taxes`

Calculates a full federal tax estimate for a tax year.

**Parameters:** `tax_year` (required)

Builds `TaxInput` from the user's documents and deductions, runs `calculate_taxes()`, and returns the full breakdown. Renders as the **TaxEstimateCard** component (`component_type: "tax_estimate"`).

### `compare_filing_statuses`

Runs `calculate_taxes()` for all 4 filing statuses and identifies the optimal one (lowest total tax).

**Parameters:** `tax_year` (required)

Returns an array of breakdowns plus `optimal_status`. Renders as the **FilingComparison** component (`component_type: "filing_comparison"`).

## Frontend Components

### TaxEstimateCard (`frontend/src/components/chat/rich/TaxEstimateCard.tsx`)

Rendered for `component_type: "tax_estimate"`. Sections:

1. **Refund/Owed banner**: Green (refund) or red (owed) with large dollar amount
2. **Income summary**: Gross income, AGI, taxable income
3. **Deductions**: Standard vs. itemized with checkmark on the one used, plus QBI if applicable
4. **Bracket chart**: Recharts `BarChart` with color-coded bars (green → red) per bracket showing tax amount
5. **Tax breakdown**: Ordinary tax, LTCG tax, SE tax, AMT (with warning icon), total tax, total withheld
6. **Rates**: Effective rate and marginal rate
7. **Disclaimer**: "This is an estimate only. Consult a tax professional for official filing."

### FilingComparison (`frontend/src/components/chat/rich/FilingComparison.tsx`)

Rendered for `component_type: "filing_comparison"`. Shows:

- **2x2 grid** of filing status cards (responsive: 1-col on mobile, 2-col on sm+)
- **Optimal status**: Highlighted with green border/background and "Best" badge
- Each card shows: total tax, refund/owed (color-coded), effective rate, deduction type used
- **Disclaimer**: "Your actual eligibility for each status depends on your household situation."

## Limitations & Disclaimer

- **Federal only** — no state tax calculations
- **No tax credits** — child tax credit, EITC, education credits, etc. are not implemented
- **Simplified QBI** — no phase-out above threshold, no W-2 wages/UBIA limitations
- **Simplified AMT** — does not account for ISO exercises, foreign tax credits, etc.
- **Estimate only** — always displayed with a disclaimer to consult a tax professional
