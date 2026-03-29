PYTHON ?= python3

.PHONY: install lint test run-example

install:
	$(PYTHON) -m pip install -e .[dev]

lint:
	ruff check .
	ruff format --check .

test:
	pytest

run-example:
	saas-footprint-analyzer validate-config --config examples/config.example.yaml
