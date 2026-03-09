"""Celery tasks for smart financial alerts and weekly summaries."""

import json
import logging
from datetime import timedelta
from decimal import Decimal

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task
def generate_daily_alerts():
    """Generate smart financial alerts for all users.

    Runs daily via Celery beat. Checks for:
    - Unusual spending (amount significantly above category average)
    - Bill due reminders (from detected subscriptions)
    - Low balance warnings
    - Subscription price increases
    - Large transactions
    - New fee detection
    """
    from django.contrib.auth import get_user_model

    User = get_user_model()

    for user in User.objects.all():
        try:
            _check_unusual_spending(user)
            _check_upcoming_bills(user)
            _check_low_balances(user)
            _check_price_increases(user)
            _check_large_transactions(user)
            _check_new_fees(user)
        except Exception:
            logger.exception("Alert generation failed for user %s", user.username)

    return "Daily alerts generated"


def _create_alert(user, alert_type, severity, title, message, action_url="", metadata=None):
    """Create an alert, avoiding duplicates from the same day."""
    from core.models import Alert

    today = timezone.now().date()

    # Don't create duplicate alerts for the same type/title today
    existing = Alert.objects.filter(
        user=user,
        alert_type=alert_type,
        title=title,
        created_at__date=today,
    ).exists()

    if not existing:
        Alert.objects.create(
            user=user,
            alert_type=alert_type,
            severity=severity,
            title=title,
            message=message,
            action_url=action_url,
            metadata=metadata or {},
        )


def _check_unusual_spending(user):
    """Detect transactions significantly above category average."""
    from django.db.models import Avg

    from transactions.models import Transaction

    # Recent transactions (last 3 days)
    three_days_ago = timezone.now().date() - timedelta(days=3)
    ninety_days_ago = timezone.now().date() - timedelta(days=90)

    recent = Transaction.objects.filter(
        user=user,
        transaction_type="expense",
        date__gte=three_days_ago,
    ).select_related("category")

    # Pre-compute category averages in a single query
    category_avgs = dict(
        Transaction.objects.filter(
            user=user,
            transaction_type="expense",
            date__gte=ninety_days_ago,
            date__lt=three_days_ago,
            category__isnull=False,
        )
        .values_list("category_id")
        .annotate(avg=Avg("amount"))
        .values_list("category_id", "avg")
    )

    for txn in recent:
        if not txn.category:
            continue

        avg = category_avgs.get(txn.category_id)
        if not avg or avg == 0:
            continue

        # Alert if transaction is more than 3x the category average
        if txn.amount > avg * 3 and txn.amount > Decimal("50"):
            _create_alert(
                user,
                "unusual_spending",
                "warning",
                f"Unusual spending: {txn.description}",
                f"${txn.amount} at {txn.description} is {txn.amount / avg:.1f}x your "
                f"average {txn.category.name} spending of ${avg:.2f}.",
                metadata={"transaction_id": txn.id, "amount": str(txn.amount)},
            )


def _check_upcoming_bills(user):
    """Remind about subscriptions due in the next 3 days."""
    from transactions.models import Subscription

    today = timezone.now().date()
    three_days_out = today + timedelta(days=3)

    upcoming = Subscription.objects.filter(
        user=user,
        status="active",
        next_expected__gte=today,
        next_expected__lte=three_days_out,
    )

    for sub in upcoming:
        days_until = (sub.next_expected - today).days
        _create_alert(
            user,
            "bill_due",
            "info",
            f"{sub.merchant} payment due",
            f"${sub.amount} {sub.frequency} charge expected "
            f"{'tomorrow' if days_until == 1 else f'in {days_until} days'}.",
            metadata={"subscription_id": sub.id},
        )


def _check_low_balances(user):
    """Warn about accounts with low balances."""
    from accounts.models import Account

    low_threshold = Decimal("100")

    accounts = Account.objects.filter(
        user=user,
        is_active=True,
        account_type__in=["checking", "savings"],
        balance__lt=low_threshold,
        balance__gte=0,
    )

    for account in accounts:
        _create_alert(
            user,
            "low_balance",
            "warning",
            f"Low balance: {account.name}",
            f"Your {account.name} balance is ${account.balance}.",
            metadata={"account_id": account.id},
        )


