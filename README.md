# amortise

> Loan repayment schedule generation and validation in Python.

`amortise is an open-source Python library for generating and validating loan repayment schedules. It is built for correctness, auditability, and explainability - every output row carries a full calculation trace recording the exact formula, values and rounding applied.

---

## Status

`v0.1.0-alpha` - Phase 1 (core-engine) in progress. Not yet published to PyPI.

--- 

## Features

**Phase 1 - available now**

- Capital & interest and interst-only repayment types
- Fixed and variable rate loan structures
- `actual/365` day count convention - actual calendar days per period
- Fixed monthly payment derived via the standard annuity formula
- Per-row `CalcTrace` - every installment records opening balance, annual rate, day count, gross interest, rounded interest and rounding delta
- Fully immutable outputs - all dataclasses are frozen post-construction
- `Decimal` throughout - no floats, no silent precision loss

**Planned**

- Phase 2: Prepayments, balloon payments, payment holidays, rate-change events, business day conventions
- Phase 3: SHA-256 audit hash per schedule, schedule validation and diff
- Phase 4: FastAPI REST layer, PyPI publication, hosted demo

---

## Installation 

Not yet published to PyPI. Install from source:

```bash
git clone https://github.com/thearun85/amortise.git
cd amortise
poetry install
```

---

## Quick start

```python
from decimal import Decimal
import datetime
from amortise import generate_schedule, LoanRequest, RepaymentType, RateType

loan = LoanRequest(
	principal=Decimal('100000.00'),
	annual_rate=Decimal('0.0525'), # 5.25% - as a decimal fraction, not a percentage
	term_months=12,
	start_date=datetime.date(2026, 3, 1),
	repayment_type=RepaymentType.CAPITAL_AND_INTEREST,
	rate_type=RateType.FIXED,
)

schedule = generate_schedule(loan)

print(f"Monthly payment : {schedule.installments[0].payment}")
print(f"Total interest : {schedule.total_interest}")
print(f"Total payment : {schedule.total_payment}")
print()

for inst in schedule.installments:
	print(
		f"{inst.number:>3} {inst.payment_date} "
		f"interest={inst.interest:>8} "
		f"principal={inst.principal:>8} "
		f"balance={inst.closing_balance:>10}"
	)
```

Output:
 
```
Monthly payment : 8572.21
Total interest  : 2882.15
Total payment   : 102882.15
 
  1  2026-04-01  interest=  445.89  principal= 8126.32  balance=  91873.68
  2  2026-05-01  interest=  396.44  principal= 8175.77  balance=  83697.91
  3  2026-06-01  interest=  373.20  principal= 8199.01  balance=  75498.90
  4  2026-07-01  interest=  325.78  principal= 8246.43  balance=  67252.47
  5  2026-08-01  interest=  299.87  principal= 8272.34  balance=  58980.13
  6  2026-09-01  interest=  262.99  principal= 8309.22  balance=  50670.91
  7  2026-10-01  interest=  218.65  principal= 8353.56  balance=  42317.35
  8  2026-11-01  interest=  188.69  principal= 8383.52  balance=  33933.83
  9  2026-12-01  interest=  146.43  principal= 8425.78  balance=  25508.05
 10  2027-01-01  interest=  113.74  principal= 8458.47  balance=  17049.58
 11  2027-02-01  interest=   76.02  principal= 8496.19  balance=   8553.39
 12  2027-03-01  interest=   34.45  principal= 8553.39  balance=      0.00
```

---
 
## Accessing the calculation trace
 
Every installment carries a `CalcTrace` — the exact values used to derive the interest figure for that row:
 
```python
inst = schedule.installments[0]
trace = inst.calc_trace
 
print(f"Opening balance : {trace.opening_balance}")
print(f"Annual rate     : {trace.annual_rate}")
print(f"Days in period  : {trace.days_in_period}")
print(f"Days in year    : {trace.days_in_year}")
print(f"Interest gross  : {trace.interest_gross}")
print(f"Interest rounded: {trace.interest_rounded}")
print(f"Rounding delta  : {trace.rounding_delta}")
```
 
Output:
 
```
Opening balance : 100000.00
Annual rate     : 0.0525
Days in period  : 31
Days in year    : 365
Interest gross  : 445.8904109589041095890410959
Interest rounded: 445.89
Rounding delta  : -0.0004109589041095890410959
```
 
The formula applied is:
 
```
interest_gross = opening_balance * annual_rate * (days_in_period / days_in_year)
```
 
---
 
## Payment model
 
The payment amount is derived once using the standard annuity formula with `annual_rate / 12` as the periodic rate:
 
```
r       = annual_rate / 12
payment = principal * (r * (1 + r)^n) / ((1 + r)^n - 1)
```
 
Interest per installment is calculated using `actual/365` — actual calendar days between `period_start` and `period_end`. This means interest varies slightly month to month (31-day months accrue more than 30-day months), while the payment amount remains fixed. The final installment absorbs any accumulated rounding residual so the closing balance is always exactly zero.
 
See [ADR-002](docs/adr/ADR-002-payment-model-and-day-count.md) for the full rationale.
 
---
 
## Design principles
 
**`Decimal` throughout** — no floats, ever. IEEE 754 binary floating point cannot represent most decimal fractions exactly. In a 300-row mortgage schedule, float errors compound and produce non-auditable results. All monetary and rate inputs must be supplied as `Decimal`. Floats raise `TypeError` at the boundary. See [ADR-001](docs/adr/ADR-001-decimal-not-float.md).
 
**Calculation trace on every row** — `CalcTrace` is always present on every `Installment`. It is not a debug flag. Every figure on the schedule can be independently reproduced and explained.
 
**Immutable outputs** — `LoanRequest`, `Schedule`, `Installment`, and `CalcTrace` are all frozen dataclasses. No mutation post-construction. `Schedule.installments` is a `tuple`, not a list.
 
**Derived totals as properties** — `Schedule.total_interest` and `Schedule.total_payment` are `@property` — not stored fields. Stored fields could diverge from the installment data.
 
---
 
## Development setup
 
Requires Python 3.12+ and [Poetry](https://python-poetry.org/).
 
```bash
git clone https://github.com/thearun85/amortise.git
cd amortise
poetry install
```
 
---
 
## Running checks
 
```bash
make lint       # ruff check
make fmt        # ruff format
make typecheck  # mypy --strict
make test       # pytest
make all      # all of the above
```
 
---
 
## Architecture Decision Records
 
| ADR | Decision |
|-----|----------|
| [ADR-001](docs/adr/ADR-001-decimal-not-float.md) | Use `Decimal` not `float` for all monetary and rate values |
| [ADR-002](docs/adr/ADR-002-payment-model-day-count.md) | Payment model: annuity formula (`/12`) + `actual/365` interest |
| [ADR-003](docs/adr/ADR-003-payment-timing-arrears-vs-advance.md) | Payment in arrears — disbursement date is not the first payment date |
 
---
 
## Roadmap
 
| Phase | Scope | Status |
|-------|-------|--------|
| 1 | Core engine — fixed/variable rate, capital & interest, interest-only, `actual/365` | Complete |
| 2 | Prepayments, balloon payments, payment holidays, rate-change events, business day conventions | Planned |
| 3 | SHA-256 audit hash, schedule validation and diff | Planned |
| 4 | FastAPI REST layer, PyPI publication, hosted demo | Planned |
 
---
 
## License
 
MIT
