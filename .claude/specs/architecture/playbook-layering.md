---
last_updated: 2026-10-03
semver: 0.5.0
author: Nicholas Bergantz
document_type: specification
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

Global configuration is the flags and parameters that identify hosts and select
features — for example `hostName`, `useVpn`, and `vscodeExtensions`.

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
  locally against the super agent with `-e`/`LIMIT` arguments. It is a test
  fixture, not shipped host data.
- Every project variable SHALL be documented in the variable schema
  (see [Variable Schema Organization](#variable-schema-organization)) with a
  description. An undocumented project variable is a defect.
- Variable names SHALL be flat and camelCase. Variables that belong to a group
  SHALL be named `<group><parameter>` (e.g. `vpnDomain`, `hostName`,
  `onePasswordVault`). Grouping is expressed by the name
  prefix and by file organization, never by nesting variables into a dict.

### Variable Schema Organization

The variable schema provides hover documentation for `host_vars`, `group_vars`,
and role defaults. It is wired to the editor in
[`.vscode/settings.json`](../../../.vscode/settings.json), so the root file
SHALL remain at
[`.schema/ansible-vars.schema.json`](../../../.schema/ansible-vars.schema.json).

- **Variables stay flat.** A variable SHALL be a top-level scalar/array key, not
  a nested dict. Depth is organizational (files and directories), not structural
  (nested objects). This preserves per-key override under Ansible's default
  `hash_behaviour: replace`, where defining a parent dict at a higher-precedence
  layer replaces the whole dict rather than merging keys — which would silently
  drop the role-default fallbacks a downstream inventory did not restate.
- **One file per group.** Each group's variables SHALL be defined in a companion
  file [`.schema/groups/<group>-schema.json`](../../../.schema/groups), where
  `<group>` is the lowercase group token: `host`, `vscode`, `tailscale`,
  `samba`, `onepassword`. The group token in the filename is lowercase; the
  matching variable-name prefix is camelCase (file `onepassword-schema.json` ↔
  prefix `onePassword`).
- **Define once, reference in `properties`.** Within a group file each variable
  SHALL be defined exactly once under `$defs` and exposed through `properties`
  by a local `$ref` (`#/$defs/<variableName>`).
- **Compose in the root.** The root schema SHALL pull in every group file via
  `allOf` `$ref` to `groups/<group>-schema.json`. Group files and the root
  SHALL set `additionalProperties: true` so the `allOf` composition validates
  each variable where it is defined and permits the rest.
- **Ungrouped variables live in the root.** Standalone variables that carry no
  group prefix (`echo_phrase`, `env`) SHALL be defined directly in the root
  schema's `$defs`/`properties`, not in a group file.
- **Adding a group.** Create `.schema/groups/<group>-schema.json` following the
  pattern above and add one `allOf` `$ref` to it in the root schema.

## Layer 2 — Roles

Roles own all host-specific implementation and are the **only** layer permitted
to branch on operating system or architecture.

- Each role SHALL declare the set of `(operatingSystem × architecture)`
  combinations it supports.
- Dispatch SHALL use `ansible_facts.os_family` and
  `ansible_facts.architecture` directly. Roles SHALL gather the required facts
  after credentials and the SSH route are resolved; they SHALL NOT introduce
  inventory declarations, normalized aliases, or role-local copies of platform
  facts.
- When a role has no implementation for the host's `(operatingSystem ×
  architecture)`, it SHALL raise a clear, actionable error naming the operation,
  the host, and the unsupported combination.
- That error SHALL be isolated to the operation: it SHALL NOT abort the overall
  run, and other operations against the same host and other hosts SHALL continue.
  (See [Failure Isolation](#failure-isolation).)

### Sequential operation routing

When one role invocation can compose multiple ordered sub-operations, the role
SHALL use list-based task dispatch:

- Each operation SHALL live in `roles/<role>/tasks/<operation>.yml` and contain
  the implementation for that operation.
- The requested operations SHALL be a flat, plural, camelCase list named
  `<role>Operations`. List order is execution order and is part of the role's
  public interface.
- `roles/<role>/tasks/main.yml` SHALL perform only shared setup, validate that
  `<role>Operations` is a non-empty sequence and not a string, and dispatch the
  operation files with `ansible.builtin.include_tasks` in a `loop`.
- The dispatch loop SHALL set an explicit singular
  `loop_control.loop_var` (`<role>Operation`) so included tasks do not depend on
  or collide with Ansible's generic `item` variable.
- When every invocation requires a canonical baseline operation, the role SHALL
  declare that operation as the ordered list default in
  `roles/<role>/defaults/main.yml`. Otherwise, the invoking playbook SHALL pass
  the non-empty operation list in its role entry.
- The list variable and its allowed operation names SHALL be documented in the
  role's companion variable schema and toolset documentation.

Application installer roles use this ordered-list pattern and expose it through
one runtime-parameterized playbook, following the stricter contract in
[`application-installer-roles.md`](application-installer-roles.md). A role whose
operations are genuinely mutually exclusive MAY keep a singular
`<role>Operation` selector and direct include.

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
  `(operatingSystem × architecture)` set using exact Ansible fact values and
  dispatches directly from gathered facts.
- Every role that composes multiple operations in one invocation uses an ordered
  plural `<role>Operations` list and an explicit singular dispatch loop variable.
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