def _check_price_increases(user):
    """Detect subscription price increases by comparing recent charges."""
    from transactions.models import Subscription, Transaction

    active_subs = Subscription.objects.filter(user=user, status="active")
    ninety_days_ago = timezone.now().date() - timedelta(days=90)

    for sub in active_subs:
        # Get the last few charges for this merchant
        charges = list(
            Transaction.objects.filter(
                user=user,
                transaction_type="expense",
                description__icontains=sub.merchant,
                date__gte=ninety_days_ago,
            )
            .order_by("-date")
            .values_list("amount", flat=True)[:5]
        )

        if len(charges) < 2:
            continue

        newest = charges[0]
        older = charges[-1]
        if newest > older and (newest - older) / older > Decimal("0.05"):
            _create_alert(
                user,
                "price_increase",
                "warning",
                f"{sub.merchant} price increased",
                f"{sub.merchant} went from ${older} to ${newest} per charge.",
                metadata={"subscription_id": sub.id, "old_amount": str(older), "new_amount": str(newest)},
            )


def _check_large_transactions(user):
    """Alert on unusually large transactions."""
    from transactions.models import Transaction

    yesterday = timezone.now().date() - timedelta(days=1)
    large_threshold = Decimal("500")

    large_txns = Transaction.objects.filter(
        user=user,
        date__gte=yesterday,
        amount__gte=large_threshold,
    )

    for txn in large_txns:
        _create_alert(
            user,
            "large_transaction",
            "info",
            f"Large {txn.transaction_type}: ${txn.amount}",
            f"${txn.amount} {txn.transaction_type} — {txn.description}",
            metadata={"transaction_id": txn.id},
        )


def _check_new_fees(user):
    """Detect bank fees and service charges."""
    from transactions.models import Transaction

    yesterday = timezone.now().date() - timedelta(days=1)
    fee_keywords = ["fee", "service charge", "overdraft", "maintenance", "atm fee"]

    recent = Transaction.objects.filter(
        user=user,
        transaction_type="expense",
        date__gte=yesterday,
    )

    for txn in recent:
        desc_lower = txn.description.lower()
        if any(kw in desc_lower for kw in fee_keywords):
            _create_alert(
                user,
                "new_fee",
                "warning",
                f"Fee detected: {txn.description}",
                f"${txn.amount} fee charged — {txn.description}",
                metadata={"transaction_id": txn.id},
            )


@shared_task
def generate_weekly_summary():
    """Generate a weekly financial summary for all users.

    Runs Sunday evening via Celery beat. Creates a summary
    that the agent can surface on Monday morning.
    """
    from django.contrib.auth import get_user_model
    from django.db.models import Sum

    from accounts.models import Account
    from transactions.models import Subscription, Transaction

    User = get_user_model()

    for user in User.objects.all():
        try:
            now = timezone.now()
            week_start = (now - timedelta(days=7)).date()
            prev_week_start = (now - timedelta(days=14)).date()

            # Spending this week vs last week
            this_week = Transaction.objects.filter(
                user=user, transaction_type="expense", date__gte=week_start,
            ).aggregate(total=Sum("amount"))["total"] or Decimal("0")

            last_week = Transaction.objects.filter(
                user=user, transaction_type="expense",
                date__gte=prev_week_start, date__lt=week_start,
            ).aggregate(total=Sum("amount"))["total"] or Decimal("0")

            # Top spending categories this week
            top_categories = list(
                Transaction.objects.filter(
                    user=user, transaction_type="expense", date__gte=week_start,
                )
                .values("category__name")
                .annotate(total=Sum("amount"))
                .order_by("-total")[:5]
            )

            # Notable transactions (> $100)
            notable = list(
                Transaction.objects.filter(
                    user=user, date__gte=week_start, amount__gte=100,
                ).order_by("-amount")[:5]
            )

            # Net worth
            net_worth = Account.objects.filter(user=user).aggregate(
                total=Sum("balance")
            )["total"] or Decimal("0")

            # Active subscriptions total
            sub_monthly = Decimal("0")
            for s in Subscription.objects.filter(user=user, status="active"):
                sub_monthly += s.annual_cost / 12

            summary = {
                "week_ending": now.date().isoformat(),
                "spending": {
                    "this_week": str(this_week),
                    "last_week": str(last_week),
                    "change_pct": str(
                        round(((this_week - last_week) / last_week * 100), 1)
                        if last_week > 0
                        else 0
                    ),
                },
                "top_categories": [
                    {"name": c["category__name"] or "Uncategorized", "amount": str(c["total"])}
                    for c in top_categories
                ],
                "notable_transactions": [
                    {"description": t.description, "amount": str(t.amount), "date": t.date.isoformat()}
                    for t in notable
                ],
                "net_worth": str(net_worth),
                "subscription_monthly": str(sub_monthly.quantize(Decimal("0.01"))),
            }

            # Store as a general alert so it's retrievable
            _create_alert(
                user,
                "general",
                "info",
                f"Weekly Summary — {now.date().isoformat()}",
                json.dumps(summary),
                metadata=summary,
            )

        except Exception:
            logger.exception("Weekly summary failed for user %s", user.username)
