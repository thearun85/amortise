"""Input model for a loan repayment schedule request.

Only fields required for Phase 1 are defined here.
 - Rate Type - Fixed and Variable
 - Payment frequency - Monthly
 - Repayment types - Principal & interest and Interest only 
 - Days - actual/365

 No float values are accepted. All monetary and rate inputs must be supplied as str or Decimal. Floats are rejected as the boundary.
 """
 
from enum import StrEnum
from dataclasses import dataclass
from decimal import Decimal
import datetime


class RateType(StrEnum):
    """Whether the interest rate type is fixed or variable."""
    FIXED = 'f'
    VARIABLE = 'v'

class RepaymentType(StrEnum):
    """How the loan is repaid over its term."""
    PRINCIPAL_AND_INTEREST = 'pi'
    INTEREST_ONLY = 'i'

# -------------------------------------------------------------------------
# Loan Request
# -------------------------------------------------------------------------
@dataclass(frozen=True)
class LoanRequest:
    """Immutable input describing a loan for which a schedule is requested.
    Attributes:
        principal: Loan amount in currency units (e.g. Decimal('250000.00')).
        annual_rate: Annual interest rate as a decimal fraction, not a percentage (e.g. Decimal('0..525') for 5.25%).
        term_months: Loan term in whole months (e.g. 300 for 25 years).
        start_date: Date of the first payment start date
        repayment_type: Whether installments cover principal + interest or interest only.
        rate_type: Whether the rate is fixed for the term or variable.
    """
    principal: Decimal
    annual_rate: Decimal
    term_months: int
    start_date: datetime.date
    repayment_type: RepaymentType
    rate_type: RateType

    def __post_init__(self) -> None:
        if not isinstance(self.principal, Decimal):
            raise TypeError(
                f"'principal' must be Decimal, got "
                f"{type(self.principal).__name__!r}."
                "Floats are not accepted. See ADR-001."
            )
        if not isinstance(self.annual_rate, Decimal):
            raise TypeError(
                f"'annual_rate' must be Decimal, got "
                f"{type(self.annual_rate).__name__!r}."
                "Floats are not accepted. See ADR-001."
            )

        if self.principal <= Decimal('0'):
            raise ValueError(f"'principal' must be greater than zero, got {self.principal!r}")

        if not (Decimal('0') < self.annual_rate <= Decimal('1')):
            raise ValueError(
            f"'annual_rate' must be between 0 (exclusive) and 1 (inclusive)"
            f"as a decimal fraction, got {self.annual_rate!r}. "
            "Example: Decimal('0.0525') for 5.25%."
            )

        if self.term_months <= 0:
            raise ValueError("f'term_months' must be greater than zero, got {self.term_months!r}")
