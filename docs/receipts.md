# Receipt Scanner & OCR

Upload receipt images and let AI extract structured data (merchant, amounts, line items) automatically. Processed receipts can be converted into tax deductions.

## Models

### Receipt (`backend/taxes/models.py`)

| Field                | Type                   | Notes                                             |
| -------------------- | ---------------------- | ------------------------------------------------- |
| `user`               | FK → User              | Owner                                             |
| `image`              | ImageField             | Uploaded to `receipts/%Y/%m/`                     |
| `status`             | CharField              | `pending` → `processing` → `completed` / `failed` |
| `merchant`           | CharField(200)         | OCR-extracted store name                          |
| `date`               | DateField              | OCR-extracted receipt date                        |
| `total_amount`       | Decimal(12,2)          | Total including tax + tip                         |
| `subtotal`           | Decimal(12,2)          | Pre-tax subtotal                                  |
| `tax_amount`         | Decimal(12,2)          | Sales tax                                         |
| `tip_amount`         | Decimal(12,2)          | Tip                                               |
| `currency`           | CharField(3)           | Default `USD`                                     |
| `payment_method`     | CharField(50)          | cash/credit/debit/other                           |
| `category`           | CharField(30)          | One of 13 categories (see below)                  |
| `raw_ocr_data`       | JSONField              | Full extraction response                          |
| `transaction`        | FK → Transaction       | Optional link to imported transaction             |
| `deductible_expense` | FK → DeductibleExpense | Set when converted to deduction                   |
| `tax_year`           | FK → TaxYear           | Set when converted to deduction                   |
| `error_message`      | TextField              | Populated on failure                              |

**Category choices:** `food`, `groceries`, `transportation`, `gas`, `shopping`, `entertainment`, `health`, `home`, `office`, `travel`, `utilities`, `business`, `other`

### ReceiptLineItem (`backend/taxes/models.py`)

| Field         | Type           | Notes                        |
| ------------- | -------------- | ---------------------------- |
| `receipt`     | FK → Receipt   | Parent receipt               |
| `description` | CharField(300) | Item name                    |
| `quantity`    | Decimal(10,3)  | Default 1                    |
| `unit_price`  | Decimal(12,2)  | Nullable                     |
| `total_price` | Decimal(12,2)  | Required                     |
| `category`    | CharField(50)  | Optional item-level category |

### Status Lifecycle

```
pending → processing → completed
                    ↘ failed
```

- **pending**: Receipt uploaded, waiting for Celery worker
- **processing**: OCR call in progress
- **completed**: Data extracted and saved
- **failed**: OCR or parsing error; `error_message` has details

## OCR Service (`backend/taxes/services.py`)

Uses the configured LLM provider's vision model (Claude Sonnet by default, or Ollama if `LLM_PROVIDER=ollama`).

**Flow:**

1. Read image from disk, base64-encode it
2. Send to the LLM vision model with a structured extraction prompt
3. Parse JSON response into Receipt fields + ReceiptLineItem rows
4. Handle markdown code fences in response (` ```json ``` `)

**Extracted fields:**

```json
{
  "merchant": "Store name",
  "date": "YYYY-MM-DD",
  "total_amount": 42.5,
  "subtotal": 38.0,
  "tax_amount": 4.5,
  "tip_amount": 0.0,
  "currency": "USD",
  "payment_method": "credit",
  "category": "food",
  "line_items": [
    {
      "description": "Coffee",
      "quantity": 2,
      "unit_price": 4.5,
      "total_price": 9.0,
      "category": "food"
    }
  ]
}
```

**Error handling:**

- `json.JSONDecodeError` → status `failed`, error saved
- Any other exception → status `failed`, error message truncated to 500 chars

## Celery Task (`backend/taxes/tasks.py`)

```python
@shared_task
def process_receipt_task(receipt_id):
```

Wraps `process_receipt_image()` in a Celery task. Fired automatically on receipt upload (both from API and chat).

## API Endpoints

All under `/api/taxes/receipts/` (DRF `ModelViewSet`, requires authentication).

