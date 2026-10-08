---
last_updated: 2026-10-03
semver: 0.5.0
author: Nicholas Bergantz
document_type: specification
scope: project
---

# Playbook Layering

## Goal

This spec gives the mandatory layered structure to write and deploy playbooks in
this repository. Put the complex work **down** the stack. Do not spread it across
the playbooks. The playbooks declare *what* is necessary. The roles select *how*
to do it for a host. The global configuration gives the *data*. This spec is the
authority on where each kind of task and variable is. It does not say the
Ansible-safety rules in [`.claude/CLAUDE.md`](../../CLAUDE.md) or the test
workflow in [`docs/testing.md`](../../../docs/testing.md) again.

## The Three Layers

The repository SHALL have three layers. Each layer SHALL have one responsibility:

| Layer | Responsibility | Concern |
|---|---|---|
| 3. Playbooks | Declare intent | *What* to do — "install VS Code", "roll ssh keys". Not for a specific OS or arch. |
| 2. Roles | Do the intent | *How* to do it for the host's OS × architecture matrix. |
| 1. Global configuration | Give data | The flags and parameters that describe hosts and features. |

A layer SHALL NOT take the responsibility of another layer. A higher layer uses a
lower layer. A lower layer SHALL NOT use a higher layer.

## Layer 1 — Global Configuration & Variables

Global configuration is the flags and parameters that identify hosts and select
features — for example `hostName`, `useVpn`, and `vscodeExtensions`.

- This repository is a collection artifact. It SHALL NOT carry environment
  inventories. The configuration that describes hosts — the per-environment
  `group_vars` and the per-host `host_vars` — is in the **downstream consumer's**
  inventory: the repository that installs this collection and gives that data.
- A role's `defaults/main.yml` is role-local and lowest-precedence. It SHALL
  carry the default values that a downstream inventory can override, so the role
  is complete when you install it as part of the collection (for example
  `onePasswordVault`, `echo_phrase`). It is the one in-repo source of each role
  variable's default. It SHALL NOT be the authority on cross-host configuration.
  The authoritative per-environment values are in the downstream inventory, and
  they override the role default.
- For local development and test, this repository keeps one loopback inventory
  at [`tests/inventory/hosts.ini`](../../../tests/inventory/hosts.ini)
  (`localhost ansible_connection=local`). It is the default `INVENTORY` and
  `TEST_INVENTORY` for the Makefile, so `make check/run/ping/syntax-check` operate
  locally on the super agent with `-e`/`LIMIT` arguments. It is a test fixture,
  not shipped host data.
