"""Tests for accounts: institutions, accounts, and balance history."""

import pytest

from accounts.models import Account, Institution


@pytest.mark.django_db
class TestInstitutions:
    def test_institution_list(self, auth_client):
        Institution.objects.create(name="Chase", institution_type="bank")
        res = auth_client.get("/api/accounts/institutions/")
        assert res.status_code == 200
        data = res.json()
        results = data.get("results", data)
        assert len(results) >= 1
        assert results[0]["name"] == "Chase"

    def test_institution_post_not_allowed(self, auth_client):
        res = auth_client.post(
            "/api/accounts/institutions/",
            {"name": "New Bank", "institution_type": "bank"},
            content_type="application/json",
        )
        assert res.status_code == 405


@pytest.mark.django_db
class TestAccounts:
    def test_list_accounts_empty(self, auth_client):
        res = auth_client.get("/api/accounts/accounts/")
        assert res.status_code == 200
        data = res.json()
        results = data.get("results", data)
        assert results == []

    def test_list_accounts_with_data(self, auth_client, account):
        res = auth_client.get("/api/accounts/accounts/")
        assert res.status_code == 200
        data = res.json()
        results = data.get("results", data)
        assert len(results) == 1
        assert results[0]["name"] == "Test Checking"

    def test_create_account(self, auth_client):
        res = auth_client.post(
            "/api/accounts/accounts/",
            {
                "name": "My Savings",
                "account_type": "savings",
                "balance": "500.00",
                "currency": "USD",
            },
            content_type="application/json",
        )
        assert res.status_code == 201
        assert res.json()["name"] == "My Savings"
        assert res.json()["account_type"] == "savings"

    def test_accounts_scoped_to_user(self, auth_client):
        from django.contrib.auth.models import User
        other_user = User.objects.create_user(username="other", password="pass")
        Account.objects.create(
            user=other_user, name="Other Account", account_type="checking", balance=0
        )
        res = auth_client.get("/api/accounts/accounts/")
        assert res.status_code == 200
        data = res.json()
        results = data.get("results", data)
        assert results == []


@pytest.mark.django_db
class TestBalanceHistory:
    def test_create_balance_history(self, auth_client, account):
        res = auth_client.post(
            "/api/accounts/balance-history/",
            {
                "account": account.id,
                "date": "2026-03-01",
                "balance": "1200.00",
            },
            content_type="application/json",
        )
        assert res.status_code == 201
        assert res.json()["balance"] == "1200.00"

    def test_balance_history_rejects_other_user_account(self, auth_client):
        from django.contrib.auth.models import User
        other_user = User.objects.create_user(username="other2", password="pass")
        other_account = Account.objects.create(
            user=other_user, name="Other", account_type="checking", balance=0
        )
        res = auth_client.post(
            "/api/accounts/balance-history/",
            {
                "account": other_account.id,
                "date": "2026-03-01",
                "balance": "999.00",
            },
            content_type="application/json",
        )
        assert res.status_code == 403
