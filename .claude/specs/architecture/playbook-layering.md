---
last_updated: 2026-09-25
semver: 0.2.0
author: Nicholas Bergantz
scope: project
---

# Playbook Layering

## Goal

Define the mandatory layered organization for authoring and deploying playbooks
in this repository. Complexity is pushed **down** the stack, never smeared across
playbooks: playbooks declare *what* is wanted, roles decide *how* to achieve it
for a given host, and global configuration supplies the *data*. This spec governs
where each kind of logic and variable lives, and is authoritative on that
organization. It does not restate Ansible-safety rules in
[`.claude/CLAUDE.md`](../../CLAUDE.md) or the test workflow in
[`docs/testing.md`](../../../docs/testing.md).

## The Three Layers

The repository SHALL be organized into three layers, each with a single
responsibility:

| Layer | Responsibility | Concern |
|---|---|---|
| 3. Playbooks | Declare intent | *What* to do — "install VS Code", "roll ssh keys". OS/arch-agnostic. |
| 2. Roles | Implement intent | *How* to do it for the host's OS × architecture matrix. |
| 1. Global configuration | Supply data | Flags and parameters describing hosts and features. |

A layer SHALL NOT absorb the responsibility of another. Higher layers depend on
lower layers; lower layers SHALL NOT depend on higher layers.

## Layer 1 — Global Configuration & Variables

Global configuration is the flags and parameters that describe hosts and select
features — for example `hostOperatingSystem`, `hostArchitecture`,
`tailscaleEnable`, `vscodeEnable`.

- This repository is a collection artifact and SHALL NOT carry environment
  inventories. Configuration that describes real hosts — per-environment
  `group_vars` and per-host `host_vars` — lives in the **downstream consumer's**
  inventory: the repository that installs this collection and supplies that data.
- A role's `defaults/main.yml` is role-local and lowest-precedence. It SHALL
  carry overridable fallback values so the role is self-contained when installed
  as part of the collection (e.g. `onePasswordVault`, `echo_phrase`), and it is
  the single in-repo source of each role variable's default. It SHALL NOT be the
  authoritative source of cross-host configuration: authoritative per-environment
  values live in the downstream inventory and override the role default.
- For local development and testing this repository keeps one loopback inventory
  at [`tests/inventory/hosts.ini`](../../../tests/inventory/hosts.ini)
  (`localhost ansible_connection=local`). It is the default `INVENTORY` and
  `TEST_INVENTORY` for the Makefile, so `make check/run/ping/syntax-check` run
  locally against the controller with `-e`/`LIMIT` arguments. It is a test
  fixture, not shipped host data.
- Every project variable SHALL be documented in
  [`.schema/ansible-vars.schema.json`](../../../.schema/ansible-vars.schema.json)
  with a description. An undocumented project variable is a defect.
- Variable names SHALL be camelCase.

## Layer 2 — Roles

Roles own all host-specific implementation and are the **only** layer permitted
to branch on operating system or architecture.

- Each role SHALL declare the set of `(operatingSystem × architecture)`
  combinations it supports.
- Dispatch SHALL be driven by the declared `hostOperatingSystem` and
  `hostArchitecture` variables, and those declared values SHALL be validated
  against the host's gathered facts (`ansible_facts.os_family`,
  `ansible_facts.architecture`) before any implementation runs. A mismatch
  between declared and discovered values is an error.
- When a role has no implementation for the host's `(operatingSystem ×
  architecture)`, it SHALL raise a clear, actionable error naming the operation,
  the host, and the unsupported combination.
- That error SHALL be isolated to the operation: it SHALL NOT abort the overall
  run, and other operations against the same host and other hosts SHALL continue.
  (See [Failure Isolation](#failure-isolation).)

## Layer 3 — Playbooks

Playbooks declare intent and nothing more.

- A playbook SHALL be thin: it selects which roles run against which hosts.
- A playbook SHALL be OS/architecture-agnostic. Branching on operating system or
  architecture in a playbook is a defect; that logic belongs in a role.
- A playbook SHALL NOT contain implementation logic that a role should own.
- Playbooks SHALL live directly under `playbooks/` (no category
  subdirectories) and be named in lowercase with `_` word separators. This is
  required for the collection: only playbooks directly under the collection's
  top-level `playbooks/` are addressable downstream by fully-qualified collection
  name (`bergantz_galaxy.home.<name>`, e.g. `bergantz_galaxy.home.echo`).
- A playbook SHALL NOT use `vars_files` with a project-relative path
  (e.g. `../../vars/defaults.yml`): that path does not resolve once the
  collection is installed downstream. Shared values come from the role's
  `defaults/main.yml` and are overridden by the downstream inventory.

## Collection Packaging

This repository is published as the Ansible collection `bergantz_galaxy.home`
(namespace `bergantz_galaxy`, name `home`), defined by
[`galaxy.yml`](../../../galaxy.yml) at the repo root.

- `roles/` and `playbooks/` at the repo root are the collection's roles and
  playbooks; downstream references them as `bergantz_galaxy.home.<role>` and
  `bergantz_galaxy.home.<playbook>`.
- Collection and playbook identifiers are lowercase alphanumeric + `_`, starting
  with a letter — no dashes (why the collection name is `home`, not the git repo
  name `my-galaxy-playbooks`).
- `ansible-galaxy collection build` SHALL succeed; it is the packaging gate.

## Failure Isolation

An operation that cannot be satisfied for a host SHALL fail that operation
without aborting unrelated work.

- The failure SHALL surface where the operation runs, with an actionable message.
- Unrelated operations, subsequent playbooks, and other hosts SHALL proceed.
- The run's exit status SHALL still reflect that a failure occurred, so failures
  are never silently swallowed.

## Compliance Criteria

Conformance is observable:

- No playbook branches on operating system or architecture (no OS/arch `when:`
  conditions in `playbooks/`).
- Every variable defined in `roles/*/defaults` is present in
  `.schema/ansible-vars.schema.json`.
- Every role that supports more than one platform declares its supported
  `(operatingSystem × architecture)` set and validates declared OS/arch against
  gathered facts.
- All variable names are camelCase.
- An operation targeting an unsupported `(operatingSystem × architecture)` errors
  for that operation while the rest of the run completes.
- `make lint` and `make test` pass.

## References

- [`.claude/CLAUDE.md`](../../CLAUDE.md) — repository-wide Critical Rules
  (idempotency, home-directory paths, `become`/`delegate_to` behavior).
- [`docs/testing.md`](../../../docs/testing.md) — the test-first Molecule
  workflow for roles.
- [`.schema/ansible-vars.schema.json`](../../../.schema/ansible-vars.schema.json)
  — the variable documentation schema.
