"""Tests for the schedule generation engine.

Reference loan (capital & interest):
    principal   : Decimal('100000.00')
    annual_rate : Decimal('0.0525') - 5.25%
    term_months : 12
    start_date  : 2026-03-01
    repayment   : CAPITAL_AND_INTEREST
    rate_type   : FIXED

Pre-computed expected values (actual/365 interest, /12 annuity payment):
    monthly payment : 8572.21
    total interest  : 2882.15
    total principal : 100000.00
    final payment   : 8587.84 (adjusted to clear residual)

Reference loan (interest only):
    principal   : Decimal('100000.00')
    annual_rate : Decimal('0.0525') - 5.25%
    term_months : 12
    start_date  : 2026-03-01
    repayment   : INTEREST_ONLY
    rate_type   : FIXED

Pre-computed expected values (actual/365 interest, /12 annuity payment):
    monthly payment : varies by day count (no fixed annuity payment)
    total interest  : 5250.01
    total principal : 100000.00 (balloon on final installment)
    final payment   : 100402.74 (100000.00 principal + 402.74 interest)
"""

from dataclasses import FrozenInstanceError
from typing import Any

import datetime
from decimal import Decimal

from amortise.models.loan import LoanRequest, RepaymentType, RateType
from amortise.models.schedule import Schedule, Installment, CalcTrace
from amortise.engine.schedule import generate_schedule

import pytest
# --------------------------------------------------------------
# Helpers
# --------------------------------------------------------------

VALID: dict[str, Any] = {
    'principal': Decimal('100000.00'),
    'annual_rate': Decimal('0.0525'),
    'term_months': 12,
    'start_date': datetime.date(2026, 3, 1),
    'repayment_type': RepaymentType.CAPITAL_AND_INTEREST,
    'rate_type': RateType.FIXED,
}

def make_loan(**overrides: object) -> LoanRequest:
    return LoanRequest(**{**VALID, **overrides})

# --------------------------------------------------------------
# Schedule structure
# --------------------------------------------------------------

class TestScheduleStructure:
    def test_returns_schedule(self) -> None:
        assert isinstance(generate_schedule(make_loan()), Schedule)

    def test_installment_count_equals_term_months(self) -> None:
        schedule = generate_schedule(make_loan())
        assert len(schedule.installments) == 12

    def test_installment_is_tuple(self) -> None:
        schedule = generate_schedule(make_loan())
        assert isinstance(schedule.installments, tuple)

    def test_each_installment_is_installment(self) -> None:
        schedule = generate_schedule(make_loan())
        assert all(isinstance(i, Installment) for i in schedule.installments)
    def test_installment_has_calc_trace(self) -> None:
        schedule = generate_schedule(make_loan())
        assert all(isinstance(i.calc_trace, CalcTrace) for i in schedule.installments)

    def test_installment_numbers_are_sequential(self) -> None:
        schedule = generate_schedule(make_loan())
        numbers = [i.number for i in schedule.installments]
        assert numbers == list(range(1, 13))

    def test_loan_is_stored_on_schedule(self) -> None:
        loan = make_loan()
        schedule = generate_schedule(loan)
        assert loan == schedule.loan

    def test_schedule_is_immutable(self) -> None:
        schedule = generate_schedule(make_loan())
        with pytest.raises(FrozenInstanceError):
            schedule.installments = () #type:ignore[misc]
    
# --------------------------------------------------------------
# Payment dates
# --------------------------------------------------------------

class TestPaymentDates:
    def test_first_payment_date_is_one_month_after_start(self) -> None:
        schedule = generate_schedule(make_loan())
        assert schedule.installments[0].payment_date == datetime.date(2026, 4, 1)

    def test_last_payment_date_is_start_plus_term(self) -> None:
            schedule = generate_schedule(make_loan())
            assert schedule.installments[-1].payment_date == datetime.date(2027, 3, 1)

    def test_payment_dates_advance_monthly(self) -> None:
        schedule = generate_schedule(make_loan())
        dates = [i.payment_date for i in schedule.installments]
        expected = [
            datetime.date(2026, 4, 1),
            datetime.date(2026, 5, 1),
            datetime.date(2026, 6, 1),
            datetime.date(2026, 7, 1),
            datetime.date(2026, 8, 1),
            datetime.date(2026, 9, 1),
            datetime.date(2026, 10, 1),
            datetime.date(2026, 11, 1),
            datetime.date(2026, 12, 1),
            datetime.date(2027, 1, 1),
            datetime.date(2027, 2, 1),
            datetime.date(2027, 3, 1)
        ]
        assert dates == expected

# --------------------------------------------------------------
# Balance progression
# --------------------------------------------------------------

class TestBalanceProgression:
    def test_opening_balance_row1_equals_principal(self) -> None:
        schedule = generate_schedule(make_loan())
        assert schedule.installments[0].opening_balance == Decimal('100000.00')

    def test_closing_balance(self) -> None:
        schedule = generate_schedule(make_loan())
        assert schedule.installments[0].closing_balance == Decimal('91873.68')

    def test_each_opening_balance_equals_previous_closing(self) -> None:
        schedule = generate_schedule(make_loan())
        for prev, curr in zip(
            schedule.installments[:-1], schedule.installments[1:], strict=True
        ):
            assert curr.opening_balance == prev.closing_balance

    def test_final_closing_balance(self) -> None:
        schedule = generate_schedule(make_loan())
        assert schedule.installments[-1].closing_balance == Decimal('0.00')

    def test_balance_decreases_each_row(self) -> None:
        schedule = generate_schedule(make_loan())
        for inst in schedule.installments:
            assert inst.closing_balance < inst.opening_balance