- Each project variable SHALL have documentation in the variable schema
  (see [Variable Schema Organization](#variable-schema-organization)) with a
  description. A project variable with no documentation is a defect.
- Variable names SHALL be flat and camelCase. A variable in a group SHALL have
  the name `<group><parameter>` (for example `vpnDomain`, `hostName`,
  `onePasswordVault`). The name prefix and the file structure show the group, not
  variables in a dict.

### Variable Schema Organization

The variable schema gives hover documentation for `host_vars`, `group_vars`, and
role defaults. [`.vscode/settings.json`](../../../.vscode/settings.json) connects
it to the editor, so the root file SHALL stay at
[`.schema/ansible-vars.schema.json`](../../../.schema/ansible-vars.schema.json).

- **Variables stay flat.** A variable SHALL be a top-level scalar or array key,
  not a key in a dict. The depth is for structure (files and directories), not
  for data (dicts). This keeps the per-key override with Ansible's default
  `hash_behaviour: replace`. With that default, a parent dict at a
  higher-precedence layer replaces the full dict and does not merge the keys. A
  merge would silently drop the role-default values that a downstream inventory
  did not give again.
- **One file per group.** Each group's variables SHALL be in a companion file
  [`.schema/groups/<group>-schema.json`](../../../.schema/groups), where
  `<group>` is the lowercase group token: `host`, `vscode`, `tailscale`,
  `samba`, `onepassword`. The group token in the filename is lowercase. The
  variable-name prefix that agrees is camelCase (file `onepassword-schema.json` ↔
  prefix `onePassword`).
- **One definition, reference in `properties`.** In a group file, each variable
  SHALL be exactly once under `$defs`. Show it through `properties` with a local
  `$ref` (`#/$defs/<variableName>`).
- **Put the groups in the root.** The root schema SHALL use an `allOf` `$ref` to
  `groups/<group>-schema.json` for each group file. The group files and the root
  SHALL set `additionalProperties: true`, so the `allOf` composition validates
  each variable where it is, and permits the rest.
- **Ungrouped variables are in the root.** A standalone variable with no group
  prefix (`echo_phrase`, `env`) SHALL be directly in the root schema's `$defs`
  and `properties`, not in a group file.
- **Adding a group.** Make `.schema/groups/<group>-schema.json` as the pattern
  above shows, and add one `allOf` `$ref` to it in the root schema.

## Layer 2 — Roles

Roles own all the host-specific work. They are the **only** layer that can change
with the operating system or the architecture.

- Each role SHALL declare the set of `(operatingSystem × architecture)`
  combinations that it supports.
- The operation sequence SHALL use `ansible_facts.os_family` and
  `ansible_facts.architecture` directly. A role SHALL get the necessary facts
  after the credentials and the SSH route are available. A role SHALL NOT add
  inventory declarations, facts with a different name, or role-local copies of
  platform facts.
- When a role has no tasks for the host's `(operatingSystem × architecture)`, it
  SHALL give a clear error that names the operation, the host, and the
  unsupported combination.
- That error SHALL be isolated to the operation. It SHALL NOT stop the full run.
  Other operations on the same host, and other hosts, SHALL continue.
  (See [Failure Isolation](#failure-isolation).)

### Sequential operation routing

When one role invocation can do more than one sub-operation in sequence, the role
SHALL use an array-based task sequence:

- Each operation SHALL be in `roles/<role>/tasks/<operation>.yml` and contain the
  tasks for that operation.
- The requested operations SHALL be a flat, plural, camelCase array with the name
  `<role>Operations`. The array sequence is the execution sequence, and it is
  part of the role's public interface.
- `roles/<role>/tasks/main.yml` SHALL do only the shared setup, make sure that
  `<role>Operations` is a non-empty sequence and not a string, and do the
  operation files with `ansible.builtin.include_tasks` in a `loop`.
- The loop SHALL set an explicit singular `loop_control.loop_var`
  (`<role>Operation`), so the included tasks do not use or collide with Ansible's
  generic `item` variable.
- When each invocation must have a canonical baseline operation, the role SHALL
  declare that operation as the array default in
  `roles/<role>/defaults/main.yml`. If not, the invoking playbook SHALL give the
  non-empty operation array in its role entry.
- The array variable and its allowed operation names SHALL have documentation in
  the role's companion variable schema and toolset documentation.

Application installer roles use this array pattern and give it through one
runtime-parameterized playbook, as the more strict contract in
[`application-installer-roles.md`](application-installer-roles.md) shows. A role
whose operations are truly only one at a time MAY keep a singular
`<role>Operation` selector and direct include.

## Layer 3 — Playbooks

Playbooks declare intent and nothing more.

- A playbook SHALL be small: it selects which roles operate on which hosts.
- A playbook SHALL NOT be for a specific OS or architecture. A branch on
  operating system or architecture in a playbook is a defect. That task belongs
  in a role.
- A playbook SHALL NOT contain the tasks that a role must own.
- Playbooks SHALL be directly in `playbooks/` (no category subdirectories), with
  lowercase names and `_` word separators. The collection needs this: only
  playbooks directly in the collection's top-level `playbooks/` have a downstream
  address by the fully-qualified collection name (`bergantz_galaxy.home.<name>`,
  for example `bergantz_galaxy.home.echo`).
- A playbook SHALL NOT use `vars_files` with a project-relative path
  (for example `../../vars/defaults.yml`): that path is not correct after you
  install the collection downstream. The shared values come from the role's
  `defaults/main.yml`, and the downstream inventory overrides them.

## Collection Packaging

This repository ships as the Ansible collection `bergantz_galaxy.home`
(namespace `bergantz_galaxy`, name `home`), from
[`galaxy.yml`](../../../galaxy.yml) at the repository root.

- `roles/` and `playbooks/` at the repository root are the collection's roles and
  playbooks. Downstream references point to them as `bergantz_galaxy.home.<role>`
  and `bergantz_galaxy.home.<playbook>`.
- Collection and playbook identifiers are lowercase alphanumeric and `_`, and
  they start with a letter. They have no dashes. (This is why the collection name
  is `home`, not the git repository name `my-galaxy-playbooks`.)
- `ansible-galaxy collection build` SHALL complete with no error; it is the
  packaging gate.

## Failure Isolation

When an operation is not possible for a host, it SHALL fail only that operation
and SHALL NOT stop unrelated work.

- The failure SHALL show where the operation operates, with a clear message.
- Unrelated operations, future playbooks, and other hosts SHALL continue.
- The run's exit status SHALL still show that a failure occurred, so no failure
  is silently hidden.

## Compliance Criteria

You can observe conformance:

- No playbook has a branch on operating system or architecture (no OS/arch
  `when:` conditions in `playbooks/`).
- Each variable in `roles/*/defaults` is also in
  `.schema/ansible-vars.schema.json`.
- Each role for more than one platform declares its supported
  `(operatingSystem × architecture)` set with the Ansible fact values, exactly,
  and it does the operations directly from the facts that it got.
- Each role that does more than one operation in one invocation uses a plural
  `<role>Operations` array in sequence and an explicit singular loop variable.
- All variable names are camelCase.
- An operation for an unsupported `(operatingSystem × architecture)` fails only
  that operation while the rest of the run completes.
- `make lint` and `make test` pass.

## References

- [`.claude/CLAUDE.md`](../../CLAUDE.md) — repository-wide Critical Rules
  (idempotency, home-directory paths, `become` and `delegate_to` semantics).
- [`docs/testing.md`](../../../docs/testing.md) — the test-first Molecule
  workflow for roles.
- [`.schema/ansible-vars.schema.json`](../../../.schema/ansible-vars.schema.json)
  — the variable documentation schema.