| Method      | Path                                       | Description                                                                      |
| ----------- | ------------------------------------------ | -------------------------------------------------------------------------------- |
| `GET`       | `/api/taxes/receipts/`                     | List user's receipts (with line items prefetched)                                |
| `POST`      | `/api/taxes/receipts/`                     | Upload receipt image → kicks off OCR                                             |
| `GET`       | `/api/taxes/receipts/{id}/`                | Retrieve single receipt                                                          |
| `PUT/PATCH` | `/api/taxes/receipts/{id}/`                | Update receipt fields                                                            |
| `DELETE`    | `/api/taxes/receipts/{id}/`                | Delete receipt                                                                   |
| `POST`      | `/api/taxes/receipts/{id}/create_expense/` | Convert to DeductibleExpense (requires `tax_year_id`, optional `deduction_type`) |
| `POST`      | `/api/taxes/receipts/{id}/reprocess/`      | Reset to `pending` and re-run OCR                                                |

**`create_expense` action** requires the receipt to have `status=completed`. Returns 400 if still processing. Creates a `DeductibleExpense`, links it back to the receipt, and sets the receipt's `tax_year`.

**`reprocess` action** clears `error_message`, sets status to `pending`, and fires `process_receipt_task.delay()`.

## Chat Tools

### `get_receipts`

Lists the user's receipts. Supports filters:

- `status` — `pending`, `processing`, `completed`, `failed`
- `date_from` / `date_to` — filter by receipt date (YYYY-MM-DD)
- `merchant` — case-insensitive search

Returns up to 50 receipts. Renders as the **ReceiptsList** component (`component_type: "receipts_list"`).

### `create_expense_from_receipt`

Converts a processed receipt into a `DeductibleExpense`. Parameters:

- `receipt_id` (required) — ID of a completed receipt
- `tax_year` (required) — e.g. 2025
- `deduction_type` (optional, default `"business"`) — one of the 12 deduction types

Auto-creates the TaxYear if it doesn't exist. Renders as the **ReceiptCard** component (`component_type: "receipt_card"`).

## Frontend Components

### ReceiptCard (`frontend/src/components/chat/rich/ReceiptCard.tsx`)

Inline chat card shown after `create_expense_from_receipt`. Displays:

- Merchant name and total amount (green highlight)
- Deduction type badge
- Receipt date and tax year
- Line items table (if available)

### ReceiptsList (`frontend/src/components/chat/rich/ReceiptsList.tsx`)

Inline chat card shown after `get_receipts`. Displays:

- Receipt count header
- Each receipt as a row with merchant, date, category, amount, and status badge
- Status badges: `completed` (default), `processing` (secondary), `pending` (outline), `failed` (destructive)

### Receipts tab (`frontend/src/pages/Receipts.tsx`)

Accessible via the **Import** section in the app modal (Receipts tab).

**Features:**

- **Upload area**: Drag-and-drop or click-to-upload with loading spinner
- **Status filter buttons**: All / completed / processing / pending / failed
- **Receipt grid**: 2-column grid showing image thumbnails, merchant, amount, and status badge
- Uses React Query (`queryKey: ["receipts"]`) to load data
- Upload via `useMutation` with CSRF token and form data POST

### ChatInput (`frontend/src/components/chat/ChatInput.tsx`)

The main chat input supports receipt image attachments:

- **Paperclip button**: Opens file picker (accepts `.jpg`, `.jpeg`, `.png`, `.webp`, `.gif`)
- **Drag-and-drop**: Drop area highlights with dashed border
- **Image preview**: 64x64 thumbnail with remove button
- **Default message**: If image is attached with no text, sends `"Here's a receipt image."`

When the message+image is sent, the backend (`streaming.py`) both:

1. Creates a `Receipt` and fires OCR via `process_receipt_task`
2. Passes the image to the LLM vision model as part of the conversation

## User Flow

1. **Upload**: Drag a receipt image into the chat input (or use the Paperclip button, or upload via the Import > Receipts tab)
2. **OCR runs**: Celery picks up the task, calls the vision model, extracts structured data
3. **Review**: Ask the assistant to show receipts (`get_receipts`) or check the Import > Receipts tab
4. **Convert to deduction**: Ask the assistant to create an expense from the receipt, or use the `/create_expense/` API action
5. **Reprocess**: If OCR failed, use the `/reprocess/` endpoint to retry
