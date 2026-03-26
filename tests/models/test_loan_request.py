"""Tests for LoanRequest input model."""

import datetime
from dataclasses import FrozenInstanceError
from decimal import Decimal
from typing import Any

import pytest

from amortise.models.loan import LoanRequest, RateType, RepaymentType

# -----------------------------------------------------------------
# Shared valid kwargs - override individual fields per test
# -----------------------------------------------------------------

VALID: dict[str, Any] = {
    "principal": Decimal("250000.00"),
    "annual_rate": Decimal("0.0525"),
    "term_months": 300,
    "start_date": datetime.date(2026, 1, 1),
    "repayment_type": RepaymentType.CAPITAL_AND_INTEREST,
    "rate_type": RateType.FIXED,
}


def make(**overrides: object) -> LoanRequest:
    return LoanRequest(**{**VALID, **overrides})


# -----------------------------------------------------------------
# Happy path
# -----------------------------------------------------------------


class TestValidLoanRequest:
    def test_constructs_cleanly(self) -> None:
        loan = make()
        assert loan.principal == Decimal("250000.00")
        assert loan.annual_rate == Decimal("0.0525")
        assert loan.term_months == 300
        assert loan.start_date == datetime.date(2026, 1, 1)
        assert loan.repayment_type == RepaymentType.CAPITAL_AND_INTEREST
        assert loan.rate_type == RateType.FIXED

    def test_interest_only_variable(self) -> None:
        loan = make(
            repayment_type=RepaymentType.INTEREST_ONLY, rate_type=RateType.VARIABLE
        )
        assert loan.repayment_type == RepaymentType.INTEREST_ONLY
        assert loan.rate_type == RateType.VARIABLE

    def test_rate_at_upper_boundary(self) -> None:
        loan = make(annual_rate=Decimal("1"))
        assert loan.annual_rate == Decimal("1")

    def test_term_months_at_lower_boundary(self) -> None:
        loan = make(term_months=1)
        assert loan.term_months == 1


# -----------------------------------------------------------------
# Type enforcement - floats and strings rejected
# -----------------------------------------------------------------


class TestTypeEnforcement:
    def test_float_principal_raises(self) -> None:
        with pytest.raises(TypeError, match="'principal' must be Decimal"):
            make(principal=float("250000.00"))

    def test_float_annual_rate_raises(self) -> None:
        with pytest.raises(TypeError, match="'annual_rate' must be Decimal"):
            make(annual_rate=float("0.0525"))

    def test_str_principal_raises(self) -> None:
        with pytest.raises(TypeError, match="'principal' must be Decimal"):
            make(principal="250000.00")

    def test_str_annual_rate_raises(self) -> None:
        with pytest.raises(TypeError, match="'annual_rate' must be Decimal"):
            make(annual_rate="0.0525")

    def test_int_principal_raises(self) -> None:
        with pytest.raises(TypeError, match="'principal' must be Decimal"):
            make(principal=250000)

    def test_int_annual_rate_raises(self) -> None:
        with pytest.raises(TypeError, match="'annual_rate' must be Decimal"):
            make(annual_rate=int(0.0525))


# -----------------------------------------------------------------
# Semantic validation - principal
# -----------------------------------------------------------------


class TestPrincipalValidation:
    def test_zero_principal_raises(self) -> None:
        with pytest.raises(ValueError, match="'principal' must be greater than zero"):
            make(principal=Decimal("0"))

    def test_negative_principal_raises(self) -> None:
        with pytest.raises(ValueError, match="'principal' must be greater than zero"):
            make(principal=Decimal("-1"))


# -----------------------------------------------------------------
# Semantic validation - annual_rate
# -----------------------------------------------------------------


class TestAnnualRateValidation:
    def test_zero_annual_rate_raises(self) -> None:
        with pytest.raises(ValueError, match="'annual_rate' must be between"):
            make(annual_rate=Decimal("0"))

    def test_above_one_annual_rate_raises(self) -> None:
        with pytest.raises(ValueError, match="'annual_rate' must be between"):
            make(annual_rate=Decimal("1.1"))

    def test_negative_annual_rate_raises(self) -> None:
        with pytest.raises(ValueError, match="'annual_rate' must be between"):
            make(annual_rate=Decimal("-1"))


# -----------------------------------------------------------------
# Semantic validation - term_months
# -----------------------------------------------------------------


class TestTermMonthsValidation:
    def test_zero_term_months_raises(self) -> None:
        with pytest.raises(ValueError, match="'term_months' must be greater than zero"):
            make(term_months=0)

    def test_negative_term_months_raises(self) -> None:
        with pytest.raises(ValueError, match="'term_months' must be greater than zero"):
            make(term_months=-1)


# -----------------------------------------------------------------
# Test Immutability
# -----------------------------------------------------------------


class TestImmutability:
    def test_cannot_mutate_principal(self) -> None:
        loan = make()
        with pytest.raises(FrozenInstanceError):
            loan.principal = Decimal("100000.00")  # type: ignore[misc]

    def test_cannot_mutate_annual_rate(self) -> None:
        loan = make()
        with pytest.raises(FrozenInstanceError):
            loan.annual_rate = Decimal("1.0")  # type: ignore[misc]
