# ADR-001: Use `Decimal` instead of `float` for all monetary values

**Status:** Accepted
**Date:** 2026-03-24
**Deciders:** Arun Raghunath

---

## Context

Python's native `float` uses IEEE 754 binary floating-point representation. Binary floats cannot represent most decimal fractions exactly - `0.1 + 0.2 != 0.3` is the canonical example. In a loan repayment schedule with 300 row, each row's principal and interest figures are derived from the previous row's outstanding balance. Float rounding errors compound across rows, producing results that:

- Differ between runs on different hardware
- Cannot be reproduced exactly from inputs alone
- Cannot be audited or explained to a regulator

This is not a theoretical comcern. UK FCA rules require that lenders can reproduce and explain every figure on a statement. A schedule that drifts by £0.01 across 25 years due to float error cannot be defended.

---

## Decision

All monetary values in `amortise` use `decimal.Decimal`. Conversion from external inputs (strings, ints) happens at the boundary - the moment a value enters the system. `Decimal` precision is set to `prec-28`. All rounding uses `ROUND_HALF_UP`, consistent with the UK retail banking convention.

Float values are never accepted internally. Any boundary function that receives a `float` will raise a `TypeError`.

---

## Rationale

### Alternatives considered

**`float` throughout**
Rejected. Produces non-reproducible, non-auditable results. Unsuitable for regulated financial outputs.

**`int` with pence (fixed-point)**
Viable for simple interest calculations but breaks down when intermediate values require sub-penny precision (e.g. daily interest accrual on a £250,000 balance). Rejected as insufficient for the intended feature scope.

**Third-party library (`mpmath`, `fpdf2`)**
Unnecessary. `decimal.Decimal` is in the Python standard library, has stable behaviour, and is the established choice in the UK fintech. Adding a dependency for a solved problem is unjustified.

---

## Consequences

### Positive
- All figures are reproducible from the same inputs, regardless of platform.
- Rounding behaviour is explicit abd auditable (`ROUND_HALF_UP` stated in code)
- No external dependency required

### Negative / trade-offs
- `Decimal` arithmetic is slower than `float` - irrelevant at schedule-generation scale (hundreds of rows, not millions)
- Developers must convert intuputs to `Decimal` explicitly; silent float acceptance is intentionally prohibited

### Neutral
- All output dataclasses store `Decimal` fields; serialisation to JSON requires explicit conversion.

---

## References

- [Python `decimal` module documentation](https://docs.python.org/3/library/decimal.html)
- [IEEE 754 Wikipedia](https://en.wikipedia.org/wiki/IEEE_754)
- FCA MCOB 10A - Mortgage illustration and illustration rules (reproducibility requirement)
