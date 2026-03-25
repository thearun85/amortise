"""Tests for the interest calculation engine.

Reference inputs used throughout:
    opening_balance : Decimal('100000.00')
    annual_rate     : Decimal('0.0525') - 5.25%
    period_start    : 2026-03-01
    period_end      : 2026-04-01 - 31 days

Expected values (actual/365):
    interest_gross  : 100000.00 * 0.0525 * 31 / 365 = 445.8904109589...
    interest_rounded: 445.89
    rounding_delta  : 445.89 - 445.8904... = -0.0004... (negative - rounded down)
"""

from __future__ import annotations

import datetime
from decimal import Decimal
from typing import Any

import pytest

from amortise.engine.interest import DayCountConvention, calculate_interest
from amortise.models.schedule import CalcTrace

# ------------------------------------------------------------------
# Shared reference inputs
# ------------------------------------------------------------------

OPENING_BALANCE = Decimal("100000.00")
ANNUAL_RATE = Decimal("0.0525")
PERIOD_START = datetime.date(2026, 3, 1)
PERIOD_END = datetime.date(2026, 4, 1)  # 31 days

VALID: dict[str, Any] = {
    "opening_balance": OPENING_BALANCE,
    "annual_rate": ANNUAL_RATE,
    "period_start": PERIOD_START,
    "period_end": PERIOD_END,
}


def make_trace(**overrides: object) -> CalcTrace:
    """Return a CalcTrace using the reference inputs, with optional overrides."""
    return calculate_interest(**({**VALID, **overrides}))


# ------------------------------------------------------------------
# Type enforcement
# ------------------------------------------------------------------


class TestTypeEnforcement:
    def test_float_opening_balance_raises(self) -> None:
        with pytest.raises(TypeError, match="'opening_balance' must be Decimal"):
            make_trace(opening_balance=float("100000.00"))

    def test_float_annual_rate_raises(self) -> None:
        with pytest.raises(TypeError, match="'annual_rate' must be Decimal"):
            make_trace(annual_rate=float("0.0525"))

    def test_int_opening_balance_raises(self) -> None:
        with pytest.raises(TypeError, match="'opening_balance' must be Decimal"):
            make_trace(opening_balance=int("100000"))

    def test_int_annual_rate_raises(self) -> None:
        with pytest.raises(TypeError, match="'annual_rate' must be Decimal"):
            make_trace(annual_rate=int("1"))

    def test_str_opening_balance_raises(self) -> None:
        with pytest.raises(TypeError, match="'opening_balance' must be Decimal"):
            make_trace(opening_balance="100000")

    def test_str_annual_rate_raises(self) -> None:
        with pytest.raises(TypeError, match="'annual_rate' must be Decimal"):
            make_trace(annual_rate="1")


# ------------------------------------------------------------------
# Semantic validation
# ------------------------------------------------------------------


class TestSemanticValidation:
    def test_zero_opening_balance_raises(self) -> None:
        with pytest.raises(
            ValueError, match="'opening_balance' must be greater than zero"
        ):
            make_trace(opening_balance=Decimal("0"))

    def test_negative_opening_balance_raises(self) -> None:
        with pytest.raises(
            ValueError, match="'opening_balance' must be greater than zero"
        ):
            make_trace(opening_balance=Decimal("-1"))

    def test_zero_annual_rate_balance_raises(self) -> None:
        with pytest.raises(ValueError, match="'annual_rate' must be greater than zero"):
            make_trace(annual_rate=Decimal("0"))

    def test_negative_annual_rate_raises(self) -> None:
        with pytest.raises(ValueError, match="'annual_rate' must be greater than zero"):
            make_trace(annual_rate=Decimal("-1"))

    def test_period_end_equal_period_start_raises(self) -> None:
        with pytest.raises(ValueError, match="'period_end' must be strictly after"):
            make_trace(period_end=PERIOD_START)

    def test_period_end_before_period_start_raises(self) -> None:
        with pytest.raises(ValueError, match="'period_end' must be strictly after"):
            make_trace(period_end=datetime.date(2026, 2, 1))


# ------------------------------------------------------------------
# CalcTrace output
# ------------------------------------------------------------------


class TestCalcTraceOutput:
    def test_returns_calc_trace(self) -> None:
        calc = make_trace()
        assert isinstance(calc, CalcTrace)

    def test_opening_balance(self) -> None:
        calc = make_trace()
        assert calc.opening_balance == OPENING_BALANCE

    def test_annual_rate(self) -> None:
        calc = make_trace()
        assert calc.annual_rate == ANNUAL_RATE

    def test_days_in_period(self) -> None:
        calc = make_trace()
        assert calc.days_in_period == 31

    def test_days_in_year(self) -> None:
        calc = make_trace()
        assert calc.days_in_year == 365

    def test_interest_gross_uses_actual_365_formula(self) -> None:
        calc = make_trace()
        expected = OPENING_BALANCE * ANNUAL_RATE * Decimal(31) / Decimal(365)
        assert calc.interest_gross == expected

    def test_interest_rounded_to_two_dp(self) -> None:
        calc = make_trace()
        assert calc.interest_rounded == Decimal("445.89")

    def test_rounding_delta_is_rounded_minus_gross(self) -> None:
        calc = make_trace()
        assert calc.rounding_delta == calc.interest_rounded - calc.interest_gross

    def test_default_convention_actual_365(self) -> None:
        calc = make_trace()
        assert calc.days_in_year == 365

    def test_explicit_convention_actual_365(self) -> None:
        calc = make_trace(convention=DayCountConvention.ACTUAL_365)
        assert calc.days_in_year == 365
