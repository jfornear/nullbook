"""Coinbase transaction history CSV parser.

Parses Coinbase's "Transaction History" CSV export for crypto
tax lot tracking and capital gains calculation.
"""

import csv
import io
from datetime import datetime
from decimal import Decimal, InvalidOperation


def parse_coinbase_transactions(file_content: str) -> dict:
    """Parse a Coinbase transaction history CSV.

    Returns:
        {
            "transactions": [...],
            "transaction_count": int,
            "assets": {symbol: {"buys": n, "sells": n, "total_cost": ..., "total_proceeds": ...}},
            "tax_lots": [...],
        }
    """
    # Coinbase CSVs sometimes have header notes before the actual CSV
    lines = file_content.strip().split("\n")
    csv_start = 0
    for i, line in enumerate(lines):
        if line.startswith("Timestamp") or line.startswith("\"Timestamp"):
            csv_start = i
            break

    csv_content = "\n".join(lines[csv_start:])
    reader = csv.DictReader(io.StringIO(csv_content))

    transactions = []
    errors = []
    assets = {}

    for i, row in enumerate(reader):
        try:
            txn = _parse_coinbase_row(row, i)
            if txn:
                transactions.append(txn)
                _update_asset_summary(assets, txn)
        except Exception as e:
            errors.append(f"Row {i + 1}: {str(e)}")

    transactions.sort(key=lambda t: t["timestamp"])

    # Calculate tax lots using FIFO
    tax_lots = calculate_fifo_lots(transactions)

    return {
        "transactions": transactions,
        "transaction_count": len(transactions),
        "assets": _serialize_asset_summaries(assets),
        "tax_lots": tax_lots,
        "errors": errors,
    }


def _parse_coinbase_row(row: dict, row_num: int) -> dict | None:
    """Parse a single Coinbase transaction row."""
    timestamp_str = (row.get("Timestamp") or row.get("timestamp") or "").strip()
    if not timestamp_str:
        return None

    # Parse timestamp
    timestamp = None
    for fmt in [
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%d %H:%M:%S UTC",
        "%Y-%m-%d %H:%M:%S",
        "%m/%d/%Y",
    ]:
        try:
            timestamp = datetime.strptime(timestamp_str, fmt)
            break
        except ValueError:
            continue

    if timestamp is None:
        return None

    txn_type = (row.get("Transaction Type") or row.get("type") or "").strip().lower()
    asset = (row.get("Asset") or row.get("asset") or "").strip().upper()

    quantity_str = (row.get("Quantity Transacted") or row.get("quantity") or "0").strip()
    spot_price_str = (row.get("Spot Price at Transaction") or row.get("Spot Price") or "0").strip()
    subtotal_str = (row.get("Subtotal") or row.get("subtotal") or "0").strip()
    total_str = (row.get("Total (inclusive of fees and/or spread)") or row.get("Total") or "0").strip()
    fees_str = (row.get("Fees and/or Spread") or row.get("Fees") or "0").strip()
    notes = (row.get("Notes") or "").strip()

    def to_decimal(s):
        try:
            return Decimal(s.replace("$", "").replace(",", "").strip() or "0")
        except (InvalidOperation, ValueError):
            return Decimal("0")

    return {
        "timestamp": timestamp.isoformat(),
        "date": timestamp.date().isoformat(),
        "transaction_type": txn_type,
        "asset": asset,
        "quantity": str(to_decimal(quantity_str)),
        "spot_price": str(to_decimal(spot_price_str)),
        "subtotal": str(to_decimal(subtotal_str)),
        "total": str(to_decimal(total_str)),
        "fees": str(to_decimal(fees_str)),
        "notes": notes,
    }


def _update_asset_summary(assets: dict, txn: dict):
    """Update the per-asset summary with a transaction."""
    asset = txn["asset"]
    if asset not in assets:
        assets[asset] = {
            "buys": 0,
            "sells": 0,
            "total_cost": Decimal("0"),
            "total_proceeds": Decimal("0"),
            "total_quantity_bought": Decimal("0"),
            "total_quantity_sold": Decimal("0"),
        }

    summary = assets[asset]
    total = Decimal(txn["total"])
    quantity = Decimal(txn["quantity"])

    if txn["transaction_type"] in ("buy", "advanced trade buy"):
        summary["buys"] += 1
        summary["total_cost"] += total
        summary["total_quantity_bought"] += quantity
    elif txn["transaction_type"] in ("sell", "advanced trade sell"):
        summary["sells"] += 1
        summary["total_proceeds"] += total
        summary["total_quantity_sold"] += quantity


def _serialize_asset_summaries(assets: dict) -> dict:
    """Convert Decimal values in asset summaries to strings for JSON serialization."""
    serialized = {}
    for asset, summary in assets.items():
        serialized[asset] = {
            **summary,
            "total_cost": str(summary["total_cost"]),
            "total_proceeds": str(summary["total_proceeds"]),
            "total_quantity_bought": str(summary["total_quantity_bought"]),
            "total_quantity_sold": str(summary["total_quantity_sold"]),
        }
    return serialized


def calculate_fifo_lots(transactions: list[dict]) -> list[dict]:
    """Calculate tax lots using FIFO (First In, First Out) method.

    Returns a list of disposed lots with cost basis and gain/loss.
    """
    from datetime import date as date_cls

    # Build buy queues per asset
    buy_queues: dict[str, list] = {}
    tax_lots = []

    for txn in transactions:
        asset = txn["asset"]
        quantity = Decimal(txn["quantity"])
        total = Decimal(txn["total"])

        if txn["transaction_type"] in ("buy", "advanced trade buy", "receive"):
            if asset not in buy_queues:
                buy_queues[asset] = []
            cost_per_unit = total / quantity if quantity > 0 else Decimal("0")
            buy_queues[asset].append({
                "date": txn["date"],
                "quantity": quantity,
                "cost_per_unit": cost_per_unit,
                "total_cost": total,
            })

        elif txn["transaction_type"] in ("sell", "advanced trade sell"):
            if asset not in buy_queues or not buy_queues[asset]:
                # Unknown cost basis
                tax_lots.append({
                    "asset": asset,
                    "quantity": str(quantity),
                    "date_acquired": None,
                    "date_disposed": txn["date"],
                    "cost_basis": "0",
                    "proceeds": str(total),
                    "gain_loss": str(total),
                    "holding_period": "unknown",
                    "cost_basis_known": False,
                })
                continue

            remaining = quantity
            while remaining > 0 and buy_queues.get(asset):
                lot = buy_queues[asset][0]
                used = min(remaining, lot["quantity"])

                cost_basis = used * lot["cost_per_unit"]
                proceeds = (used / quantity) * total if quantity > 0 else Decimal("0")
                gain_loss = proceeds - cost_basis

                # Determine holding period
                acquired = date_cls.fromisoformat(lot["date"])
                disposed = date_cls.fromisoformat(txn["date"])
                days_held = (disposed - acquired).days
                holding_period = "long_term" if days_held > 365 else "short_term"

                tax_lots.append({
                    "asset": asset,
                    "quantity": str(used),
                    "date_acquired": lot["date"],
                    "date_disposed": txn["date"],
                    "cost_basis": str(cost_basis),
                    "proceeds": str(proceeds),
                    "gain_loss": str(gain_loss),
                    "holding_period": holding_period,
                    "cost_basis_known": True,
                })

                lot["quantity"] -= used
                if lot["quantity"] <= 0:
                    buy_queues[asset].pop(0)
                remaining -= used

    return tax_lots
