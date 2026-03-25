"""Output models for a generated loan repayment schedule.

Three frozen dataclasses, built inside out:

    CalcTrace   - how a single row's interest was calculated
    Installment - one repayment row: dates, amounts, trace
    Schedule    - the full output: originating loan + all installments

All fields are immutable post-construction.
Derived totals are exposed as properties to prevent them
diverging from the installment data.
"""

from __future__ import annotations
from typing import TYPE_CHECKING

import datetime
from dataclasses import dataclass, field
from decimal import Decimal

if TYPE_CHECKING:
    from .loan import LoanRequest

# ------------------------------------------------------------------
# CalcTrace - per-row calculation audit record
# ------------------------------------------------------------------


@dataclass(frozen=True)
class CalcTrace:
    """Exact record of how interest was derived for one installment.

    Carries every value that fed into the interest calculation so
    that any figure on the schedule can be independently reproduced
    and explained. Always present - not a debug flag.

    Attributes:
        opening_balance: Principal outstanding at the start of the period.
        periodic_rate: Monthly interest rate applied (annual_rate / 12).
        days_in_period: Actual number of days in this repayment period.
        days_in_year: Day count denominator - 365 for actual/ 365 convention.
        interest_gross: Raw interest before rounding.
        interest_rounded: Interest after HALF_ROUND_UP rounding to 2dp.
        rounding_delta: Difference between interest_gross and
        interest_rounded. Represents the exact rounding effect on each row.
    """

    opening_balance: Decimal
    periodic_rate: Decimal
    days_in_period: int
    days_in_year: int
    interest_gross: Decimal
    interest_rounded: Decimal
    rounding_delta: Decimal


# ------------------------------------------------------------------
# Installment - one row in the repayment schedule
# ------------------------------------------------------------------


@dataclass(frozen=True)
class Installment:
    """A single repayment installment in schedule.

    Attributes:
        number: 1-based position of this installment in the schedule.
        payment_date: Date on which this installment is due.
        opening_balance: Principal outstanding before this payment.
        interest: Interest component of the payment (rounded).
        principal: Principal repayment component of the payment.
        payment: Total payment due principal + interest.
        closing_balance: Principal outstanding after this payment.
        calc_trace: Full audit record of how interest was calculated.
    """

    number: int
    payment_date: datetime.date
    opening_balance: Decimal
    interest: Decimal
    principal: Decimal
    payment: Decimal
    closing_balance: Decimal
    calc_trace: CalcTrace


# ------------------------------------------------------------------
# Schedule - the complete output
# ------------------------------------------------------------------


@dataclass(frozen=True)
class Schedule:
    """A fully generated loan repayment schedule.

    Attributes:
        loan: The LoanRequest that produced this schedule.
        installments: Ordered tuple of every repayment row.
        Tuple - not list - to preserve immutability of the output.
        generated_at: UTC timestamp of when the schedule was generated.
        Defaults to now. Retained for audit and reproducibility.
    """

    loan: LoanRequest
    installments: tuple[Installment, ...]
    generated_at: datetime.datetime = field(
        default_factory=lambda: datetime.datetime.now(tz=datetime.UTC)
    )

    @property
    def total_interest(self) -> Decimal:
        """Sum of interest across all installments."""
        return sum((i.interest for i in self.installments), Decimal("0"))

    @property
    def total_payment(self) -> Decimal:
        """Sum of all payments across all installments."""
        return sum((i.payment for i in self.installments), Decimal("0"))
