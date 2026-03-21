# ==============================
# Config
# ==============================

RUN_CMD ?= uv run
PYTHON := $(RUN_CMD) python
PYTEST := $(RUN_CMD) coverage run --parallel-mode -m pytest
ALEMBIC := $(RUN_CMD) alembic

ENV_FILE ?= .env
COMPOSE_FILE ?= docker-compose.yml
DC := docker compose --env-file $(ENV_FILE) -f $(COMPOSE_FILE)

# ==============================
# Colors
# ==============================

BLUE := \033[0;34m
NC := \033[0m

# ==============================
# Logging (minimal)
# ==============================

define log_step
	@echo "\n$(BLUE)==> $(1)$(NC)"
endef

# ==============================
# Docker
# ==============================

up:
	$(call log_step,🐳 Docker Up)
	@$(DC) up -d

down:
	$(call log_step,🧼 Docker Down)
	@$(DC) down -v

logs:
	$(call log_step,📜 Docker Logs)
	@$(DC) logs -f

# ==============================
# DB
# ==============================

migrate:
	$(call log_step,🛠️ Migration)
	@$(ALEMBIC) upgrade head

# ==============================
# Tests
# ==============================

unit-tests:
	$(call log_step,🧪 Unit Tests)
	@$(PYTEST) tests/unit

integration-tests:
	$(call log_step,🔗 Integration Tests)
	@$(PYTEST) tests/integration

e2e-tests:
	$(call log_step,🌐 E2E Tests)
	@$(PYTEST) tests/e2e

# ==============================
# Coverage
# ==============================

coverage:
	$(call log_step,📊 Coverage)
	@$(RUN_CMD) coverage combine
	@$(RUN_CMD) coverage report
	@$(RUN_CMD) coverage html

# ==============================
# App
# ==============================

run:
	$(call log_step,🚀 Application)
	@$(PYTHON) -m app.main

# ==============================
# Setup
# ==============================

wait-db:
	$(call log_step,⏳ Waiting for DB)
	@until pg_isready -h localhost -p 5432; do sleep 1; done

setup-local: up wait-db migrate

# ==============================
# Lint
# ==============================

lint:
	$(call log_step,🧹 Lint)
	@$(RUN_CMD) ruff check --fix .
	@$(RUN_CMD) ruff format --check .
	@$(RUN_CMD) ty check .

format:
	$(call log_step,✨ Format)
	@$(RUN_CMD) ruff check --fix .
	@$(RUN_CMD) ruff format .

# ==============================
# Cleanup
# ==============================

clean:
	$(call log_step,🧼 Cleanup)
	@find . -type f -name "*.pyc" -delete
	@find . -type d -name "__pycache__" -delete
	@rm -rf .pytest_cache .coverage coverage.xml htmlcov

# ==============================
# Help
# ==============================

help:
	@echo "\n$(BLUE)Available commands:$(NC)"
	@echo "  make up              	- 🐳 Start docker"
	@echo "  make down            	- 🧼 Stop docker"
	@echo "  make logs            	- 📜 Logs"
	@echo ""
	@echo "  make migrate         	- 🛠️ Migrations"
	@echo "  make setup-local       - 🚀 Setup (up + migrate)"
	@echo ""
	@echo "  make unit-tests      	- 🧪 Unit"
	@echo "  make integration-tests - 🔗 Integration"
	@echo "  make e2e-tests       	- 🌐 E2E"
	@echo ""
	@echo "  make lint            	- 🧹 Lint"
	@echo "  make format          	- ✨ Format"
	@echo ""
	@echo "  make coverage        	- 📊 Coverage"
	@echo "  make clean           	- 🧼 Cleanup"
