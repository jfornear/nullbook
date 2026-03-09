"""Receipt OCR processing via LLM Vision API."""

import base64
import json
import logging
from decimal import Decimal, InvalidOperation
from pathlib import Path

logger = logging.getLogger(__name__)


def process_receipt_image(receipt_id):
    """Read a receipt image, call LLM Vision to extract structured data, and update the Receipt."""
    from chat.llm_client import LLMClient
    from .models import Receipt, ReceiptLineItem

    try:
        receipt = Receipt.objects.get(id=receipt_id)
    except Receipt.DoesNotExist:
        logger.error("Receipt %s not found", receipt_id)
        return

    receipt.status = "processing"
    receipt.save(update_fields=["status"])

    try:
        file_path = receipt.image.path
        suffix = Path(file_path).suffix.lower()
        media_type_map = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".webp": "image/webp",
            ".pdf": "application/pdf",
        }
        media_type = media_type_map.get(suffix, "image/jpeg")

        with open(file_path, "rb") as f:
            file_data = base64.standard_b64encode(f.read()).decode("utf-8")

        llm = LLMClient()

        extraction_prompt = """Analyze this receipt and extract the following information as JSON:

{
  "merchant": "Store/restaurant name",
  "date": "YYYY-MM-DD format or null",
  "total_amount": 0.00,
  "subtotal": 0.00,
  "tax_amount": 0.00,
  "tip_amount": 0.00,
  "currency": "USD",
  "payment_method": "cash/credit/debit/other or empty string",
  "category": "one of: food, groceries, transportation, gas, shopping, entertainment, health, home, office, travel, utilities, business, other",
  "line_items": [
    {
      "description": "Item name",
      "quantity": 1,
      "unit_price": 0.00,
      "total_price": 0.00,
      "category": "optional category"
    }
  ]
}

Rules:
- Return ONLY valid JSON, no other text
- Use null for fields you cannot determine
- Amounts should be numbers, not strings
- Date must be YYYY-MM-DD or null
- Extract as many line items as visible"""

        raw_text = llm.vision_extract(
            image_data=file_data,
            media_type=media_type,
            prompt=extraction_prompt,
        )
        # Try to extract JSON from the response
        json_text = raw_text.strip()
        if json_text.startswith("```"):
            # Strip markdown code fences
            lines = json_text.split("\n")
            lines = [line for line in lines if not line.strip().startswith("```")]
            json_text = "\n".join(lines)

        data = json.loads(json_text)
        receipt.raw_ocr_data = data

        # Populate fields
        receipt.merchant = (data.get("merchant") or "")[:200]
        if data.get("date"):
            try:
                from datetime import date as date_type
                parts = str(data["date"]).split("-")
                receipt.date = date_type(int(parts[0]), int(parts[1]), int(parts[2]))
            except (ValueError, IndexError):
                pass

        for field in ("total_amount", "subtotal", "tax_amount", "tip_amount"):
            val = data.get(field)
            if val is not None:
                try:
                    setattr(receipt, field, Decimal(str(val)))
                except (InvalidOperation, ValueError):
                    pass

        receipt.currency = (data.get("currency") or "USD")[:3]
        receipt.payment_method = (data.get("payment_method") or "")[:50]
        receipt.category = data.get("category") or ""
        receipt.status = "completed"
        receipt.save()

        # Create line items
        for item in data.get("line_items", []):
            try:
                total_price = Decimal(str(item.get("total_price", 0)))
                unit_price = None
                if item.get("unit_price") is not None:
                    unit_price = Decimal(str(item["unit_price"]))
                quantity = Decimal(str(item.get("quantity", 1)))

                ReceiptLineItem.objects.create(
                    receipt=receipt,
                    description=(item.get("description") or "Unknown")[:300],
                    quantity=quantity,
                    unit_price=unit_price,
                    total_price=total_price,
                    category=(item.get("category") or "")[:50],
                )
            except (InvalidOperation, ValueError, TypeError):
                continue

        logger.info("Receipt %s processed successfully: %s", receipt_id, receipt.merchant)

    except json.JSONDecodeError as e:
        receipt.status = "failed"
        receipt.error_message = f"Failed to parse OCR response: {e}"
        receipt.save(update_fields=["status", "error_message"])
        logger.exception("Receipt %s OCR parse error", receipt_id)
    except Exception as e:
        receipt.status = "failed"
        receipt.error_message = str(e)[:500]
        receipt.save(update_fields=["status", "error_message"])
        logger.exception("Receipt %s processing failed", receipt_id)
