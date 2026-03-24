# amortise

> Loan repayment schedule generation and validation in Python.

`amortise is an open-source Python library for generating and validating loan repayment schedules. It is built for correctness, auditability, and explainability - every output row carries a full calculation trace, and every schedule carries a SHA-256 tamper-detection hash.`

---

## Status

`v0.1.0-alpha` - Phase 1 (core-engine) in progress. Not yet published to PyPI.

--- 

## Design Principles

- **`Decimal` throughout** - no floats, ever. IEEE 754 errors are unacceptable in financial outputs.
- **Calculation trace on every row** - `CalcTrace` records the exact formula, values, and rounding applied per installment. Always present, not a debug flag.
- **Immutable outputs** - all output dataclasses are frozen. No mutation post-generation.
- **Audit hash** - SHA-256 fingerprint of the complete schedule. Any downstream change invalidates it.

---

## Installation (once published)

```bash
pip install amortise
```

## Development setup

Requires Python 3.12+ and [Poetry](https://python-poetry.org/).

```bash
git clone https://github.com/thearun85/amortise.git
cd amortise
poetry install
```

## Run checks

```bash
# Lint 
make lint

# Format
make fmt

# Type check
make typecheck

# Tests
make test
```

## Architecture Decision Records

Design decisions are documented in ['docs/adr/'](docs/adr/).

| ADR | Decision |
|-----|----------|
| [ADR-001](docs/adr/ADR-001-decimal-not-float.md) | Use `Decimal` instead of `float` for all monetary values |

---

## Roadmap

| Phase | Scope |
|-------|-------|
| 1 | Core Engine - fixed/variable rate, monthly, principal & interest, interest-only |
| 2 | Prepayments, ballon payments, payment holidays, rate-change events |
| 3 | SHA-256 audit hash, schedule validation and diff |
| 4 | API layer, PyPI publication, hosted demo |

---

## License

MIT
