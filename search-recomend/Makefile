.PHONY: help setup test coverage clean run

help:
	@echo "Available targets:"
	@echo "  setup     - Install dependencies and download LAYA model"
	@echo "  test      - Run test suite with coverage"
	@echo "  coverage  - Show detailed coverage report"
	@echo "  clean     - Remove venv, cache, and build artifacts"
	@echo "  run       - Start the application"

setup:
	python scripts/setup.py

test:
	python -m pytest tests/ -v

coverage:
	python -m pytest tests/ --cov=app --cov-report=term-missing

clean:
	rm -rf .venv
	rm -rf __pycache__
	rm -rf .pytest_cache
	rm -rf data-runtime/cache
	rm -rf .coverage
	rm -rf htmlcov

run:
	./run.sh || python run.py
