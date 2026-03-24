.PHONY: lint fmt typecheck test all clean

lint:
	poetry run ruff check amortise tests

fmt:
	poetry run ruff format amortise tests
	poetry run ruff check --fix amortise tests

typecheck:
	poetry run mypy amortise tests

test:
	poetry run pytest -v -s

all: fmt lint typecheck test

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name .mypy_cache -exec rm -rf {} +
	find . -type d -name .pytest_cache -exec rm -rf {} +