# --------------------------------------------------------------
# Capital & interest payment amounts
# --------------------------------------------------------------

class TestCapitalAndInterestPayments:
    def test_fixed_payment_amount(self) -> None:
        schedule = generate_schedule(make_loan())
        for inst in schedule.installments[:-1]:
            assert inst.payment == Decimal('8572.21')

    def test_final_payment_adjusted_to_clear_balance(self) -> None:
        schedule = generate_schedule(make_loan())
        assert schedule.installments[-1].payment == Decimal("8587.84")

    def test_payment_equals_principal_plus_interest(self) -> None:
        schedule = generate_schedule(make_loan())
        for inst in schedule.installments:
            assert inst.payment == inst.principal + inst.interest

    def test_total_principal_equals_loan_principal(self) -> None:
        schedule = generate_schedule(make_loan())
        total = sum(i.principal for i in schedule.installments)
        assert total == Decimal('100000.00')

    def test_total_interest(self) -> None:
        schedule = generate_schedule(make_loan())
        total = sum(i.interest for i in schedule.installments)
        assert total == Decimal("2882.15")

    def test_interest_varies_by_day_count(self) -> None:
        # Row 1 (31 days for March) and Row 2 (30 days for April) may differ
        schedule = generate_schedule(make_loan())
        assert schedule.installments[0].interest != schedule.installments[1].interest

# --------------------------------------------------------------
# Interest figures - spot checks agsinst reference values
# --------------------------------------------------------------

class TestInterestSpotChecks:
    def test_row1_interest(self) -> None:
        schedule = generate_schedule(make_loan())
        assert schedule.installments[0].interest == Decimal("445.89")

    def test_row2_interest(self) -> None:
        schedule = generate_schedule(make_loan())
        assert schedule.installments[1].interest == Decimal("396.44")

    def test_row12_interest(self) -> None:
        schedule = generate_schedule(make_loan())
        assert schedule.installments[11].interest == Decimal("34.45")

    def test_row1_days_in_period(self) -> None:
        schedule = generate_schedule(make_loan())
        assert schedule.installments[0].calc_trace.days_in_period == 31

    def test_row2_days_in_period(self) -> None:
        schedule = generate_schedule(make_loan())
        assert schedule.installments[1].calc_trace.days_in_period == 30

    def test_row12_days_in_period(self) -> None:
        schedule = generate_schedule(make_loan())
        assert schedule.installments[11].calc_trace.days_in_period == 28
        
# --------------------------------------------------------------
# Interest only
# --------------------------------------------------------------

class TestInterestOnly:
    def test_principal_is_zero_for_all_but_last(self) -> None:
        loan = make_loan(repayment_type=RepaymentType.INTEREST_ONLY)
        schedule = generate_schedule(loan)
        for inst in schedule.installments[:-1]:
            assert inst.principal == Decimal('0.00')

    def test_opening_balance_constant_until_final(self) -> None:
        loan = make_loan(repayment_type=RepaymentType.INTEREST_ONLY)
        schedule = generate_schedule(loan)
        for inst in schedule.installments[:-1]:
            assert inst.opening_balance == Decimal('100000.00')

    def test_final_installment_repays_full_principal(self) -> None:
        loan = make_loan(repayment_type=RepaymentType.INTEREST_ONLY)
        schedule = generate_schedule(loan)
        assert schedule.installments[-1].principal == Decimal('100000.00')

    def test_final_closing_balance_is_zero(self) -> None:
        loan = make_loan(repayment_type=RepaymentType.INTEREST_ONLY)
        schedule = generate_schedule(loan)
        assert schedule.installments[-1].closing_balance == Decimal('0.00')

    def test_payment_equals_interest_for_non_final_rows(self) -> None:
        loan = make_loan(repayment_type=RepaymentType.INTEREST_ONLY)
        schedule = generate_schedule(loan)
        for inst in schedule.installments[:-1]:
            assert inst.payment == inst.interest

    def test_final_payment_equals_principal_plus_interest(self) -> None:
        loan = make_loan(repayment_type=RepaymentType.INTEREST_ONLY)
        schedule = generate_schedule(loan)
        assert schedule.installments[-1].payment == schedule.installments[-1].principal + schedule.installments[-1].interest

    def test_total_interest(self) -> None:
        loan = make_loan(repayment_type=RepaymentType.INTEREST_ONLY)
        schedule = generate_schedule(loan)
        assert schedule.total_interest == Decimal("5250.01")

    def test_final_payment_amount(self) -> None:
        loan = make_loan(repayment_type=RepaymentType.INTEREST_ONLY)
        schedule = generate_schedule(loan)
        assert schedule.installments[-1].payment == Decimal("100402.74")
