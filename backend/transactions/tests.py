"""Tests for transactions: CRUD, spending summary, budgets."""

import pytest
from decimal import Decimal
from datetime import date

from transactions.models import Budget, Transaction


@pytest.mark.django_db
class TestTransactionCRUD:
    def test_create_transaction(self, auth_client, account, category):
        res = auth_client.post(
            "/api/transactions/transactions/",
            {
                "account": account.id,
                "category": category.id,
                "date": "2026-03-01",
                "amount": "42.50",
                "transaction_type": "expense",
                "description": "Test lunch",
            },
            content_type="application/json",
        )
        assert res.status_code == 201
        assert res.json()["description"] == "Test lunch"

    def test_list_transactions(self, auth_client, account, user):
        Transaction.objects.create(
            user=user, account=account, date=date(2026, 3, 1),
            amount=Decimal("10.00"), transaction_type="expense", description="Coffee",
        )
        res = auth_client.get("/api/transactions/transactions/")
        assert res.status_code == 200
        assert res.json()["count"] == 1


@pytest.mark.django_db
class TestSpendingSummary:
    def test_spending_summary(self, auth_client, account, category, user):
        Transaction.objects.create(
            user=user, account=account, category=category,
            date=date(2026, 3, 1), amount=Decimal("25.00"),
            transaction_type="expense", description="Dinner",
        )
        res = auth_client.get("/api/transactions/transactions/spending_summary/")
        assert res.status_code == 200
        data = res.json()
        assert len(data) >= 1
        assert data[0]["category_name"] == "Dining"


@pytest.mark.django_db
class TestBudgets:
    def test_create_budget(self, auth_client, category):
        res = auth_client.post(
            "/api/transactions/budgets/",
            {"category": category.id, "amount": "500.00", "period": "monthly"},
            content_type="application/json",
        )
        assert res.status_code == 201
        assert res.json()["amount"] == "500.00"

    def test_budget_progress(self, auth_client, account, category, user):
        Budget.objects.create(user=user, category=category, amount=Decimal("500.00"))
        Transaction.objects.create(
            user=user, account=account, category=category,
            date=date.today(), amount=Decimal("100.00"),
            transaction_type="expense", description="Test",
        )
        res = auth_client.get("/api/transactions/budgets/progress/")
        assert res.status_code == 200
        data = res.json()
        assert len(data) == 1
        assert Decimal(data[0]["spent"]) == Decimal("100.00")


@pytest.mark.django_db
class TestBulkOperations:
    def test_bulk_delete(self, auth_client, account, user):
        t1 = Transaction.objects.create(
            user=user, account=account, date=date(2026, 3, 1),
            amount=Decimal("10.00"), transaction_type="expense", description="A",
        )
        t2 = Transaction.objects.create(
            user=user, account=account, date=date(2026, 3, 1),
            amount=Decimal("20.00"), transaction_type="expense", description="B",
        )
        res = auth_client.post(
            "/api/transactions/transactions/bulk_delete/",
            {"ids": [t1.id, t2.id]},
            content_type="application/json",
        )
        assert res.status_code == 200
        assert res.json()["deleted"] == 2

    def test_export_csv(self, auth_client, account, user):
        Transaction.objects.create(
            user=user, account=account, date=date(2026, 3, 1),
            amount=Decimal("10.00"), transaction_type="expense", description="Coffee",
        )
        res = auth_client.get("/api/transactions/transactions/export/")
        assert res.status_code == 200
        assert res["Content-Type"] == "text/csv"
        content = b"".join(res.streaming_content).decode()
        assert "Coffee" in content
