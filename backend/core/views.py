import json
from datetime import timedelta

from django.contrib.auth import authenticate, login, logout
from django.db import models
from django.middleware.csrf import get_token
from django.utils import timezone
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import Account
from portfolio.models import Holding, PriceHistory
from transactions.models import Transaction

from .models import Alert, UserSettings
from .serializers import AlertSerializer, UserSettingsSerializer


@api_view(["GET"])
@permission_classes([AllowAny])
def health_check(request):
    from django.db import connection

    result = {"status": "ok", "version": "1.0.0"}

    # Database
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        result["database"] = "ok"
    except Exception:
        result["database"] = "error"
        result["status"] = "degraded"

    # Redis / Celery broker
    try:
        from nullbook.celery_app import app as celery_app
        conn = celery_app.connection()
        conn.ensure_connection(max_retries=1, timeout=2)
        conn.close()
        result["redis"] = "ok"
        result["celery_broker"] = "ok"
    except Exception:
        result["redis"] = "error"
        result["celery_broker"] = "error"

    http_status = status.HTTP_200_OK if result["status"] == "ok" else status.HTTP_503_SERVICE_UNAVAILABLE
    return Response(result, status=http_status)


@api_view(["GET"])
@permission_classes([AllowAny])
@ensure_csrf_cookie
def csrf_view(request):
    return Response({"csrfToken": get_token(request)})


