---
last_updated: 2026-10-08
semver: 0.4.1
author: Nicholas Bergantz
document_type: specification
scope: project
---

# Application Installer Roles

## Goal

This spec gives the minimum, mandatory template for an **application installer**
role. The template makes each tool that this repository sets up (for example
Claude CLI, Ollama, LM Studio, VS Code, and Tailscale) have the same structure. A
new tool follows this template and does not need a new structure.

This spec is about the *structure* of an installer:

- its operations and operation sequence,
- its per-OS tasks,
- its firewall use,
- its playbooks, schema, docs, and tests.

This spec does not say the rules in these documents again. It refers to them:

- [`playbook-layering.md`](playbook-layering.md) for the layering rules.
- [`playbook-documentation.md`](playbook-documentation.md) for the documentation
  rules.
- [`.claude/CLAUDE.md`](../../CLAUDE.md) for the Ansible-safety rules.

An "application installer" is a role that installs, removes, and reports on
software on a target host.

## Operations

An application installer SHALL be one role that does the operations in the
`<tool>Operations` array in sequence. Its operation set changes with the tool. A
full installer SHOULD have these common operations when it does them:

- `install`
- `uninstall`
- `diagnose`

An installer with one purpose SHALL have only the operations that it does, not
stub operations. The complete operation enum SHALL be in
`roles/<tool>/vars/main.yml` as `<tool>SupportedOperations`. Operations more than
the three common operations are permitted when their task files, schema,
documentation, and tests are included together.

## Operation sequence

`roles/<tool>/tasks/main.yml` SHALL do these steps in sequence:

1. Make sure that `<tool>Operations` is a non-empty sequence, is not a string,
   and that its difference from `<tool>SupportedOperations` is empty.
2. Get the target's minimum fact subset with `ansible.builtin.setup`. This MUST
   occur in the role, after the playbook's `ssh` role found the route. Installer
   playbooks keep `gather_facts: false`, because the credentials and the route
   are not available at play start.
3. Fail non-fatally (`ansible.builtin.fail`) with a clear message that names the
   host when the `(OS family × architecture)` pair is not in
   `<tool>SupportMatrix`.
4. Do a loop on `<tool>Operations` with
   `include_tasks: "{{ <tool>Operation }}.yml"`. Keep the caller sequence and set
   `loop_control.loop_var: <tool>Operation`.

`<tool>SupportMatrix` (OS family → the supported architectures) SHALL be in
`roles/<tool>/vars/main.yml`. Its keys and values SHALL be the same as
`ansible_facts.os_family` and `ansible_facts.architecture` exactly. A role SHALL
NOT change, copy, or override those facts, or give them a different name, through
intermediate platform variables.

## OS branches

When an operation is different by OS family, the operation file SHALL divide with
`include_tasks: <operation>-<OsFamily>.yml` (for example `install-Darwin.yml`,
`install-Debian.yml`), with a direct `when: ansible_facts.os_family == '<family>'`.
A role for only one OS family SHALL still use `<tool>SupportMatrix` to stop
unsupported hosts, so an unsupported platform fails with the standard message
and not with an unexpected error.

## Privilege and Homebrew

Homebrew tasks (`community.general.homebrew`, `homebrew_cask`, `homebrew_services`)
SHALL set both `become: false` and `vars: {ansible_become: false}`, because the
host-level `ansible_become: true` makes Homebrew operate as root without both.
[`.claude/CLAUDE.md`](../../CLAUDE.md) gives the other privilege and
home-directory rules.

## Firewall

To open or close a service port, a role SHALL use the
[`firewall`](../../roles/firewall) role through `include_role`, and give
`firewallPort` and a `firewallComment`. `uninstall` SHALL give
`firewallState: absent` to remove the rule. The `firewall` role SHALL use
`ansible_facts.os_family` directly. An installer role SHALL NOT call firewall
modules (`community.general.ufw`, etc.) directly. The `firewall` role opens ports
on Linux (UFW when it is present) and does nothing on macOS.

## Playbooks

Each application installer SHALL have one small playbook
`playbooks/<tool>.yml` with `hosts: all`, `gather_facts: false`, and `serial: 1`.
It SHALL use `onepassword` (`onePasswordTasks: [ssh_user_pass]`) → `ssh` →
`<tool>` in this sequence. The caller SHALL give `<tool>Operations` as an array
at `ansible-playbook` runtime. The playbook SHALL NOT hard-code an operation.

When only some operations need another credential query, the playbook MAY get
more `onePasswordTasks` from a type-safe examination of the operation array. The
role keeps the authoritative array and enum validation. Installer playbooks SHALL
have no play-level `become` or `tags`.

## Variables, schema, and docs

- `<tool>Operations` SHALL have an empty-array default in
  `roles/<tool>/defaults/main.yml`, so the runtime caller must select at least
  one operation. It SHALL have documentation as a non-empty enum array in the
  tool's schema group.
- The other variables that the user can override SHALL be in
  `roles/<tool>/defaults/main.yml`. They SHALL be flat camelCase with the group
  token as the prefix (`<tool>Port`). Add a `$ref` to the `allOf` array in
  `.schema/ansible-vars.schema.json`, and put each variable in
  `.schema/groups/<tool>-schema.json`. A role with only `vars/` (the operations
  and the support matrix, with no defaults that the user can override) needs no
  schema group.
- Each toolset SHALL include `docs/playbooks/<tool>.md` and a `readme.md` pointer,
  as in [`playbook-documentation.md`](playbook-documentation.md).

## 1Password item coordinates

A **1Password item coordinate** is a variable whose value becomes the item name
in an `op://<vault>/<item>/<field>` secret reference. The `onepassword` role reads
it. Examples are `tailscaleAuthKeyItem` and `sambaPasswordOpItem`.

- A 1Password item coordinate SHALL be a human-readable item name. It SHALL NOT
  be an item ID (a 1Password UUID). Semantic names keep the items that a program
  makes human-readable and the same each time.
- A 1Password item name SHALL NOT contain a comma. A comma is not valid in an
  `op://` secret reference, so a comma in the name stops the read.
- For each 1Password item coordinate, the description in its schema `$def` SHALL
  give the no-comma rule.
- The role default for each 1Password item coordinate SHALL agree with the two
  rules above, or SHALL be an empty string when the caller must give the name.

## Tests

Static contract tests SHALL examine each application installer. The tests SHALL
make sure that each installer has:

- exactly one `playbooks/<tool>.yml` entry point,
- no `playbooks/<tool>_<operation>.yml` files,
- an empty `<tool>Operations` default,
- a `<tool>SupportedOperations` enum that agrees,
- an operation loop in sequence, and
- a schema definition whose item enum is the same as the role enum.

This test is the regression gate for the pattern across the whole repository.

When the role has a Linux (Debian) install path, it SHALL include a Molecule
`default` scenario (`molecule/default/{molecule,prepare,converge,verify}.yml`)
that tests that path. Write `verify.yml` first. Add the scenario to both the
Makefile (`test-molecule-<tool>`, the `.PHONY` line, and the `test-molecule`
aggregate) and the `.github/workflows/molecule.yml` matrix. A macOS-only role has
no Molecule scenario (the Docker driver has no macOS image). It SHALL give manual
verification steps in its docs page instead.
