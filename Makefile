.DEFAULT_GOAL := help

.PHONY: help install lint format typecheck test pre-commit all build clean

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install all dependencies and pre-commit hooks
	uv sync
	uv run pre-commit install --hook-type pre-commit --hook-type commit-msg

lint: ## Run ruff linter
	uv run ruff check src tests docs/examples

format: ## Format and auto-fix with ruff
	uv run ruff format src tests docs/examples
	uv run ruff check --fix src tests docs/examples

typecheck: ## Run pyright type checker
	uv run pyright

test: ## Run tests with coverage
	uv run pytest

test-no-cov: ## Run tests without coverage
	uv run pytest --no-cov

pre-commit: ## Run all pre-commit hooks against all files
	uv run pre-commit run --all-files

all: check pre-commit ## Run all validations (lint, typecheck, tests, pre-commit hooks)

clean: ## Remove build artifacts and caches
	rm -rf dist .coverage .pytest_cache .ruff_cache
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +

check: lint typecheck test ## Run lint, typecheck, and tests
