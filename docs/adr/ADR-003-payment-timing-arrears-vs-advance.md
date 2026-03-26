# ADR-003: Payment timing - arrears vs advance

**Status:** Accepted
**Date:** 2026-03-26
**Deciders:** Arun Raghunath

---

## Context

A loan repayment schedule must define when the first payment is due relative to the loan start date (disbursement date). There are two standard models.

**Payment in arrears (ordinary annuity)**
The first payment falls one full period after the disbursement date. For a monthly loan starting March 1, the first payment is due April 1. This is the standard model for retail mortgages, personal loans, and most commercial term loans.

**Payment in advance (annuity due)**
The first payment falls on the disbursement date itself. For a loan starting March 1, the first payment is due March 1. This model is common in leasing and asset finance, where the lessor requires an upfront payment before releasing the asset.

The two models produce different schedules and different total interest figures for the same principal, rate and term. The annuity formula also differs:

```
# Payment un arrears (ordinary annuity)
payment = principal * (r * (1 + r)^n) / ((1 + r)^n - 1)

# Payment in advance (annuity due)
payment = principal * (r * (1 + r)^n) / ((1 + r)^n - 1) * (1 / (1 + r))
```

The `LoanRequest` model currently holds a `start_date` field, defined as the loan disbursement date. The mapping of `start_date` to `period_start` and `payment_date` depends on which model is in use.

---

## Decision

Phase 1 implements **payment in arrears** only.

- `start_date` is the loan disbursement date - the first day of the first interest period.
- `period_start` of installment 1 = `start_date`
- `period_end` of installment 1 = `start_date` + 1 month - this is also the first `payment_date`.
- Each subsequent installment's `period_start` = previous installment's `period_end`.

For a loan with `start_date = 2026-03-01` and `term_months = 12`:

| # | period_start | period_end / payment_date |
|---|---|---|
| 1 | 2026-03-01 | 2026-04-01 |
| 2 | 2026-04-01 | 2026-05-01 |
|...|...|...|
| 12| 2027-02-01 | 2027-03-01 |

---

## Rationale

Payment in arrears is the dominant model for the loan products this library targets in Phase 1 - retail mortgages, personal loans, and commercial term loans. It is the assumed default in most lending contexts unless explicitly stated otherwise.

Payment in advance is specific to leasing and asset finance, which are explicitly out of scope for Phase 1.

---

## Consequences

### Positive
- Schedule generation logic is straightforward - period dates advance linearly from `start_date` with no conditional branching on payment timing.
- `payment_date` on each installment is unambigous - it is always `period_end`.
- The annuity formula has one form only.

### Negative / trade-offs
- Leasing and asset finance schedules cannot be modelled until payment in advance is implemented.

### Neutral
- `start_date` on `LoanRequest` is the disbursement date in both models. - the field name and semantics do not need to change when payment in advance is added.

## Extension points

**payment in advance** - adding a `PaymentTiming` `StrEnum` to `LoanRequest` with values `ARREARS` and `ADVANCE`, then branching in `generate_schedule()` on that field, is the intended extension path. The annuity formula adjustment is a one-line multiplicative factor. Planned for Phase 2 alongside leasing structures.

---

## References

- ADR-002 - Payment model and day count convention
