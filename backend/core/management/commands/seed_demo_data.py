"""Seed realistic demo data for screenshots and development."""

import random
from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from accounts.models import Account, BalanceHistory, Institution
from core.models import UserSettings
from chat.models import Conversation
from news.models import NewsArticle, NewsSource
from portfolio.models import Holding, PriceHistory, Security
from taxes.models import DeductibleExpense, TaxDocument, TaxYear
from transactions.models import Budget, Category, Goal, Subscription, Transaction

User = get_user_model()

TODAY = date.today()


class Command(BaseCommand):
    help = "Seed realistic demo data for screenshots and development"

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true", help="Clear existing demo data before seeding")

    def handle(self, *args, **options):
        # Always seed into a dedicated demo account
        demo_username = "jesse"
        demo_password = "demo"
        user, created = User.objects.get_or_create(
            username=demo_username,
            defaults={
                "email": "jesse@example.com",
                "first_name": "Jesse",
                "is_staff": True,
                "is_superuser": True,
            },
        )
        if created:
            user.set_password(demo_password)
            user.save()
            UserSettings.objects.get_or_create(user=user)
            self.stdout.write(self.style.SUCCESS(f"Created demo user: {demo_username} / {demo_password}"))
        else:
            UserSettings.objects.get_or_create(user=user)
            self.stdout.write(f"Using existing demo user: {demo_username}")
        self.stdout.write(f"Seeding data for user: {user.username}")

        if options["reset"]:
            self._clear_data(user)

        self._create_accounts(user)
        self._create_transactions(user)
        self._create_portfolio(user)
        self._create_subscriptions(user)
        self._create_budgets(user)
        self._create_goals(user)
        self._create_tax_data(user)
        self._create_news()
        self._create_conversations(user)

        self.stdout.write(self.style.SUCCESS("Demo data seeded."))

    def _clear_data(self, user):
        """Remove all demo-seeded data for a clean re-seed."""
        Transaction.objects.filter(user=user).delete()
        Subscription.objects.filter(user=user).delete()
        Budget.objects.filter(user=user).delete()
        Goal.objects.filter(user=user).delete()
        Holding.objects.filter(user=user).delete()
        PriceHistory.objects.all().delete()
        Security.objects.all().delete()
        TaxYear.objects.filter(user=user).delete()
        BalanceHistory.objects.filter(account__user=user).delete()
        Account.objects.filter(user=user).delete()
        Conversation.objects.filter(user=user).delete()
        NewsArticle.objects.all().delete()
        NewsSource.objects.all().delete()
        self.stdout.write("Cleared existing data.")

    def _create_accounts(self, user):
        if Account.objects.filter(user=user).count() >= 5:
            return

        # Clear any partial state
        Account.objects.filter(user=user).delete()

        chase = Institution.objects.filter(name__icontains="chase").first()
        schwab = Institution.objects.filter(name__icontains="schwab").first()
        amex = Institution.objects.filter(name__icontains="american express").first()
        bofa = Institution.objects.filter(name__icontains="bank of america").first()

        accounts = Account.objects.bulk_create([
            Account(user=user, institution=chase, name="Chase Checking", account_type="checking", balance=Decimal("42817.50")),
            Account(user=user, institution=chase, name="Chase Savings", account_type="savings", balance=Decimal("185000.00")),
            Account(user=user, institution=amex, name="Amex Platinum", account_type="credit_card", balance=Decimal("-4215.89")),
            Account(user=user, institution=schwab, name="Schwab Brokerage", account_type="investment", balance=Decimal("1287500.00")),
            Account(user=user, institution=schwab, name="Schwab 401k", account_type="investment", balance=Decimal("342000.00")),
            Account(user=user, institution=bofa, name="BofA Auto Loan", account_type="loan", balance=Decimal("-28750.00")),
        ])

        # Balance history for checking and savings
        for acct in accounts[:2]:
            base = Decimal("38000") if acct.account_type == "checking" else Decimal("170000")
            history = []
            bal = base
            for i in range(90, 0, -1):
                d = TODAY - timedelta(days=i)
                bal += Decimal(random.randint(-150, 250)) / Decimal("100")
                bal = max(bal, base * Decimal("0.6"))
                history.append(BalanceHistory(account=acct, date=d, balance=bal))
            BalanceHistory.objects.bulk_create(history, ignore_conflicts=True)

    def _create_transactions(self, user):
        if Transaction.objects.filter(user=user).count() >= 50:
            return

        checking = Account.objects.filter(user=user, account_type="checking").first()
        credit = Account.objects.filter(user=user, account_type="credit_card").first()
        if not checking:
            return

        def cat(name):
            return Category.objects.filter(name=name).first()

        txns = []

        # Salary deposits (biweekly)
        for m in range(3):
            for day in [1, 15]:
                try:
                    d = TODAY.replace(day=day) - timedelta(days=30 * m)
                except ValueError:
                    continue
                if d <= TODAY:
                    txns.append(Transaction(
                        user=user, account=checking, category=cat("Salary"),
                        date=d, amount=Decimal("14583.33"), transaction_type="income",
                        description="TYRELL CORP DIRECT DEPOSIT", is_recurring=True,
                    ))

        # Recurring monthly expenses
        recurring = [
            ("Rent/Mortgage", "AVALON COMMUNITIES RENT", "5200.00", checking),
            ("Utilities", "PG&E ELECTRIC", "142.87", checking),
            ("Utilities", "COMCAST INTERNET", "89.99", checking),
            ("Car Insurance", "GEICO AUTO INSURANCE", "156.00", checking),
            ("Health Insurance", "ANTHEM BLUE CROSS", "485.00", checking),
        ]
        for cat_name, desc, amt, acct in recurring:
            for m in range(3):
                try:
                    d = TODAY.replace(day=3) - timedelta(days=30 * m)
                except ValueError:
                    continue
                if d <= TODAY:
                    txns.append(Transaction(
                        user=user, account=acct, category=cat(cat_name),
                        date=d, amount=Decimal(amt), transaction_type="expense",
                        description=desc, is_recurring=True,
                    ))

        # Variable expenses with realistic amounts
        variable = [
            ("Groceries", [
                ("WHOLE FOODS MARKET", 45, 120), ("TRADER JOES", 30, 85),
                ("SAFEWAY", 25, 95), ("COSTCO", 80, 250),
            ]),
            ("Restaurants", [
                ("DOORDASH*SWEETGREEN", 12, 28), ("UBER EATS", 15, 45),
                ("CHIPOTLE ONLINE", 10, 18), ("STARBUCKS", 5, 9),
                ("THAI BASIL RESTAURANT", 35, 65),
            ]),
            ("Shopping", [
                ("AMAZON.COM*", 15, 200), ("TARGET", 20, 80),
                ("APPLE.COM/BILL", 0.99, 15), ("IKEA", 40, 300),
            ]),
            ("Gas", [
                ("SHELL OIL", 40, 70), ("CHEVRON", 45, 75),
            ]),
            ("Entertainment", [
                ("AMC THEATERS", 15, 30), ("STEAM GAMES", 10, 60),
                ("TICKETMASTER", 50, 150),
            ]),
            ("Rideshare", [
                ("UBER *TRIP", 12, 35), ("LYFT *RIDE", 10, 30),
            ]),
            ("Travel", [
                ("UNITED AIRLINES", 250, 600), ("MARRIOTT HOTELS", 150, 350),
                ("AIRBNB", 120, 280),
            ]),
            ("Healthcare", [
                ("EQUINOX MEMBERSHIP", 185, 185), ("CVS PHARMACY", 8, 45),
            ]),
        ]

        for cat_name, merchants in variable:
            count = random.randint(6, 18) if cat_name != "Travel" else random.randint(1, 3)
            for _ in range(count):
                merchant_name, low, high = random.choice(merchants)
                d = TODAY - timedelta(days=random.randint(0, 89))
                acct = random.choice([checking, credit]) if credit else checking
                txns.append(Transaction(
                    user=user, account=acct, category=cat(cat_name),
                    date=d, amount=Decimal(str(round(random.uniform(low, high), 2))),
                    transaction_type="expense", description=merchant_name,
                ))

        # Transfers
        for m in range(3):
            d = TODAY.replace(day=5) - timedelta(days=30 * m)
            if d <= TODAY:
                txns.append(Transaction(
                    user=user, account=checking, category=cat("Financial"),
                    date=d, amount=Decimal("500.00"), transaction_type="expense",
                    description="TRANSFER TO SAVINGS",
                ))

        Transaction.objects.bulk_create(txns)

    def _create_portfolio(self, user):
        if Security.objects.count() >= 7:
            return

        stocks = [
            ("GME", "GameStop Corp.", "stock", "28.50", 8000),
            ("AAPL", "Apple Inc.", "stock", "175.50", 150),
            ("NVDA", "NVIDIA Corporation", "stock", "875.30", 40),
            ("MSFT", "Microsoft Corporation", "stock", "420.80", 60),
            ("VOO", "Vanguard S&P 500 ETF", "etf", "518.40", 100),
            ("VTI", "Vanguard Total Stock Market ETF", "etf", "268.90", 120),
            ("BND", "Vanguard Total Bond Market ETF", "etf", "72.15", 200),
            ("TSLA", "Tesla Inc.", "stock", "248.50", 50),
        ]

        brokerage = Account.objects.filter(user=user, account_type="investment", name__icontains="brokerage").first()

        for symbol, name, sec_type, price, shares in stocks:
            sec, _ = Security.objects.get_or_create(symbol=symbol, defaults={"name": name, "security_type": sec_type})
            if not Holding.objects.filter(user=user, security=sec).exists():
                cost = Decimal(price) * Decimal("0.85")
                Holding.objects.create(
                    user=user, account=brokerage, security=sec,
                    shares=Decimal(str(shares)), cost_basis=cost * Decimal(str(shares)),
                )

            # Price history (30 days) with trending movement
            if not PriceHistory.objects.filter(security=sec).exists():
                base = Decimal(price)
                trend = Decimal(str(round(random.uniform(-0.005, 0.008), 5)))
                history = []
                for i in range(30, 0, -1):
                    d = TODAY - timedelta(days=i)
                    daily = Decimal(str(round(random.uniform(-0.02, 0.02), 4)))
                    change = trend + daily
                    close = base * (1 + change)
                    history.append(PriceHistory(
                        security=sec, date=d, close_price=close,
                        open_price=close * Decimal("0.998"),
                        high_price=close * Decimal("1.008"),
                        low_price=close * Decimal("0.992"),
                    ))
                    base = close
                PriceHistory.objects.bulk_create(history, ignore_conflicts=True)

    def _create_subscriptions(self, user):
        if Subscription.objects.filter(user=user).count() >= 8:
            return

        subs = [
            ("Netflix", "15.49", "monthly", "active"),
            ("Spotify Premium", "10.99", "monthly", "active"),
            ("ChatGPT Plus", "20.00", "monthly", "active"),
            ("iCloud+ 200GB", "2.99", "monthly", "active"),
            ("GitHub Pro", "4.00", "monthly", "active"),
            ("Figma", "15.00", "monthly", "active"),
            ("New York Times", "17.00", "monthly", "active"),
            ("Costco Membership", "65.00", "annual", "active"),
            ("Adobe Creative Cloud", "54.99", "monthly", "active"),
            ("Notion Plus", "10.00", "monthly", "active"),
            ("YouTube Premium", "13.99", "monthly", "active"),
            ("Hulu", "17.99", "monthly", "cancelled"),
            ("Audible", "14.95", "monthly", "cancelled"),
        ]

        cat_software = Category.objects.filter(name="Software").first()
        cat_entertainment = Category.objects.filter(name="Entertainment").first()

        for merchant, amount, freq, status in subs:
            if not Subscription.objects.filter(user=user, merchant=merchant).exists():
                is_software = any(s in merchant for s in ["Git", "Figma", "Adobe", "Notion", "iCloud"])
                Subscription.objects.create(
                    user=user, merchant=merchant, amount=Decimal(amount),
                    frequency=freq, status=status, confidence=random.uniform(0.88, 0.99),
                    category=cat_software if is_software else cat_entertainment,
                    last_charged=TODAY - timedelta(days=random.randint(1, 28)),
                    next_expected=TODAY + timedelta(days=random.randint(1, 28)) if status == "active" else None,
                )

    def _create_budgets(self, user):
        if Budget.objects.filter(user=user).count() >= 4:
            return

        budgets = [
            ("Food", "1000.00"),
            ("Shopping", "300.00"),
            ("Entertainment", "200.00"),
            ("Transportation", "250.00"),
            ("Travel", "500.00"),
            ("Housing", "4000.00"),
        ]

        for cat_name, amount in budgets:
            c = Category.objects.filter(name=cat_name, parent__isnull=True).first()
            if c and not Budget.objects.filter(user=user, category=c).exists():
                Budget.objects.create(user=user, category=c, amount=Decimal(amount), period="monthly")

    def _create_goals(self, user):
        if Goal.objects.filter(user=user).count() >= 3:
            return

        savings = Account.objects.filter(user=user, account_type="savings").first()
        goals = [
            ("Emergency Fund", "100000", "85000", 120, savings),
            ("Japan Trip", "15000", "9200", 200, None),
            ("Porsche Fund", "120000", "42000", 365, None),
            ("Home Down Payment", "400000", "185000", 730, savings),
        ]

        for name, target, current, days, acct in goals:
            if not Goal.objects.filter(user=user, name=name).exists():
                Goal.objects.create(
                    user=user, name=name,
                    target_amount=Decimal(target), current_amount=Decimal(current),
                    target_date=TODAY + timedelta(days=days), linked_account=acct,
                )

    def _create_tax_data(self, user):
        year = TODAY.year - 1
        if TaxYear.objects.filter(user=user, year=year).exists():
            return

        ty = TaxYear.objects.create(
            user=user, year=year, filing_status="single",
            federal_tax_paid=Decimal("98750.00"), state_tax_paid=Decimal("32400.00"),
        )

        TaxDocument.objects.bulk_create([
            TaxDocument(tax_year=ty, document_type="w2", issuer="Tyrell Corp", amount=Decimal("350000.00"),
                        details={"federal_withheld": "98750.00", "state_withheld": "32400.00", "ss_withheld": "10453.20", "medicare_withheld": "5075.00"}),
            TaxDocument(tax_year=ty, document_type="1099_div", issuer="Charles Schwab", amount=Decimal("18500.00"),
                        details={"qualified_dividends": "14200.00", "ordinary_dividends": "18500.00"}),
            TaxDocument(tax_year=ty, document_type="1099_int", issuer="Chase Bank", amount=Decimal("2840.00")),
            TaxDocument(tax_year=ty, document_type="1099_b", issuer="Charles Schwab", amount=Decimal("45000.00"),
                        details={"short_term_gains": "12000.00", "long_term_gains": "33000.00"}),
        ])

        DeductibleExpense.objects.bulk_create([
            DeductibleExpense(tax_year=ty, deduction_type="retirement", description="401k contributions", amount=Decimal("23500.00"), is_verified=True),
            DeductibleExpense(tax_year=ty, deduction_type="state_local_tax", description="State income tax paid", amount=Decimal("10000.00"), is_verified=True),
            DeductibleExpense(tax_year=ty, deduction_type="charitable", description="Charitable donations — various", amount=Decimal("12500.00"), is_verified=True),
            DeductibleExpense(tax_year=ty, deduction_type="home_office", description="Home office deduction", amount=Decimal("1500.00"), is_verified=False),
            DeductibleExpense(tax_year=ty, deduction_type="education", description="Professional development courses", amount=Decimal("4800.00"), is_verified=False),
        ])

    def _create_news(self):
        if NewsArticle.objects.count() >= 10:
            return

        mw, _ = NewsSource.objects.get_or_create(name="MarketWatch", defaults={"url": "https://www.marketwatch.com", "feed_url": ""})
        wsj, _ = NewsSource.objects.get_or_create(name="The Wall Street Journal", defaults={"url": "https://www.wsj.com", "feed_url": ""})
        reuters, _ = NewsSource.objects.get_or_create(name="Reuters", defaults={"url": "https://www.reuters.com", "feed_url": ""})

        articles = [
            (mw, "GameStop shares surge 15% as meme-stock rally reignites", 1),
            (wsj, "Fed signals rate cuts likely later this year amid cooling inflation", 2),
            (reuters, "NVIDIA overtakes Apple as world's most valuable company", 3),
            (mw, "S&P 500 hits record high as tech earnings beat expectations", 4),
            (wsj, "Tesla deliveries top estimates, stock jumps 8% in premarket", 5),
            (reuters, "Warren Buffett's Berkshire Hathaway trims Apple stake by 25%", 6),
            (mw, "Why the 60/40 portfolio is making a comeback in 2026", 7),
            (wsj, "Retail investors pour record $4.2B into ETFs in a single week", 8),
            (reuters, "GameStop announces first profitable quarter since 2021", 9),
            (mw, "The housing market is finally thawing — here's what buyers need to know", 10),
            (wsj, "Bond yields fall as markets price in summer rate cuts", 11),
            (reuters, "Oil prices drop below $70 as OPEC+ signals production increase", 12),
        ]

        from django.utils import timezone
        NewsArticle.objects.bulk_create([
            NewsArticle(
                source=source, title=title,
                url=f"https://example.com/article/{i}",
                summary="",
                published_at=timezone.now() - timedelta(hours=i * 4),
            )
            for source, title, i in articles
        ])

    def _create_conversations(self, user):
        if Conversation.objects.filter(user=user).count() >= 5:
            return

        convos = [
            "What's my net worth?",
            "Show my portfolio performance",
            "Estimate my taxes for 2025",
            "Which subscriptions should I cancel?",
            "How much did I spend on food this month?",
            "Analyze my spending trends",
            "Compare my budget vs actual",
        ]

        for i, title in enumerate(convos):
            if not Conversation.objects.filter(user=user, title=title).exists():
                Conversation.objects.create(
                    user=user, title=title,
                )
