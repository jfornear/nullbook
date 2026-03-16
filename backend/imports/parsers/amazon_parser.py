"""Amazon Order History CSV parser.

Parses the "Retail.OrderHistory.1.csv" file from Amazon's
"Request My Data" (GDPR/CCPA) export.
"""

import csv
import io
from datetime import datetime
from decimal import Decimal, InvalidOperation


def parse_amazon_orders(file_content: str) -> dict:
    """Parse an Amazon Order History CSV.

    Returns:
        {
            "orders": [...],
            "order_count": int,
            "date_range": {"start": str, "end": str},
        }
    """
    reader = csv.DictReader(io.StringIO(file_content))
    orders = []
    errors = []

    for i, row in enumerate(reader):
        try:
            order = _parse_order_row(row, i)
            if order:
                orders.append(order)
        except Exception as e:
            errors.append(f"Row {i + 1}: {str(e)}")

    # Sort by date
    orders.sort(key=lambda o: o["order_date"])

    date_range = {}
    if orders:
        date_range = {
            "start": orders[0]["order_date"],
            "end": orders[-1]["order_date"],
        }

    return {
        "orders": orders,
        "order_count": len(orders),
        "date_range": date_range,
        "errors": errors,
    }


def _parse_order_row(row: dict, row_num: int) -> dict | None:
    """Parse a single Amazon order row.

    Amazon's export has varying column names depending on when the export
    was generated. We handle common variants.
    """
    # Try various column name patterns for date
    date_str = (
        row.get("Order Date")
        or row.get("order date")
        or row.get("OrderDate")
        or ""
    ).strip()

    if not date_str:
        return None

    # Parse date - Amazon uses various formats
    order_date = None
    for fmt in ["%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y", "%Y-%m-%dT%H:%M:%S"]:
        try:
            order_date = datetime.strptime(date_str.split("T")[0].split(" ")[0], fmt.split("T")[0]).date()
            break
        except ValueError:
            continue

    if order_date is None:
        return None

    # Product name
    product_name = (
        row.get("Title")
        or row.get("Product Name")
        or row.get("title")
        or row.get("Item Description")
        or ""
    ).strip()

    # Order ID
    order_id = (
        row.get("Order ID")
        or row.get("order id")
        or row.get("OrderId")
        or ""
    ).strip()

    # ASIN
    asin = (
        row.get("ASIN")
        or row.get("asin")
        or ""
    ).strip()

    # Amount
    amount_str = (
        row.get("Total Owed")
        or row.get("Purchase Price Per Unit")
        or row.get("Item Total")
        or row.get("total_owed")
        or row.get("Total Charged")
        or "0"
    ).strip()

    try:
        amount = Decimal(amount_str.replace("$", "").replace(",", ""))
    except (InvalidOperation, ValueError):
        amount = Decimal("0")

    # Quantity
    qty_str = (row.get("Quantity") or row.get("quantity") or "1").strip()
    try:
        quantity = int(qty_str)
    except ValueError:
        quantity = 1

    # Category
    category = (
        row.get("Category")
        or row.get("category")
        or ""
    ).strip()

    return {
        "order_date": order_date.isoformat(),
        "order_id": order_id,
        "product_name": product_name,
        "asin": asin,
        "total_amount": str(amount),
        "quantity": quantity,
        "category": category,
    }
