"""Tests for portfolio: securities, holdings, and price history."""

import pytest
from decimal import Decimal

from accounts.models import Account
from portfolio.models import Holding, Security


@pytest.fixture
def security(db):
    return Security.objects.create(
        symbol="AAPL",
        name="Apple Inc.",
        security_type="stock",
        exchange="NASDAQ",
    )


@pytest.fixture
def investment_account(user):
    """An investment-type account required by the holding validator."""
    return Account.objects.create(
        user=user,
        name="Brokerage",
        account_type="investment",
        balance=Decimal("0"),
    )


@pytest.mark.django_db
class TestSecurityViewSet:
    def test_security_list(self, auth_client, security):
        res = auth_client.get("/api/portfolio/securities/")
        assert res.status_code == 200
        data = res.json()
        results = data.get("results", data)
        assert len(results) >= 1
        assert results[0]["symbol"] == "AAPL"

    def test_security_post_not_allowed(self, auth_client):
        res = auth_client.post(
            "/api/portfolio/securities/",
            {"symbol": "GOOG", "name": "Alphabet", "security_type": "stock"},
            content_type="application/json",
        )
        assert res.status_code == 405


@pytest.mark.django_db
class TestPriceHistoryViewSet:
    def test_price_history_post_not_allowed(self, auth_client, security):
        res = auth_client.post(
            "/api/portfolio/price-history/",
            {
                "security": security.id,
                "date": "2026-03-01",
                "close_price": "175.00",
            },
            content_type="application/json",
        )
        assert res.status_code == 405


@pytest.mark.django_db
class TestHoldingViewSet:
    def test_create_holding(self, auth_client, investment_account, security):
        res = auth_client.post(
            "/api/portfolio/holdings/",
            {
                "account": investment_account.id,
                "security": security.id,
                "shares": "10.000000",
                "cost_basis": "1500.00",
            },
            content_type="application/json",
        )
        assert res.status_code == 201
        assert res.json()["shares"] == "10.000000"

    def test_list_holdings_scoped_to_user(self, auth_client, user, investment_account, security):
        from django.contrib.auth.models import User

        other_user = User.objects.create_user(username="other_portfolio", password="pass")
        other_account = Account.objects.create(
            user=other_user, name="Other", account_type="investment", balance=0
        )
        Holding.objects.create(
            user=other_user,
            account=other_account,
            security=security,
            shares=Decimal("5.000000"),
            cost_basis=Decimal("750.00"),
        )
        Holding.objects.create(
            user=user,
            account=investment_account,
            security=security,
            shares=Decimal("10.000000"),
            cost_basis=Decimal("1500.00"),
        )
        res = auth_client.get("/api/portfolio/holdings/")
        assert res.status_code == 200
        data = res.json()
        results = data.get("results", data)
        assert len(results) == 1
        assert results[0]["shares"] == "10.000000"
