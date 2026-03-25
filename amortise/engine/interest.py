"""Interest calculation engine.

Provides a single public function, ``calculate_interest``, that computes
the interest due for one repayment period and returns a fully populated
``CalcTrace`` capturing every input and intermediate value.

Day count conventions
---------------------
Omly ``ACTUAL_365`` is supported in Phase 1. The convention is encoded
as a ``StrEnum`` so additional conventions (ACT/360, 30/360, etc.) can
be added later without a breaking interface change.

ACTUAl_365
    days_in_period = (period_end - period_start).days
    interest_gross = opening_balance * annual_rate * (days_in_period / 365)
    ``period_end`` is exclusive - the period March 1 -> April 1 is 31 days.
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal
from enum import StrEnum
from typing import TYPE_CHECKING

from amortise.models.schedule import CalcTrace

if TYPE_CHECKING:
    import datetime

# --------------------------------------------------------------
# Day  count convention
# --------------------------------------------------------------

_DAYS_IN_YEAR_ACTUAL_365: int = 365


class DayCountConvention(StrEnum):
    """Supported day count conventions for interest calculation.

    Attributes:
        ACTUAL_365: Actual days in period divided by 365.
    """

    ACTUAL_365 = "actual_365"


# --------------------------------------------------------------
# Public Interface
# --------------------------------------------------------------


def calculate_interest(
    opening_balance: Decimal,
    annual_rate: Decimal,
    period_start: datetime.date,
    period_end: datetime.date,
    convention: DayCountConvention = DayCountConvention.ACTUAL_365,
) -> CalcTrace:
    """Calculate interest for one repayment period.

    Args:
        opening_balance: Principal outstanding at the start of the period.
        annual_rate: Annual interest rate as a decimal fraction
            (e.g. ``Decimal('0.0525'))``).
        period_start: First day of the interest period (inclusive).
        period_end: First day of the next period (exclusve).
        convention: Day count convention to apply. Defaults to ``ACTUAL_365``.

    Returns:
        A fully populated ``CalcTrace`` recording every input and
        intermediate value used to derive the interest figure.

    Raises:
        TypeError: If ``opening_balance`` or ``annual_rate`` is not a
        ``Decimal``.
        ValueError: If ``period_end`` is not strictly after
        ``period_start``, or if ``opening_balance`` or ``annual_rate``
        is not positive.
    """

    if not isinstance(opening_balance, Decimal):
        raise TypeError(
            f"'opening_balance' must be Decimal, "
            f"got {type(opening_balance).__name__!r}."
            f"Floats and strings are not accepted. See ADR-001."
        )

    if not isinstance(annual_rate, Decimal):
        raise TypeError(
            f"'annual_rate' must be Decimal, "
            f"got {type(annual_rate).__name__!r}."
            f"Floats and strings are not accepted. See ADR-001."
        )

    if opening_balance <= Decimal("0"):
        raise ValueError(
            f"'opening_balance' must be greater than zero, got {opening_balance!r}."
        )

    if annual_rate <= Decimal("0"):
        raise ValueError(
            f"'annual_rate' must be greater than zero, got {annual_rate!r}."
        )

    if period_end <= period_start:
        raise ValueError(
            f"'period_end' must be strictly after 'period_start', "
            f"got period_start={period_start!r}, period_end={period_end!r}."
        )

    days_in_period: int = (period_end - period_start).days
    days_in_year: int = _DAYS_IN_YEAR_ACTUAL_365

    interest_gross: Decimal = (
        opening_balance * annual_rate * Decimal(days_in_period) / Decimal(days_in_year)
    )

    interest_rounded: Decimal = interest_gross.quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )

    rounding_delta: Decimal = interest_rounded - interest_gross

    return CalcTrace(
        opening_balance=opening_balance,
        annual_rate=annual_rate,
        days_in_period=days_in_period,
        days_in_year=days_in_year,
        interest_gross=interest_gross,
        interest_rounded=interest_rounded,
        rounding_delta=rounding_delta,
    )
