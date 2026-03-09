# Tax Prep Assistant

AI-guided tax preparation workflow through the chat interface. The assistant walks users through filing status, document collection, deduction review, and tax estimation.

## System Prompt Behavior

The tax-specific guidance is embedded in the chat system prompt (`backend/chat/streaming.py`). Key directives:

- When a receipt image is uploaded, describe what you see and confirm it's being processed
- Guide users through a structured tax preparation process when asked
- Proactively suggest missed deductions by scanning transactions
- Always compare standard vs. itemized deductions and recommend the better option
- For self-employed users, explain SE tax and QBI deduction
- Flag AMT risk, estimated payment requirements, and SALT cap impacts
- Always disclaim: estimates only — consult a tax professional

## Chat Tool: `get_tax_prep_checklist`

Returns a structured checklist showing tax preparation progress.

**Parameters:** `tax_year` (required)

### Checklist Sections

**1. Filing Status**

- Whether a filing status has been selected
- Shows the current status (Single, Married Filing Jointly, etc.)

**2. Income Documents**

- W-2 (always shown — expected if user has checking/savings accounts)
- 1099-B, 1099-DIV, 1099-INT (shown if user has investment accounts)
- 1099-NEC (shown if already uploaded)
- 1098 (shown if user has mortgage/loan accounts)
- Status: `complete` if uploaded, `review` if expected but missing

**3. Deductions**

- Mortgage Interest, State & Local Taxes, Charitable Donations, Medical Expenses, Business Expenses
- Status: `complete` with claimed amount, or `review` if not yet addressed

**4. Review**

- All income documents uploaded (complete/incomplete)
- Deductions reviewed (complete/incomplete)
- Transaction scan for missed deductions (always `review` — prompts user to run the scan)

### Progress Tracking

```json
{
  "progress": {
    "complete": 5,
    "total": 12,
    "percentage": 42
  }
}
```

Items with `status: "complete"` count toward progress. The checklist infers expected documents from the user's linked account types (e.g., investment accounts suggest 1099-B/DIV/INT).

Renders as the **TaxChecklist** component (`component_type: "tax_checklist"`).

## Typical User Workflow

### 1. Start tax preparation

> "Help me prepare my 2025 taxes"

The assistant asks about filing status and creates/updates the TaxYear. Suggests running the checklist.

### 2. Upload tax documents

The user adds W-2s, 1099s, and other documents via the tax documents API or tells the assistant about them. The assistant uses `get_tax_years` to verify what's been entered.

### 3. Upload receipts for deductions

User uploads receipt images through:

- **Chat**: Attach via paperclip button or drag-and-drop
- **Import > Receipts tab**: Dedicated view for bulk uploads

OCR runs automatically. Once completed, the assistant can convert receipts to deductions using `create_expense_from_receipt`.

### 4. Scan transactions for missed deductions

> "Scan my transactions for any deductible expenses"

The assistant calls `scan_transactions_for_deductions`, which matches transaction categories/descriptions against the `CATEGORY_DEDUCTION_MAP`. The DeductionSuggestions component shows results with "Add" buttons.

### 5. Run tax estimate

> "Estimate my taxes"

The assistant calls `estimate_taxes`, which builds a `TaxInput` from all documents and deductions, runs the tax engine, and displays the TaxEstimateCard with bracket chart, breakdown, and refund/owed amount.

### 6. Compare filing statuses

> "Which filing status would be best for me?"

The assistant calls `compare_filing_statuses`, which calculates taxes for all 4 statuses and shows the FilingComparison grid with the optimal status highlighted.

### 7. Review checklist for completeness

> "How's my tax prep looking?"

The assistant calls `get_tax_prep_checklist` and shows the TaxChecklist component with progress bar and section-by-section status.

## Frontend Component

### TaxChecklist (`frontend/src/components/chat/rich/TaxChecklist.tsx`)

Rendered for `component_type: "tax_checklist"`. Shows:

- **Header**: Tax year title + progress fraction (e.g., "5/12 (42%)")
- **Progress bar**: Green fill proportional to completion percentage
- **Sections**: Each section has a heading and a list of items
- **Item states**:
  - `complete` — green CheckCircle2 icon
  - `incomplete` — gray Circle icon
  - `review` — amber AlertCircle icon
- Each item shows a label and detail text (e.g., "2 uploaded" or "$4,500.00 claimed")

## All Tax & Expense Chat Tools (Summary)

| Tool                                 | Purpose                                  | Component            |
| ------------------------------------ | ---------------------------------------- | -------------------- |
| `get_receipts`                       | List receipts with filters               | ReceiptsList         |
| `create_expense_from_receipt`        | Convert receipt → deduction              | ReceiptCard          |
| `generate_expense_report`            | Categorized deduction summary            | ExpenseReport        |
| `estimate_taxes`                     | Full federal tax estimate                | TaxEstimateCard      |
| `compare_filing_statuses`            | Compare all 4 statuses                   | FilingComparison     |
| `scan_transactions_for_deductions`   | Find unclaimed deductions                | DeductionSuggestions |
| `create_deduction_from_transactions` | Batch-create deduction from transactions | (text response)      |
| `get_tax_prep_checklist`             | Progress checklist                       | TaxChecklist         |

## Related Documentation

- [Receipt Scanner & OCR](./receipts.md) — Receipt upload, OCR, and management
- [Expense & Deduction Tracking](./expense-tracking.md) — Deductions, expense reports, transaction scanning
- [Tax Calculation Engine](./tax-engine.md) — Tax brackets, SE tax, QBI, AMT
