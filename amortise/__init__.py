"""amortise - loan repayment schedule generation and validation.

Public API
----------
    generate_schedule(loan: LoanRequest) -> Schedule
        Generate a full repayment schedule from a loan request.

    LoanRequest     - immutable input describing the loan
    RepaymentType   - CAPITAL_AND_INTEREST | INTEREST_ONLY
    RateType        - FIXED | VARIABLE
    Schedule        - complete output: loan + installments + totals
    Installment     - one repayment row: dates, amounts, calc trace
    CalcTrace       - per-row audit record of the interest calculation

Example
-------
    from decimal import Decimal
    import datetime
    from amortise import generate_schedule, LoanRequest, RepaymentType, RateType

    loan = LoanRequest(
        principal=Decimal('100000.00'),
        annual_rate=Decimal('0.0525'), # 5.25%
        term_months=12,
        start_date=datetime.date(2026, 3, 1),
        repayment_type=RepaymentType.CAPITAL_AND_INTEREST,
        rate_type=RateType.FIXED,
    )
    schedule = generate_schedule(loan)

    for installment in schedule.installments:
        print(
            installment.number,
            installment.payment_date,
            installment.payment,
            installment.closing_balance,
        )
"""


from amortise.engine.schedule import generate_schedule
from amortise.models.loan import LoanRequest, RepaymentType, RateType
from amortise.models.schedule import CalcTrace, Installment, Schedule

__all__ = [
    'CalcTrace',
    'Installment',
    'LoanRequest',
    'RateType',
    'RepaymentType',
    'Schedule',
    'generate_schedule',
]
