---
last_updated: 2026-10-08
semver: 0.0.1
author: Nicholas Bergantz
document_type: readme
---

# CLAUDE.md

This file tells Claude Code (claude.ai/code) how to work with the code in this
repository.

## Overview

This is an Ansible repository that sets up dev and production machines. It
contains the playbooks, the first-party roles, the Molecule role tests, and the
CI (lint and Molecule through GitHub Actions).

## Specs

- [Playbook Layering](specs/architecture/playbook-layering.md) — the mandatory
  three-layer structure for playbooks: the playbooks declare what to do → the
  roles do the work for each OS and arch → the global config gives the data.
- [Playbook Documentation](specs/architecture/playbook-documentation.md) — each
  toolset must have a `docs/playbooks/<toolset>.md` file and a `readme.md`
  pointer. Change them in the same change that changes the toolset.
- [Application Installer Roles](specs/architecture/application-installer-roles.md) —
  the minimum template for an application installer: `install`/`uninstall`/
  `diagnose` operations, per-OS tasks, the firewall through the `firewall` role,
  small playbooks, schema, docs, and Molecule tests.

## Commands

```bash
make bootstrap   # install ansible/lint/test/molecule deps + Galaxy collections
make lint        # yamllint + ansible-lint
make syntax-check # syntax-check every playbook against the test inventory
make check       # dry-run PLAYBOOK against INVENTORY (--check --diff)
make ping        # ansible.builtin.ping against every host in INVENTORY
make test        # fast: test-static (lint+syntax-check) + test-unit (pytest) — no Docker
make test-all    # test + test-molecule (all roles, requires Docker)
make test-molecule-<role>  # molecule test for a single role, e.g. test-molecule-vscode
make open-github # open the repo's GitHub remote in the browser
```

You can override `INVENTORY`, `PLAYBOOK`, `LIMIT`, and `TAGS` on the CLI
(`make check LIMIT=local PLAYBOOK=playbooks/vscode.yml`), or in a git-ignored
`.env` file (copy it from `.env.example`). The CLI wins over `.env`, and `.env`
wins over the Makefile defaults (`tests/inventory/hosts.ini`,
`playbooks/ping.yml`).

### Running a single Molecule scenario

```bash
cd roles/<role>
molecule converge -s default   # apply the role, keep the instance running
molecule verify   -s default   # re-run verify.yml assertions only
molecule login    -s default   # shell into the test instance
molecule destroy  -s default   # tear it down
```

The Makefile exports `MOLECULE_GLOBAL_CONFIG` for you (the driver and verifier
config in `.config/molecule/config.yml`). When you run `molecule` directly, do
this `export` first: `export MOLECULE_GLOBAL_CONFIG=$PWD/.config/molecule/config.yml`.
[docs/testing.md](../docs/testing.md) gives the full details and shows how to
add a new scenario.

### Running a single pytest test

```bash
pytest tests/test_tailscale.py::test_tailscale_status_prints_diagnostics -v
```

## Architecture

- `playbooks/` — the small entry points (`ping.yml`, `vscode.yml`, per-toolset
  install/uninstall). The roles contain all the tasks. The playbooks only select
  which roles operate on which hosts.
- `roles/<name>/{defaults,tasks,handlers,meta}` — the first-party roles. A role
  that changes with the OS divides its tasks per family (see
  `roles/vscode/tasks/{main,Darwin,Debian}.yml`; `main.yml` sends to them on
  `ansible_facts.os_family`). `roles/<name>/molecule/<scenario>/` holds that
  role's Molecule test scenario (`prepare.yml` → `converge.yml` → `verify.yml`).
  [docs/testing.md](../docs/testing.md) gives the full test-first workflow.
- `galaxy_roles/` — the Galaxy-installed roles and collections. They are
  git-ignored. `make bootstrap` fills them from `requirements.yml`.
- This repository is the `bergantz_galaxy.home` collection. It ships **no**
  environment inventory. The host data (the per-environment `group_vars` and the
  per-host `host_vars`) is in the consumer repository that installs the
  collection. The role `defaults/` are the lowest-precedence default values that
  the consumer inventory overrides. `tests/inventory/hosts.ini` is the only
  inventory here: one `localhost` loopback for local dev and test
  (`make check/run/ping/syntax-check`). It is not shipped host data.
- The CI (`.github/workflows/lint.yml`, `molecule.yml`) does `make bootstrap`,
  then `make test` and `make test-molecule-<role>` for each role. These are the
  same targets that you use locally, so a green `make test-all` locally stays
  green in CI. To add a Molecule scenario, add its target to both the Makefile
  matrix and the `molecule.yml` workflow matrix (see
  [docs/testing.md](../docs/testing.md)).

## Critical Rules

### Check against the Ansible documentation — do not assume

Ground each decision about Ansible use in the official Ansible documentation
(https://docs.ansible.com/ansible/latest/) for the version that this repository
uses. This includes module names, parameters and their default values, return
values, how a plugin operates, variable precedence, idempotency, and the
`become` and `delegate_to` semantics. Do not use your memory or an adjacent task
as the source. Do not use what you only think is correct. When the documentation
does not show what occurs, or it is not clear, tell the user. Make sure of the
correct behavior before you continue. Do not fill the clearance yourself. For a
decision that is not clear, give the module or the Ansible documentation page
for it.

### Ansible hosts stay live for a long time

Each task that operates changes the system state. That change continues through
all future runs. There is no kill-and-restart. A bad change stays in all future
playbook runs. Do not do test changes to module parameters to find what occurs;
check the documentation first. Before you give a change, think about what occurs
if the task stops in the middle of a run on a live host.

### Home directory paths

Use `{{ login_user_home }}` for user home paths. `prefetch_credentials.yml`
sets this fact one time with `become: false`, so it gives the login user's home
on each OS (macOS `/Users/…`, Linux `/home/…`).

Do **not** use `{{ ansible_user_dir }}` or `{{ ansible_env.HOME }}` directly.
When `ansible_become: true` is active (set in group_vars), both give `/root/`.
Do **not** hardcode `/home/{{ ansible_user }}`.


### delegate_to: localhost and become

When a task uses `delegate_to: localhost`, the host-level `ansible_become: true`
(from group_vars) overrides the task-level `become: false`. Always add
`vars: ansible_become: false` with `become: false` on a delegated task.