@api_view(["POST"])
@permission_classes([AllowAny])
def login_view(request):
    username = request.data.get("username")
    password = request.data.get("password")
    if not username or not password:
        return Response(
            {"detail": "Username and password are required."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    user = authenticate(request, username=username, password=password)
    if user is None:
        return Response(
            {"detail": "Invalid credentials."},
            status=status.HTTP_401_UNAUTHORIZED,
        )
    login(request, user)
    return Response({
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "csrfToken": get_token(request),
    })


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout_view(request):
    logout(request)
    return Response({"detail": "Logged out."})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def change_password_view(request):
    current_password = request.data.get("current_password", "")
    new_password = request.data.get("new_password", "")
    if not current_password or not new_password:
        return Response(
            {"detail": "Both current_password and new_password are required."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if not request.user.check_password(current_password):
        return Response(
            {"detail": "Current password is incorrect."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if len(new_password) < 8:
        return Response(
            {"detail": "New password must be at least 8 characters."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    from django.contrib.auth.password_validation import validate_password
    from django.core.exceptions import ValidationError as DjangoValidationError
    try:
        validate_password(new_password, user=request.user)
    except DjangoValidationError as e:
        return Response(
            {"detail": e.messages},
            status=status.HTTP_400_BAD_REQUEST,
        )
    request.user.set_password(new_password)
    request.user.save()
    # Re-authenticate to keep the session active
    login(request, request.user)
    return Response({"detail": "Password changed successfully."})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def session_view(request):
    user = request.user
    return Response({"id": user.id, "username": user.username, "email": user.email})


class DashboardSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        # Accounts aggregate (single query instead of two)
        accounts_agg = Account.objects.filter(user=user).aggregate(
            total=models.Count("id"),
            net_worth=models.Sum("balance"),
        )
        total_accounts = accounts_agg["total"]
        net_worth = accounts_agg["net_worth"] or 0

        # Recent transactions in the last 30 days
        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent_transactions = Transaction.objects.filter(
            user=user,
            date__gte=thirty_days_ago,
        ).count()

        # Portfolio value from holdings × latest prices (database aggregation)
        latest_price_sq = models.Subquery(
            PriceHistory.objects.filter(
                security=models.OuterRef("security")
            ).order_by("-date").values("close_price")[:1]
        )
        portfolio_value = (
            Holding.objects.filter(user=user)
            .annotate(latest_price=latest_price_sq)
            .annotate(
                market_value=models.Case(
                    models.When(
                        latest_price__isnull=False,
                        then=models.F("shares") * models.F("latest_price"),
                    ),
                    default=models.F("cost_basis"),
                    output_field=models.DecimalField(),
                )
            )
            .aggregate(total=models.Sum("market_value"))["total"]
            or 0
        )

        return Response(
            {
                "total_accounts": total_accounts,
                "net_worth": str(net_worth),
                "recent_transactions": recent_transactions,
                "portfolio_value": str(portfolio_value),
            }
        )


class IntegrationStatusView(APIView):
    """Report the status of all integrations for Settings panel."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from django.conf import settings as django_settings
        from email_sync.models import EmailAccount
        from integrations.models import PlaidItem
        from news.models import NewsSource
        from portfolio.models import Holding
        from taxes.models import TaxYear

        user = request.user

        # Plaid
        plaid_items = PlaidItem.objects.filter(user=user)
        plaid_connected = [
            {
                "id": item.id,
                "institution_name": item.institution_name,
                "status": item.status,
                "last_synced_at": item.last_synced_at.isoformat() if item.last_synced_at else None,
            }
            for item in plaid_items
        ]

        # Email
        email_accounts = EmailAccount.objects.filter(user=user)
        email_connected = [
            {
                "id": acct.id,
                "email_address": acct.email_address,
                "provider": acct.provider,
                "status": acct.status,
                "last_synced_at": acct.last_synced_at.isoformat() if acct.last_synced_at else None,
            }
            for acct in email_accounts
        ]

        # News sources
        news_count = NewsSource.objects.filter(is_active=True).count()

        # API keys / services configured
        has_plaid = bool(django_settings.PLAID_CLIENT_ID)
        has_email_accounts = len(email_connected) > 0
        has_smtp = bool(django_settings.SMTP_HOST)

        # LLM provider check
        llm_provider = getattr(django_settings, "LLM_PROVIDER", "anthropic")
        llm_model = getattr(django_settings, "CHAT_MODEL", "")
        if llm_provider == "ollama":
            # Check Ollama connectivity
            has_llm = False
            try:
                import urllib.request
                ollama_base = getattr(django_settings, "OLLAMA_BASE_URL", "http://localhost:11434/v1")
                # Strip /v1 to hit the native tags endpoint
                ollama_host = ollama_base.replace("/v1", "")
                req = urllib.request.Request(f"{ollama_host}/api/tags", method="GET")
                with urllib.request.urlopen(req, timeout=3) as resp:
                    if resp.status == 200:
                        data = json.loads(resp.read())
                        pulled_models = [m.get("name", "") for m in data.get("models", [])]
                        # Check if the configured model (or its base name) is pulled
                        has_llm = any(
                            llm_model == m or llm_model.split(":")[0] in m
                            for m in pulled_models
                        )
            except Exception:
                pass
        elif llm_provider == "openai":
            has_llm = bool(getattr(django_settings, "OPENAI_API_KEY", ""))
        else:
            has_llm = bool(getattr(django_settings, "ANTHROPIC_API_KEY", ""))

        # Data counts
        total_accounts = Account.objects.filter(user=user).count()
        total_transactions = Transaction.objects.filter(user=user).count()
        total_holdings = Holding.objects.filter(user=user).count()
        has_tax_year = TaxYear.objects.filter(user=user).exists()

        # Redis / Celery connectivity
        redis_ok = False
        try:
            from nullbook.celery_app import app as celery_app
            conn = celery_app.connection()
            conn.ensure_connection(max_retries=1, timeout=2)
            conn.close()
            redis_ok = True
        except Exception:
            pass

        # Build setup checklist
        setup_checklist = [
            {
                "id": "llm",
                "label": (
                    "Set up AI model" if llm_provider == "ollama"
                    else f"Configure {'OpenAI' if llm_provider == 'openai' else 'Anthropic'} API key"
                ),
                "description": (
                    f"Install Ollama and run: ollama pull {llm_model}"
                    if llm_provider == "ollama"
                    else (
                        "Add OPENAI_API_KEY to your .env file. Required for the AI chat agent."
                        if llm_provider == "openai"
                        else "Add ANTHROPIC_API_KEY to your .env file. Required for the AI chat agent."
                    )
                ),
                "completed": has_llm,
                "required": True,
                "category": "required",
            },
            {
                "id": "redis",
                "label": "Start Redis",
                "description": "Run `docker run -d -p 6379:6379 redis` or `make dev` to start Redis. Required for background tasks.",
                "completed": redis_ok,
                "required": True,
                "category": "required",
            },
            {
                "id": "financial_data",
                "label": "Add financial data",
                "description": "Import transactions from CSV/OFX/QIF, or connect a bank account via Plaid.",
                "completed": total_transactions > 0,
                "required": True,
                "category": "data",
                "action": "import",
            },
            {
                "id": "accounts",
                "label": "Set up accounts",
                "description": "Create accounts to organize your finances (checking, savings, credit cards).",
                "completed": total_accounts > 0,
                "required": True,
                "category": "data",
                "action": "accounts",
            },
            {
                "id": "plaid",
                "label": "Connect bank via Plaid",
                "description": "Add PLAID_CLIENT_ID and PLAID_SECRET to .env, then link your bank for automatic syncing.",
                "completed": len(plaid_connected) > 0,
                "required": False,
                "category": "integrations",
                "action": "accounts",
            },
            {
                "id": "email",
                "label": "Connect email for receipts",
                "description": "Connect your email via IMAP to automatically scan for receipts. For Gmail, use an App Password.",
                "completed": len(email_connected) > 0,
                "required": False,
                "category": "integrations",
                "action": "email",
            },
            {
                "id": "tax_year",
                "label": "Create a tax year",
                "description": "Set up a tax year to track deductions, estimate taxes, and prepare filings.",
                "completed": has_tax_year,
                "required": False,
                "category": "features",
                "action": "chat:Help me set up a tax year",
            },
            {
                "id": "portfolio",
                "label": "Add portfolio holdings",
                "description": "Add stocks, ETFs, or other securities to track your investment portfolio.",
                "completed": total_holdings > 0,
                "required": False,
                "category": "features",
                "action": "chat:Help me add portfolio holdings",
            },
            {
                "id": "smtp",
                "label": "Configure email sending (SMTP)",
                "description": "Add SMTP_HOST, SMTP_USER, and SMTP_PASSWORD to .env for subscription cancellation emails.",
                "completed": has_smtp,
                "required": False,
                "category": "integrations",
            },
        ]

        return Response({
            "plaid": {
                "configured": has_plaid,
                "items": plaid_connected,
            },
            "email": {
                "configured": has_email_accounts,
                "accounts": email_connected,
            },
            "smtp": {
                "configured": has_smtp,
            },
            "llm": {
                "configured": has_llm,
                "provider": llm_provider,
                "model": llm_model,
            },
            "news": {
                "source_count": news_count,
            },
            "onboarding": {
                "has_accounts": total_accounts > 0,
                "has_transactions": total_transactions > 0,
                "has_api_key": has_llm,
            },
            "setup_checklist": setup_checklist,
        })


class InsightsView(APIView):
    """Generate proactive financial insights for the home view."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from decimal import Decimal

        from transactions.models import Subscription, Transaction

        user = request.user
        insights = []

        # 1. Spending comparison vs last month
        now = timezone.now()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        prev_month_end = month_start - timedelta(days=1)
        prev_month_start = prev_month_end.replace(day=1)

        this_month_spending = (
            Transaction.objects.filter(
                user=user,
                transaction_type="expense",
                date__gte=month_start,
            ).aggregate(total=models.Sum("amount"))["total"]
            or Decimal("0")
        )
        last_month_spending = (
            Transaction.objects.filter(
                user=user,
                transaction_type="expense",
                date__gte=prev_month_start,
                date__lte=prev_month_end,
            ).aggregate(total=models.Sum("amount"))["total"]
            or Decimal("0")
        )

        if last_month_spending > 0 and this_month_spending > 0:
            diff = this_month_spending - last_month_spending
            if abs(diff) > Decimal("20"):
                direction = "more" if diff > 0 else "less"
                insights.append({
                    "type": "spending_comparison",
                    "title": f"You've spent ${abs(diff):.0f} {direction} this month",
                    "description": f"${this_month_spending:.0f} this month vs ${last_month_spending:.0f} last month",
                    "chat_prompt": "Analyze my spending this month compared to last month",
                })

        # 2. Unread alerts
        from core.models import Alert

        unread_count = Alert.objects.filter(user=user, is_read=False).count()
        if unread_count > 0:
            insights.append({
                "type": "unread_alerts",
                "title": f"{unread_count} unread alert{'s' if unread_count != 1 else ''}",
                "description": "Financial alerts need your attention",
                "chat_prompt": "Show my alerts",
            })

        # 3. Subscription price changes
        subs_with_changes = Subscription.objects.filter(
            user=user,
            status="active",
            updated_at__gte=now - timedelta(days=7),
        )
        for sub in subs_with_changes[:2]:
            insights.append({
                "type": "subscription_update",
                "title": f"{sub.merchant} — ${sub.amount}/{sub.frequency}",
                "description": f"Next charge expected {sub.next_expected}",
                "chat_prompt": f"Tell me about my {sub.merchant} subscription",
            })

        # 4. Recent large transactions
        three_days_ago = now - timedelta(days=3)
        large_txns = Transaction.objects.filter(
            user=user,
            amount__gte=Decimal("200"),
            date__gte=three_days_ago,
        ).order_by("-amount")[:2]

        for txn in large_txns:
            insights.append({
                "type": "large_transaction",
                "title": f"${txn.amount} — {txn.description}",
                "description": f"{txn.transaction_type.title()} on {txn.date}",
                "chat_prompt": f"Tell me about my recent transaction at {txn.description}",
            })

        # Return top 3 insights
        return Response(insights[:3])


class NetWorthHistoryView(APIView):
    """Return net worth over time by aggregating BalanceHistory."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from accounts.models import BalanceHistory

        period = request.query_params.get("period", "90d")
        period_days = {"30d": 30, "90d": 90, "1y": 365, "all": 3650}.get(period, 90)
        cutoff = timezone.now().date() - timedelta(days=period_days)

        entries = (
            BalanceHistory.objects.filter(
                account__user=request.user,
                date__gte=cutoff,
            )
            .values("date")
            .annotate(total=models.Sum("balance"))
            .order_by("date")
        )

        return Response([
            {"date": e["date"].isoformat(), "net_worth": str(e["total"])}
            for e in entries
        ])


class UserSettingsView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSettingsSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        obj, _created = UserSettings.objects.get_or_create(user=self.request.user)
        return obj


class AlertListView(generics.ListAPIView):
    serializer_class = AlertSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = Alert.objects.filter(user=self.request.user).order_by("-created_at")
        unread = self.request.query_params.get("unread")
        if unread and unread.lower() == "true":
            qs = qs.filter(is_read=False)
        alert_type = self.request.query_params.get("type")
        if alert_type:
            qs = qs.filter(alert_type=alert_type)
        severity = self.request.query_params.get("severity")
        if severity:
            qs = qs.filter(severity=severity)
        return qs


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def mark_alerts_read(request):
    """Mark alerts as read."""
    alert_ids = request.data.get("alert_ids", [])
    if alert_ids:
        Alert.objects.filter(user=request.user, id__in=alert_ids).update(is_read=True)
    else:
        Alert.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return Response({"status": "ok"})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def delete_alerts(request):
    """Delete alerts by ID list, or delete all read alerts."""
    alert_ids = request.data.get("alert_ids", [])
    if alert_ids:
        Alert.objects.filter(user=request.user, id__in=alert_ids).delete()
    else:
        Alert.objects.filter(user=request.user, is_read=True).delete()
    return Response({"status": "ok"})
