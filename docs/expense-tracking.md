# Expense & Deduction Tracking

Track deductible expenses linked to tax years. Deductions can come from receipts, manual entry, or automated transaction scanning.

## Model

### DeductibleExpense (`backend/taxes/models.py`)

| Field            | Type           | Notes                                     |
| ---------------- | -------------- | ----------------------------------------- |
| `tax_year`       | FK → TaxYear   | Required                                  |
| `receipt`        | FK → Receipt   | Nullable; set when created from a receipt |
| `deduction_type` | CharField(30)  | One of 12 types (see below)               |
| `description`    | CharField(500) | Free-text description                     |
| `amount`         | Decimal(12,2)  | Deduction amount                          |
| `is_verified`    | BooleanField   | Default `False`                           |
| `created_at`     | DateTimeField  | Auto-set                                  |

**Ordering:** by `-amount` (largest first).

### Deduction Types

| Value               | Display Name             |
| ------------------- | ------------------------ |
| `standard`          | Standard Deduction       |
| `mortgage_interest` | Mortgage Interest        |
| `state_local_tax`   | State & Local Tax        |
| `charitable`        | Charitable Donations     |
| `medical`           | Medical Expenses         |
| `business`          | Business Expenses        |
| `education`         | Education                |
| `home_office`       | Home Office              |
| `vehicle`           | Vehicle                  |
| `insurance`         | Insurance                |
| `retirement`        | Retirement Contributions |
| `other`             | Other                    |

## API Endpoints

All under `/api/taxes/deductions/` (DRF `ModelViewSet`, requires authentication).

| Method      | Path                          | Description               |
| ----------- | ----------------------------- | ------------------------- |
| `GET`       | `/api/taxes/deductions/`      | List user's deductions    |
| `POST`      | `/api/taxes/deductions/`      | Create a deduction        |
| `GET`       | `/api/taxes/deductions/{id}/` | Retrieve single deduction |
| `PUT/PATCH` | `/api/taxes/deductions/{id}/` | Update deduction          |
| `DELETE`    | `/api/taxes/deductions/{id}/` | Delete deduction          |

Queryset is scoped to `tax_year__user=request.user`.

## Chat Tools

### `generate_expense_report`

Generates a categorized deduction summary for a tax year.

**Parameters:** `tax_year` (required, e.g. 2025)

**Response shape:**

```json
{
  "tax_year": 2025,
  "filing_status": "single",
  "categories": [
    {
      "category": "Business Expenses",
      "total": "4500.00",
      "count": 8,
      "items": [
        {
          "id": 1,
          "description": "Office Supplies - 2025-03-15",
          "amount": "250.00",
          "is_verified": false
        }
      ]
    }
  ],
  "grand_total": "12500.00",
  "component_type": "expense_report"
}
```

Categories are sorted by total descending. Renders as the **ExpenseReport** component.

### `scan_transactions_for_deductions`

Scans the user's expense transactions for a given year to find potentially deductible spending that hasn't been claimed yet.

**Parameters:** `tax_year` (required)

**How it works:**

1. Queries all `expense` transactions for the year
2. Matches transaction category names and descriptions against `CATEGORY_DEDUCTION_MAP`
3. Compares totals against existing deductions by type
4. Returns only categories where `unclaimed_amount > 0`

**Response shape:**

```json
{
  "tax_year": 2025,
  "suggestions": [
    {
      "deduction_type": "medical",
      "deduction_type_display": "Medical Expenses",
      "transaction_count": 12,
      "total_amount": "3200.00",
      "existing_claimed": "500.00",
      "unclaimed_amount": "2700.00",
      "transactions": [
        {
          "id": 42,
          "date": "2025-06-15",
          "description": "CVS Pharmacy",
          "amount": "45.00",
          "category_name": "Healthcare"
        }
      ]
    }
  ],
  "total_unclaimed": "5400.00",
  "component_type": "deduction_suggestions"
}
```

Each suggestion includes up to 10 sample transactions. Renders as the **DeductionSuggestions** component.

### `create_deduction_from_transactions`

Aggregates selected transactions into a single `DeductibleExpense`.

**Parameters:**

- `transaction_ids` (required) — array of transaction IDs
- `tax_year` (required)
- `deduction_type` (required) — e.g. `"medical"`
- `description` (optional) — auto-generated from first 3 transaction descriptions if omitted

Auto-creates TaxYear via `get_or_create` if needed. Sums the amounts of all matching transactions.

## Category-to-Deduction Mapping

Defined as `CATEGORY_DEDUCTION_MAP` in `backend/chat/tools.py`. Maps transaction category names (and description keywords) to deduction types:

| Transaction Category                                               | Deduction Type |
| ------------------------------------------------------------------ | -------------- |
| Medical, Healthcare, Doctor, Pharmacy, Dentist                     | `medical`      |
| Charitable, Donations, Charity                                     | `charitable`   |
| Education, Tuition, Books                                          | `education`    |
| Office, Office Supplies, Software, Business, Professional Services | `business`     |
| Home Improvement, Home Office                                      | `home_office`  |
| Gas, Auto, Car Maintenance, Parking                                | `vehicle`      |
| Insurance                                                          | `insurance`    |

Matching is case-insensitive and checks both `category.name` and `transaction.description`.

## Frontend Components

### ExpenseReport (`frontend/src/components/chat/rich/ExpenseReport.tsx`)

Rendered for `component_type: "expense_report"`. Shows:

- **Header**: Tax year title + grand total
- **Horizontal bar chart** (Recharts `BarChart`, vertical layout): One bar per category, colored distinctly
- **Category cards**: Each category shows name, total amount, and expense count

### DeductionSuggestions (`frontend/src/components/chat/rich/DeductionSuggestions.tsx`)

Rendered for `component_type: "deduction_suggestions"`. Shows:

- **Header**: "Potential Deductions Found" with total unclaimed badge
- **Per-category cards** with:
  - Deduction type name + transaction count + unclaimed amount
  - Up to 5 sample transactions (date, description, amount)
  - **"Add" button**: Uses `ChatActionContext` to send a follow-up message requesting `create_deduction_from_transactions`

The Add button calls `chatAction.sendMessage()` with a natural language request that includes the transaction IDs and deduction type, triggering the assistant to call the `create_deduction_from_transactions` tool.

**Empty state:** "No unclaimed deductions found in your transactions."
