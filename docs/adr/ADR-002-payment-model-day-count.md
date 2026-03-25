# ADR-002: Payment model and day count convention

**Status:** Accepted
**Date:** 2026-03-25
**Deciders:** Arun Raghunath

---

## Context

Generating a loan repayment schedule requires two distinct calculations:

1. **The periodic payment amount** - how much the borrower pays each period.
2. **The interest component of each payment** - how much of that payment is interest vs principal reduction.

These two calculations do not have to use the same convention. In practice, many commercial lending systems derive the payment using a simplified convention for stability, and compute actual interest using a more precide day count convention for accuracy and auditability.

There are two common approaches for each:

**Payment derivation:**
- `annual_rate / 12` - divides the annual_rate into equal monthly slices. Produces a stable, fixed payment regardless of how many days are in each calendar month.
- `actual/365` - uses the actual number of days in each period. Payment varies month to month depending on calendar. Uncommon for standard loan products.

**Interest calculation:**
- `annual_rate / 12` - same simplified convention. Used by most UK high-street residential mortgage lenders. Simple, predictable, no date dependency.
- `actual/365` - counts actual calendar days between period start and period end, divides by 365. More precise. Standard in commercial lending, bridging finance, development finance, and core banking systems.

The two can be combined: derive a fixed payment using `annual_rate / 12`, then compute actual interest using `actual/365`. The difference between interest abd payment goes to principal reduction each period. The final installment absorbs any residual so the closing balance lands exactly at zero.

---

## Decision

The `amortise` engine uses the following payment model in Phase 1:

- **Payment amount** is derived using the standard annuity formula with `annual_rate / 12` as the periodic rate. This produces a fixed payment for all installment except the last.
- **Interest per installment** is calculated using the `actual/365` day count convention via `calculate_interest()`. The actual number of calendar days between `period_start` and `period_end` determines the interest for that row.
- **Principal per installment**= `payment - interest_rounded`.
- **Final installment** - payment is adjusted so that `closing_balance` is exactly zero, absorbing any accumulated rounding residual.

The annuity formula used for payment derivation:

```
r = annual_rate / 12
payment = principal * (r * (1 + r)^n) / ((1 + r)^n - 1)
```

Where `n = term_months` and all arithmetic is performed in `Decimal` with `ROUND_HALF_UP`.

For interest-only loans, no payment amount is derived upfront. Interest is calculated per perriod via `actual/365`. The principal component is zero for all installments except the last, which carries a balloon payment equal to the full outstanding principal plus that period's interest.

---

## Rationale

**Why `actual/365` for interest?**

The target audience for this library is fintech developers, challenger banks, system integrators - not consumers comparing high-street mortgage products. The `actual/365` convention is standard in commercial and institutional lending and in core banking systems. It is more precise, fuly auditable (every row records exact dates and day counts in `CalcTrace`), and more defensible under regulatory scrutiny.

Pure `annual_rate / 12` interest calculation was rejected because it obscures the day count dependency, produces identical interest figures regardless of period length, and is unsuitable for commercial loan structures where periods may not be uniform (drawdown mid-month, payment holidays, etc.).

**Why `annual_rate / 12` for payment derivation?**

The annuity formula requires a periodic rate. Using `actual/365` for payment derivation would require a different payment amount each month - as day counts vary - which is not how loan products are structured or communicated to borrowers. A fixed payment is the market norm.

**Why not pure `actual/365` throughout?**

Some lenders apply `actual/365` to both payment derivation and interest calculation, accepting variable monthly payments. This is uncommon in retail lending and complicates product design and borrower communication. It is out of scope for Phase 1.

**Why not pure `annual_rate / 12` throughout?**

Accepted for Phase 2 extension (see below). Excluded from Phase 1 because `actual/ 365` interest is the more technically interesting and differentiated choice, and the one most relevant to the library's target audience.

---

## Consequences

### Positive
- Interest figures are fully auditable - `CalcTrace` records exact dates, day counts, gross and rounded values per row.
- The model is realistic for commercial and institutional lending contexts.
- A fixed payment amount is stable and predictable for borrowers.
- The final installment adjustment ensures closing balance is always exactly zero regardless of accumulated rounding.

### Negative / trade-offs
- The payment model uses two different conventions (`/12` for payment, `actual/365` for interest). This is accurate and standard in institutional lending but requires explanation - it will surprise developers expecting a single convention througout.
- Interest figures will vary slightly row to row due to differing day counts (e.g. February vs March), even though the payment amount is fixed. This is correct behaviour but must be clearly documented.

### Neutral
- The final installment may differ from all preceding installments due to rounding residual absorption. This is expected and recored in `CalcTrace`.

---

## Extension points

**`annual_rate / 12` interest convention** - adding a `monthly_twelfths` option tp `DayCountConvention` and branching in `calculate_interest` is straightforward. Planned for Phase 2. This would make the library suitable for modelling standard UK high-street residential mortgage schedules.

**Payment in advance (annuity due)** - see ADR-003. Out of Phase 1 scope.

**Variable payment amounts** - required for variable rate loans where the rate changes mid-term. The payment is recalculated at each rate change event using the remaining balance and remaining term. Planned for Phase 2.

---

## References

- ADR-001 - Decimal not float
- ADR-003 - Payment timing: arrears vs advance
- ICMA Actual/Actual day count convention (for reference contrast)
