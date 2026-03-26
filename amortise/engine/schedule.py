"""Schedule generation engine.

Provides a single public function, ``generate_schedule``,
that produces a fully populated ``Schedule`` from a ``LoanRequest``.

Payment model (see ADR-002)
---------------------------
- Payment amount is derived once using the standard annuity formula
with ``annual_rate / 12`` as the periodic rate. This produces a
fixed payment for all installments except the last.
- Interest per installment is calculated using the ``actual/365``
day count convention via ``calculate_interest()``.
- Principal = payment - interest_rounded per row.
- The final installment absorbs any rounding residual so that
closing balance is exactly zero.

Payment timing (see ADR-003)
----------------------------
- Payment in arrears. start_date`` is the disbursement date.
- Row 1: period_start = start_date, period_end = start_date + 1 month.
- payment_date = period_end for every installment.

Repayment types
---------------
- ``CAPITAL_AND_INTEREST``: fixed payment, principal reduces each row
- ``INTEREST_ONLY``: interest-only payments throughout;
full principal repaid as ballon on the final installment.
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal
from typing import TYPE_CHECKING

from dateutil.relativedelta import relativedelta

from amortise.engine.interest import calculate_interest
from amortise.models.loan import RepaymentType
from amortise.models.schedule import Installment, Schedule

if TYPE_CHECKING:
    import datetime

    from amortise.models.loan import LoanRequest


# --------------------------------------------------------------------
# Internal helpers
# --------------------------------------------------------------------

_TWO_DP = Decimal("0.01")


def _annuity_payment(
    principal: Decimal, annual_rate: Decimal, term_months: int
) -> Decimal:
    """Derive the fixed monthly payment using the standard annuity formula.
    Formula:
        r = annual_rate / 12
        payment = principal * (r * (1 + r)^n) / ((1 + r)^n - 1)

    Args:
        principal: Loan amount.
        annual_rate: Annual interest rate as a Decimal fraction.
        term_months: Loan term in months.

    Returns:
        Fixed monthly payment rounded to 2dp with ``ROUND_HALF_UP``.
    """
    r = annual_rate / 12
    n = term_months
    factor = (1 + r) ** n
    payment = principal * (r * factor) / (factor - 1)
    return payment.quantize(_TWO_DP, rounding=ROUND_HALF_UP)


# --------------------------------------------------------------------
# Public interface
# --------------------------------------------------------------------


def generate_schedule(loan: LoanRequest) -> Schedule:
    """Generate a full repayment schedule for the given loan.

    Args:
        loan: Immutable ``LoanRequest`` describing the loan
        parameters.

    Returns:
        A fully populated ``Schedule`` with one ``Installment``
        per month, each carrying a ``CalcTrace`` of the exact interest calculation.
    """
    installments: list[Installment] = []

    if loan.repayment_type == RepaymentType.CAPITAL_AND_INTEREST:
        installments = _build_capital_and_interest(loan)
    else:
        installments = _build_interest_only(loan)

    return Schedule(
        loan=loan,
        installments=tuple(installments),
    )


# --------------------------------------------------------------------
# Repayment type builders
# --------------------------------------------------------------------


def _build_capital_and_interest(loan: LoanRequest) -> list[Installment]:
    """Build installments for a capital & interest loan."""
    payment = _annuity_payment(loan.principal, loan.annual_rate, loan.term_months)
    balance = loan.principal
    installments: list[Installment] = []
    for i in range(1, loan.term_months + 1):
        period_start: datetime.date = loan.start_date + relativedelta(months=i - 1)
        period_end: datetime.date = loan.start_date + relativedelta(months=i)

        trace = calculate_interest(balance, loan.annual_rate, period_start, period_end)
        interest = trace.interest_rounded
        is_final = i == loan.term_months

        if is_final:
            principal = balance
            total_payment = (principal + interest).quantize(
                _TWO_DP, rounding=ROUND_HALF_UP
            )

        else:
            principal = (payment - interest).quantize(_TWO_DP, rounding=ROUND_HALF_UP)
            total_payment = payment
        closing_balance = (balance - principal).quantize(
            _TWO_DP, rounding=ROUND_HALF_UP
        )

        installments.append(
            Installment(
                number=i,
                payment_date=period_end,
                opening_balance=balance,
                interest=interest,
                principal=principal,
                payment=total_payment,
                closing_balance=closing_balance,
                calc_trace=trace,
            )
        )

        balance = closing_balance

    return installments


def _build_interest_only(loan: LoanRequest) -> list[Installment]:
    """Build installments for an interest-only loan."""
    balance = loan.principal
    installments: list[Installment] = []

    for i in range(1, loan.term_months + 1):
        period_start: datetime.date = loan.start_date + relativedelta(months=i - 1)
        period_end: datetime.date = loan.start_date + relativedelta(months=i)

        trace = calculate_interest(balance, loan.annual_rate, period_start, period_end)
        interest = trace.interest_rounded

        is_final = i == loan.term_months

        principal = balance if is_final else Decimal("0.00")

        total_payment = (principal + interest).quantize(_TWO_DP, rounding=ROUND_HALF_UP)
        closing_balance = (balance - principal).quantize(
            _TWO_DP, rounding=ROUND_HALF_UP
        )

        installments.append(
            Installment(
                number=i,
                payment_date=period_end,
                opening_balance=balance,
                interest=interest,
                principal=principal,
                payment=total_payment,
                closing_balance=closing_balance,
                calc_trace=trace,
            )
        )

        balance = closing_balance

    return installments
