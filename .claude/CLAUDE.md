# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Ansible automation repo for provisioning dev and production machines: playbooks,
first-party roles, per-environment inventories, Molecule role tests, and CI
(lint + molecule via GitHub Actions).

## Commands

```bash
make bootstrap   # install ansible/lint/test/molecule deps + Galaxy collections
make lint        # yamllint + ansible-lint
make syntax-check # syntax-check every playbook against the test inventory
make check       # dry-run PLAYBOOK against INVENTORY (--check --diff)
make run         # apply PLAYBOOK to INVENTORY
make ping        # ansible.builtin.ping against every host in INVENTORY
make test        # fast: test-static (lint+syntax-check) + test-unit (pytest) — no Docker
make test-all    # test + test-molecule (all roles, requires Docker)
make test-molecule-<role>  # molecule test for a single role, e.g. test-molecule-vscode
make open-github # open the repo's GitHub remote in the browser
```

`INVENTORY`, `PLAYBOOK`, `LIMIT`, `TAGS` are overridable on the CLI
(`make run LIMIT=local PLAYBOOK=playbooks/vscode.yml`) or via a git-ignored
`.env` (copy from `.env.example`); CLI wins over `.env` wins over the Makefile
defaults (`inventories/production/hosts.ini`, `playbooks/site.yml`).

### Running a single Molecule scenario

```bash
cd roles/<role>
molecule converge -s default   # apply the role, keep the instance running
molecule verify   -s default   # re-run verify.yml assertions only
molecule login    -s default   # shell into the test instance
molecule destroy  -s default   # tear it down
```

`MOLECULE_GLOBAL_CONFIG` (shared driver/verifier config in
`.config/molecule/config.yml`) is exported automatically by the Makefile; when
running `molecule` directly, `export MOLECULE_GLOBAL_CONFIG=$PWD/.config/molecule/config.yml`
first. Full details, including how to add a new scenario, are in
[docs/testing.md](../docs/testing.md).

### Running a single pytest test

```bash
pytest tests/test_inventory.py::test_inventory_parses -v
```

## Architecture

- `playbooks/` — thin entry points (`site.yml`, `vscode.yml`, `ping.yml`). All
  logic lives in roles; playbooks just select which roles run against which
  hosts.
- `roles/<name>/{defaults,tasks,handlers,meta}` — first-party roles. Roles that
  branch on OS split tasks per-family (see `roles/vscode/tasks/{main,Darwin,Debian}.yml`,
  dispatched from `main.yml` on `ansible_facts.os_family`).
  `roles/<name>/molecule/<scenario>/` holds that role's Molecule test scenario
  (`prepare.yml` → `converge.yml` → `verify.yml`); see
  [docs/testing.md](../docs/testing.md) for the full test-first workflow.
- `galaxy_roles/` — Galaxy-installed roles/collections, git-ignored, populated
  by `make bootstrap` from `requirements.yml`.
- `inventories/{production,staging,test}/` — one inventory per environment,
  each with its own `hosts.ini` + `group_vars/` (and `host_vars/` where
  needed). Variable precedence is role `defaults/` < inventory `group_vars/all.yml`
  < `group_vars/<group>.yml` < `host_vars/`. `production/group_vars/local.yml`
  applies only to the `[local]` loopback group in `hosts.ini`
  (`ansible_connection=local`), not to real hosts like `host-01`.
- `files/`, `templates/` — static files and Jinja2 templates referenced by role
  tasks.
- CI (`.github/workflows/lint.yml`, `molecule.yml`) runs `make bootstrap` then
  `make test` / `make test-molecule-<role>` per role — the same targets used
  locally, so a green `make test-all` locally should stay green in CI. Adding a
  Molecule scenario requires adding its target to both the Makefile matrix and
  the `molecule.yml` workflow matrix (see [docs/testing.md](../docs/testing.md)).

## Critical Rules

### Ansible hosts are long-lived production systems

Every task that runs modifies real system state that persists across all
subsequent runs. There is no kill-and-restart. A bad change compounds through
every future playbook run. Never experiment with module parameters or patterns
— verify first. Before suggesting any change, think through what happens if it
fails mid-run on a live host.

### Home directory paths

Use `{{ login_user_home }}` for user home paths. This fact is captured once in
`prefetch_credentials.yml` with `become: false` so it resolves to the login
user's home on any OS (macOS `/Users/…`, Linux `/home/…`).

Do **not** use `{{ ansible_user_dir }}` or `{{ ansible_env.HOME }}` directly —
when `ansible_become: true` is active (set in group_vars), both resolve to
`/root/`. Do **not** hardcode `/home/{{ ansible_user }}`.


### delegate_to: localhost and become

When a task uses `delegate_to: localhost`, the host-level `ansible_become: true` (from group_vars) overrides task-level `become: false`. Always add `vars: ansible_become: false` alongside `become: false` on delegated tasks.
