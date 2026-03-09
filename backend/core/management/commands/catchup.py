"""Startup catch-up: detect stale data and run overdue tasks."""

import logging
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from core.task_utils import run_task

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Run catch-up tasks for stale data on startup"

    def handle(self, *args, **options):
        self.stdout.write("Running startup catch-up...")
        now = timezone.now()
        today = now.date()

        # ── Phase 1: Synchronous (fast, no external APIs) ──

        self._generate_alerts(today)
        self._detect_subscriptions()
        self._match_receipts()

        # ── Phase 2: Async via run_task (external APIs) ──

        self._sync_plaid(now)
        self._scan_email(now)
        self._categorize_transactions()
        self._update_prices(today)
        self._fetch_news()

        self.stdout.write(self.style.SUCCESS("Catch-up complete."))

    def _generate_alerts(self, today):
        from core.models import Alert

        if Alert.objects.filter(created_at__date=today).exists():
            self.stdout.write("  Alerts: already generated today, skipping")
            return
        from core.tasks import generate_daily_alerts

        self.stdout.write("  Alerts: generating...")
        generate_daily_alerts()

    def _detect_subscriptions(self):
        from transactions.models import Transaction

        if not Transaction.objects.exists():
            self.stdout.write("  Subscriptions: no transactions, skipping")
            return
        from transactions.tasks import detect_subscriptions

        self.stdout.write("  Subscriptions: detecting...")
        detect_subscriptions()

    def _match_receipts(self):
        from taxes.models import Receipt

        if not Receipt.objects.filter(transaction__isnull=True, status="completed").exists():
            self.stdout.write("  Receipts: no unmatched receipts, skipping")
            return
        from taxes.tasks import auto_match_receipts

        self.stdout.write("  Receipts: matching...")
        auto_match_receipts()

    def _sync_plaid(self, now):
        from integrations.models import PlaidItem

        stale_cutoff = now - timedelta(hours=4)
        stale_items = PlaidItem.objects.filter(status="active").filter(
            models_q_last_synced_stale(stale_cutoff)
        )
        if not stale_items.exists():
            self.stdout.write("  Plaid: all items fresh, skipping")
            return
        from integrations.tasks import sync_plaid_transactions

        for item in stale_items:
            self.stdout.write(f"  Plaid: syncing item {item.item_id}...")
            run_task(sync_plaid_transactions, item.id)

    def _scan_email(self, now):
        from email_sync.models import EmailAccount

        stale_cutoff = now - timedelta(hours=2)
        stale_accounts = EmailAccount.objects.filter(status="active").filter(
            models_q_last_synced_stale(stale_cutoff)
        )
        if not stale_accounts.exists():
            self.stdout.write("  Email: all accounts fresh, skipping")
            return
        from email_sync.tasks import scan_single_email_account

        for account in stale_accounts:
            self.stdout.write(f"  Email: scanning {account.email_address}...")
            run_task(scan_single_email_account, account.id)

    def _categorize_transactions(self):
        from transactions.models import Transaction

        if not Transaction.objects.filter(category__isnull=True).exists():
            self.stdout.write("  Categorize: all transactions categorized, skipping")
            return
        from transactions.tasks import auto_categorize_transactions

        self.stdout.write("  Categorize: running auto-categorization...")
        run_task(auto_categorize_transactions)

    def _update_prices(self, today):
        from portfolio.models import Holding, PriceHistory

        if not Holding.objects.exists():
            self.stdout.write("  Prices: no holdings, skipping")
            return
        if PriceHistory.objects.filter(date=today).exists():
            self.stdout.write("  Prices: already updated today, skipping")
            return
        from portfolio.tasks import update_security_prices

        self.stdout.write("  Prices: updating security prices...")
        run_task(update_security_prices)

    def _fetch_news(self):
        from news.models import NewsSource

        if not NewsSource.objects.filter(is_active=True).exists():
            self.stdout.write("  News: no active sources, skipping")
            return
        from news.tasks import fetch_news_articles

        self.stdout.write("  News: fetching articles...")
        run_task(fetch_news_articles)


def models_q_last_synced_stale(cutoff):
    """Return a Q filter for objects whose last_synced_at is null or older than cutoff."""
    from django.db.models import Q

    return Q(last_synced_at__isnull=True) | Q(last_synced_at__lt=cutoff)
