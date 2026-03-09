"""Tests for taxes: tax years, deductions, and the estimate endpoint."""

import pytest
from decimal import Decimal

from taxes.models import TaxYear


@pytest.fixture
def tax_year(user):
    return TaxYear.objects.create(
        user=user,
        year=2025,
        filing_status="single",
        federal_tax_paid=Decimal("5000.00"),
        state_tax_paid=Decimal("1500.00"),
    )


@pytest.mark.django_db
class TestTaxYears:
    def test_create_tax_year(self, auth_client):
        res = auth_client.post(
            "/api/taxes/tax-years/",
            {"year": 2025, "filing_status": "single"},
            content_type="application/json",
        )
        assert res.status_code == 201
        assert res.json()["year"] == 2025
        assert res.json()["filing_status"] == "single"

    def test_list_tax_years_scoped_to_user(self, auth_client, user, tax_year):
        from django.contrib.auth.models import User

        other_user = User.objects.create_user(username="other_tax", password="pass")
        TaxYear.objects.create(user=other_user, year=2025, filing_status="single")

        res = auth_client.get("/api/taxes/tax-years/")
        assert res.status_code == 200
        data = res.json()
        results = data.get("results", data)
        assert len(results) == 1
        assert results[0]["year"] == 2025

    def test_duplicate_year_rejected(self, auth_client, tax_year):
        res = auth_client.post(
            "/api/taxes/tax-years/",
            {"year": 2025, "filing_status": "married_joint"},
            content_type="application/json",
        )
        assert res.status_code == 400


@pytest.mark.django_db
class TestDeductions:
    def test_create_deduction(self, auth_client, tax_year):
        res = auth_client.post(
            "/api/taxes/deductions/",
            {
                "tax_year": tax_year.id,
                "deduction_type": "charitable",
                "description": "Donation to Red Cross",
                "amount": "250.00",
            },
            content_type="application/json",
        )
        assert res.status_code == 201
        data = res.json()
        assert data["amount"] == "250.00"
        assert data["deduction_type"] == "charitable"

    def test_deduction_rejected_for_other_user_tax_year(self, auth_client):
        from django.contrib.auth.models import User

        other_user = User.objects.create_user(username="other_ded", password="pass")
        other_tax_year = TaxYear.objects.create(
            user=other_user, year=2024, filing_status="single"
        )
        res = auth_client.post(
            "/api/taxes/deductions/",
            {
                "tax_year": other_tax_year.id,
                "deduction_type": "charitable",
                "description": "Unauthorized deduction",
                "amount": "100.00",
            },
            content_type="application/json",
        )
        assert res.status_code == 400


@pytest.mark.django_db
class TestTaxEstimate:
    def test_estimate_returns_summary(self, auth_client, tax_year):
        res = auth_client.get(f"/api/taxes/tax-years/{tax_year.id}/estimate/")
        assert res.status_code == 200
        data = res.json()
        assert data["tax_year"] == 2025
        assert "total_income" in data
        assert "tax_breakdown" in data
