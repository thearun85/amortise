"""Test for Schedule, Installment and CalcTrace output models."""

import datetime
from dataclasses import FrozenInstanceError
from decimal import ROUND_HALF_UP, Decimal

import pytest

from amortise.models.loan import LoanRequest, RateType, RepaymentType
from amortise.models.schedule import CalcTrace, Installment, Schedule

# ---------------------------------------------------------------
# Builders
# ---------------------------------------------------------------


def make_loan() -> LoanRequest:
    return LoanRequest(
        principal=Decimal("100000.00"),
        annual_rate=Decimal("0.0525"),
        term_months=12,
        start_date=datetime.date(2026, 3, 1),
        repayment_type=RepaymentType.CAPITAL_AND_INTEREST,
        rate_type=RateType.FIXED,
    )


def make_trace(opening_balance: Decimal = Decimal("100000.00")) -> CalcTrace:
    annual_rate: Decimal = Decimal("0.0525")
    days_in_period: int = 31
    days_in_year: int = 365

    interest_gross = (
        opening_balance * annual_rate * Decimal(days_in_period) / Decimal(days_in_year)
    )
    interest_rounded = interest_gross.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    rounding_delta = interest_rounded - interest_gross

    return CalcTrace(
        opening_balance=opening_balance,
        annual_rate=annual_rate,
        days_in_period=days_in_period,
        days_in_year=days_in_year,
        interest_gross=interest_gross,
        interest_rounded=interest_rounded,
        rounding_delta=rounding_delta,
    )


def make_installment(
    number: int, opening_balance: Decimal = Decimal("100000.00")
) -> Installment:
    interest: Decimal = Decimal("100.00")
    principal: Decimal = Decimal("756.00")
    payment: Decimal = principal + interest
    closing_balance: Decimal = opening_balance - principal

    return Installment(
        number=number,
        payment_date=datetime.date(2026, 3, 1),
        opening_balance=opening_balance,
        interest=interest,
        principal=principal,
        payment=payment,
        closing_balance=closing_balance,
        calc_trace=make_trace(opening_balance),
    )


def make_schedule(n: int) -> Schedule:
    installments = tuple(make_installment(i + 1) for i in range(n))
    return Schedule(
        loan=make_loan(),
        installments=installments,
    )


class TestCalcTrace:
    def test_constructs_cleanly(self) -> None:
        trace = make_trace()
        assert trace.opening_balance == Decimal("100000.00")
        assert trace.days_in_year == 365

    def test_rounding_delta_is_difference(self) -> None:
        trace = make_trace()
        assert trace.rounding_delta == trace.interest_rounded - trace.interest_gross

    def test_interest_gross_uses_actual_365_formula(self) -> None:
        trace = make_trace()
        expected = Decimal("100000.00") * Decimal("0.0525") * Decimal(31) / Decimal(365)
        assert trace.interest_gross == expected

    def test_is_immutable(self) -> None:
        trace = make_trace()
        with pytest.raises(FrozenInstanceError):
            trace.opening_balance = Decimal("0.00")  # type: ignore[misc]


class TestInstallment:
    def test_constructs_cleanly(self) -> None:
        installment = make_installment(number=1, opening_balance=Decimal("100000.00"))
        assert installment.number == 1
        assert installment.payment == installment.principal + installment.interest
        assert (
            installment.closing_balance
            == installment.opening_balance - installment.principal
        )

    def test_is_immutable(self) -> None:
        installment = make_installment(number=1, opening_balance=Decimal("100000.00"))
        with pytest.raises(FrozenInstanceError):
            installment.number = 1  # type: ignore[misc]

    def test_calc_trace_is_present(self) -> None:
        installment = make_installment(number=1, opening_balance=Decimal("100000.00"))
        assert isinstance(installment.calc_trace, CalcTrace)


class TestSchedule:
    def test_constructs_cleanly(self) -> None:
        schedule = make_schedule(2)
        assert len(schedule.installments) == 2
        assert isinstance(schedule.generated_at, datetime.datetime)

    def test_generated_at_is_utc(self) -> None:
        schedule = make_schedule(2)
        assert schedule.generated_at.tzinfo is datetime.UTC

    def test_installments_is_tuple(self) -> None:
        schedule = make_schedule(2)
        assert isinstance(schedule.installments, tuple)

    def test_total_interest_sums_interest(self) -> None:
        schedule = make_schedule(2)
        expected = sum(i.interest for i in schedule.installments)
        assert schedule.total_interest == expected

    def test_total_principal_sums_payments(self) -> None:
        schedule = make_schedule(2)
        expected = sum(i.payment for i in schedule.installments)
        assert schedule.total_payment == expected

    def test_is_immutable(self) -> None:
        schedule = make_schedule(2)
        with pytest.raises(FrozenInstanceError):
            schedule.installments = ()  # type: ignore[misc]
