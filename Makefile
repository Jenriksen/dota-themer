# Dota Themer - Makefile for Development
# Provides common commands for development and testing

.PHONY: help test test-verbose test-core test-bot test-logging run run-cli clean install

# Default target
help:
	@echo "Dota Themer - Available Commands"
	@echo "================================="
	@echo ""
	@echo "Development:"
	@echo "  make install    - Install dependencies"
	@echo "  make run        - Run the Discord bot"
	@echo "  make run-cli    - Run the CLI theme suggester"
	@echo ""
	@echo "Testing:"
	@echo "  make test           - Run all tests"
	@echo "  make test-verbose  - Run all tests with verbose output"
	@echo "  make test-core      - Run core tests only"
	@echo "  make test-bot       - Run bot tests only"
	@echo "  make test-logging   - Run logging tests only"
	@echo ""
	@echo "Maintenance:"
	@echo "  make clean     - Clean build artifacts"
	@echo "  make help      - Show this help message"

# Install dependencies
install:
	pip install -r requirements.txt

# Run the Discord bot
run:
	python bot.py

# Run the CLI
run-cli:
	python core.py 2

# Run tests
test:
	python -m unittest discover

test-verbose:
	python -m unittest discover -v

test-core:
	python -m unittest test_core -v

test-bot:
	python -m unittest test_bot -v

test-logging:
	python -m unittest test_logging -v

# Clean
clean:
	rm -rf __pycache__
	rm -rf *.pyc
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
