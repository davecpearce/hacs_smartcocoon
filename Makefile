.PHONY: help install test lint format ci-local ci-summary update-hooks

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies
	pip install -r requirements_test.txt
	pip install -e .

test: ## Run tests
	python -m pytest tests/ --cov=custom_components.smartcocoon --cov-report=term-missing -v

lint: ## Run pre-commit hooks
	pre-commit run --all-files

format: ## Format code with Black (safe mode)
	python -m black --safe custom_components/ tests/

ci-local: ## Run full CI locally
	./scripts/run-ci-local.sh

ci-summary: ## Run CI with summary output
	./scripts/run-ci-summary.sh

update-hooks: ## Update pre-commit hooks to latest versions
	./scripts/update-precommit.sh
