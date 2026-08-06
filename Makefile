# ============================================================================
#  Ansible automation — developer & CI entrypoints
#  Run `make help` for a summary of available targets.
# ============================================================================

.DEFAULT_GOAL := help
SHELL := /bin/bash

.PHONY: help bootstrap venv \
        lint syntax-check check run ping \
        test test-all test-static test-unit \
        test-molecule test-molecule-example test-molecule-vscode check-docker \
        open-github

# ----------------------------------------------------------------------------
#  Configuration
# ----------------------------------------------------------------------------

# Optional local overrides; see .env.example. CLI overrides (make VAR=...) win.
-include .env

# Operational defaults (used only if not set in .env or on the CLI).
INVENTORY ?= inventories/production/hosts.ini
PLAYBOOK  ?= playbooks/site.yml
LIMIT     ?=
TAGS      ?=

# Static-analysis inputs.
TEST_INVENTORY := inventories/test/hosts.ini
PLAYBOOKS      := $(wildcard playbooks/*.yml) \
                  $(wildcard playbooks/*/update.yml) \
                  $(wildcard playbooks/*/validate.yml)

# Project virtualenv. Everything installs into .venv rather than the ambient
# interpreter: Homebrew's python is PEP 668 "externally managed" and refuses a
# bare `pip install`, and on a fresh machine unversioned `pip` is not on PATH at
# all. Putting .venv/bin first on PATH means every target below keeps calling
# `ansible-lint` / `pytest` / `molecule` unqualified and still gets the venv —
# one definition here instead of a prefix on ten recipes.
PYTHON   ?= python3
VENV     := .venv
VENV_BIN := $(VENV)/bin
export PATH := $(CURDIR)/$(VENV_BIN):$(PATH)

# Install commands.
PIP_INSTALL    := $(VENV_BIN)/pip install --index-url https://pypi.org/simple/ --no-input
GALAXY_INSTALL := $(VENV_BIN)/ansible-galaxy collection install --ignore-certs

# Host OS, used to pick a browser opener.
UNAME_S := $(shell uname -s)

# Share .config/molecule/config.yml across every scenario.
export MOLECULE_GLOBAL_CONFIG := $(CURDIR)/.config/molecule/config.yml

# Docker Desktop on macOS serves its socket under ~/.docker/run/, but the docker
# Python SDK that Molecule uses defaults to /var/run/docker.sock. Point the SDK
# at the Desktop socket when the default is absent (no-op on Linux/CI, and
# skipped entirely if DOCKER_HOST is already set).
ifndef DOCKER_HOST
ifeq ($(wildcard /var/run/docker.sock),)
ifneq ($(wildcard $(HOME)/.docker/run/docker.sock),)
export DOCKER_HOST := unix://$(HOME)/.docker/run/docker.sock
endif
endif
endif

# Assemble ansible-playbook options from the tunables above.
ANSIBLE_PLAYBOOK_OPTS := -i $(INVENTORY)
ifneq ($(LIMIT),)
ANSIBLE_PLAYBOOK_OPTS += --limit $(LIMIT)
endif
ifneq ($(TAGS),)
ANSIBLE_PLAYBOOK_OPTS += --tags $(TAGS)
endif

# ----------------------------------------------------------------------------
#  Help
# ----------------------------------------------------------------------------

help: ## Show this help
	@grep -hE '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| sort \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-28s\033[0m %s\n", $$1, $$2}'

# ----------------------------------------------------------------------------
#  Setup
# ----------------------------------------------------------------------------

venv: $(VENV_BIN)/pip ## Create the project virtualenv (.venv)

# Order-only on the interpreter: create the venv once, then leave it alone.
$(VENV_BIN)/pip:
	@echo "==> Creating virtualenv in $(VENV)..."
	$(PYTHON) -m venv $(VENV)
	$(VENV_BIN)/pip install --upgrade pip

bootstrap: venv ## Install all dev/test dependencies and verify prerequisites
	@echo "==> Installing Ansible + linting tools..."
	$(PIP_INSTALL) "ansible>=9.6" "ansible-lint>=24.5" yamllint "passlib>=1.7"
	@echo ""
	@echo "==> Installing test tools..."
	$(PIP_INSTALL) "pytest>=8.0" "jinja2>=3.1" "pyyaml>=6.0"
	@echo ""
	@echo "==> Installing Molecule + Docker plugin..."
	$(PIP_INSTALL) "molecule>=24.2" "molecule-plugins[docker]>=23.5"
	@echo ""
	@echo "==> Installing Galaxy collections..."
	$(GALAXY_INSTALL) -r requirements.yml
	$(GALAXY_INSTALL) community.docker
	@echo ""
	@echo "==> Verifying prerequisites..."
	@printf "  %-30s" "ansible";      ansible --version | head -1
	@printf "  %-30s" "ansible-lint"; ansible-lint --version | head -1
	@printf "  %-30s" "yamllint";     yamllint --version
	@printf "  %-30s" "molecule";     molecule --version | head -1
	@printf "  %-30s" "pytest";       pytest --version | head -1
	@printf "  %-30s" "docker";       docker version --format 'Docker {{.Client.Version}}' 2>/dev/null \
		|| echo "NOT RUNNING — start Docker Desktop for molecule tests"
	@echo ""
	@echo "Bootstrap complete. Run 'make test' for fast checks or 'make test-all' for the full suite."

# ----------------------------------------------------------------------------
#  Static analysis
# ----------------------------------------------------------------------------

lint: ## Run yamllint and ansible-lint
	yamllint .
	ansible-lint

syntax-check: ## Syntax-check all playbooks against the test inventory
	@failed=0; \
	for pb in $(PLAYBOOKS); do \
		printf "  %-55s" "$$pb"; \
		if ansible-playbook --syntax-check -i $(TEST_INVENTORY) "$$pb" > /dev/null 2>&1; then \
			echo "OK"; \
		else \
			echo "FAIL"; \
			ansible-playbook --syntax-check -i $(TEST_INVENTORY) "$$pb" 2>&1 | tail -5; \
			failed=1; \
		fi; \
	done; \
	[ $$failed -eq 0 ] || (echo "" && echo "Syntax check failed." && exit 1)

# ----------------------------------------------------------------------------
#  Run playbooks
# ----------------------------------------------------------------------------

check: ## Dry-run the playbook (no changes applied)
	ansible-playbook $(ANSIBLE_PLAYBOOK_OPTS) $(PLAYBOOK) --check --diff

run: ## Apply the playbook
	ansible-playbook $(ANSIBLE_PLAYBOOK_OPTS) $(PLAYBOOK)

ping: ## Ping all hosts in the inventory
	ansible -i $(INVENTORY) all -m ansible.builtin.ping

# ----------------------------------------------------------------------------
#  Tests
# ----------------------------------------------------------------------------

test: test-static test-unit ## Fast tests (no Docker) — run before committing

test-all: test test-molecule ## Full test suite including Molecule (requires Docker)

test-static: lint syntax-check ## All static analysis (lint + syntax-check)

test-unit: ## Run pytest template and inventory tests
	pytest tests/ -v

test-molecule: test-molecule-example test-molecule-vscode ## All Molecule tests

test-molecule-example: check-docker ## Molecule test: example role (default scenario)
	cd roles/example && molecule test

test-molecule-vscode: check-docker ## Molecule test: vscode role (default scenario, Ubuntu/apt path only)
	cd roles/vscode && molecule test

check-docker:
	@docker info > /dev/null 2>&1 \
		|| (echo "ERROR: Docker daemon is not running. Start Docker Desktop and retry." && exit 1)

# ----------------------------------------------------------------------------
#  Utilities
# ----------------------------------------------------------------------------

open-github: ## Open the GitHub repository in the default browser (macOS/Linux)
	@remote=$$(git remote | head -1); \
	[ -n "$$remote" ] || { echo "No git remote configured."; exit 1; }; \
	url=$$(git remote get-url "$$remote" | sed -e 's|git@github.com:|https://github.com/|' -e 's|\.git$$||'); \
	echo "Opening $$url"; \
	if [ "$(UNAME_S)" = "Darwin" ]; then open "$$url"; \
	elif command -v xdg-open >/dev/null 2>&1; then xdg-open "$$url"; \
	else echo "No browser opener found; visit: $$url"; fi
