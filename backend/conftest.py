"""Shared pytest fixtures for the nullbook test suite."""

import pytest
from django.contrib.auth.models import User


@pytest.fixture
def user(db):
    return User.objects.create_user(username="testuser", password="testpass123")


@pytest.fixture
def auth_client(client, user):
    client.login(username="testuser", password="testpass123")
    return client


@pytest.fixture
def account(user):
    from accounts.models import Account
    return Account.objects.create(
        user=user,
        name="Test Checking",
        account_type="checking",
        balance=1000,
        currency="USD",
    )


@pytest.fixture
def category():
    from transactions.models import Category
    return Category.objects.create(name="Dining", icon="utensils")
