---
last_updated: 2026-10-03
semver: 0.2.0
author: Nicholas Bergantz
scope: project
---

# Application Installer Roles

## Goal

Define the minimal, mandatory template an **application installer** role follows,
so every tool this repo provisions (Claude CLI, Ollama, LM Studio, VS Code,
Tailscale, …) is shaped the same way and a new one can be added by pattern, not
invention. This spec governs the *structure* of an installer — its operations,
dispatch, OS branching, firewall handling, playbooks, schema, docs, and tests. It
does not restate the layering rules in
[`playbook-layering.md`](playbook-layering.md), the documentation rules in
[`playbook-documentation.md`](playbook-documentation.md), or the Ansible-safety
rules in [`.claude/CLAUDE.md`](../../CLAUDE.md); it references them.

An "application installer" is any role whose job is to install, remove, and report
on a piece of software on a target host.

## Operations

An application installer SHALL be a single role that dispatches an ordered
`<tool>Operations` array. It SHALL support at least these three operations:

- `install`
- `uninstall`
- `diagnose`

The complete operation enum SHALL be declared in
`roles/<tool>/vars/main.yml` as `<tool>SupportedOperations`. Tool-specific
operations beyond the common three are permitted when their task files, schema,
documentation, and tests are shipped together.

## Dispatch

`roles/<tool>/tasks/main.yml` SHALL, in order:

1. Assert `<tool>Operations` is a non-empty sequence, is not a string, and its
   difference from `<tool>SupportedOperations` is empty.
2. Normalize the gathered architecture (`arm64` → `aarch64`) into `<tool>Arch`.
3. When `hostOperatingSystem` / `hostArchitecture` are declared, assert each
   matches the gathered facts.
4. Resolve `<tool>OsFamily` and `<tool>EffectiveArch` from the declared values or
   the gathered facts.
5. Fail non-fatally (`ansible.builtin.fail`) with a clear message naming the host
   when the `(OS family × architecture)` pair is not in `<tool>SupportMatrix`.
6. Loop over `<tool>Operations` with
   `include_tasks: "{{ <tool>Operation }}.yml"`, preserving caller order and
   setting `loop_control.loop_var: <tool>Operation`.

`<tool>SupportMatrix` (OS family → supported architectures) SHALL live in
`roles/<tool>/vars/main.yml`.

## OS branching

Where an operation differs by OS family, the operation file SHALL branch with
`include_tasks: <operation>-<OsFamily>.yml` (for example `install-Darwin.yml`,
`install-Debian.yml`) guarded by `when: <tool>OsFamily == '<family>'`. A role that
supports only one OS family SHALL still gate unsupported hosts through
`<tool>SupportMatrix`, so an unsupported platform fails with the standard message
rather than a surprising error.

## Privilege and Homebrew

Homebrew tasks (`community.general.homebrew`, `homebrew_cask`, `homebrew_services`)
SHALL set both `become: false` and `vars: {ansible_become: false}`, because the
host-level `ansible_become: true` otherwise forces Homebrew to run as root. Other
privilege and home-directory rules are governed by
[`.claude/CLAUDE.md`](../../CLAUDE.md).

## Firewall

Opening or closing a service port SHALL delegate to the shared
[`firewall`](../../roles/firewall) role via `include_role`, passing
`firewallOsFamily`, `firewallPort`, and a `firewallComment`; `uninstall` SHALL
pass `firewallState: absent` to remove the rule. Installer roles SHALL NOT call
firewall modules (`community.general.ufw`, etc.) directly. The firewall role opens
ports on Linux (UFW when present) and no-ops on macOS.

## Playbooks

Each application installer SHALL expose one thin playbook
`playbooks/<tool>.yml` with `hosts: all`, `gather_facts: false`, and `serial: 1`.
It SHALL chain `onepassword` (`onePasswordTasks: [ssh_user_pass]`) → `ssh` →
`<tool>`. The caller SHALL supply `<tool>Operations` as an array at
`ansible-playbook` runtime; the playbook SHALL NOT hard-code an operation.

When only some operations need another credential query, the playbook MAY
derive additional `onePasswordTasks` from a type-safe inspection of the
operation array. The role remains responsible for authoritative array and enum
validation. Installer playbooks SHALL carry no play-level `become` or `tags`.

## Variables, schema, and docs

- `<tool>Operations` SHALL have an empty-list default in
  `roles/<tool>/defaults/main.yml`, forcing the runtime caller to choose at
  least one operation, and SHALL be documented as a non-empty enum array in the
  tool's schema group.
- Other user-overridable variables SHALL live in `roles/<tool>/defaults/main.yml`, be
  flat camelCase prefixed with the group token (`<tool>Port`), and be registered
  in `.schema/groups/<tool>-schema.json` with a `$ref` added to the `allOf` array
  in `.schema/ansible-vars.schema.json`. A role that ships only `vars/`
  (operations + support matrix, no overridable defaults) needs no schema group.
- Each toolset SHALL ship `docs/playbooks/<tool>.md` and a `readme.md` pointer per
  [`playbook-documentation.md`](playbook-documentation.md).

## Tests

Where the role has a Linux (Debian) install path, it SHALL ship a Molecule
`default` scenario (`molecule/default/{molecule,prepare,converge,verify}.yml`)
exercising that path, with `verify.yml` authored first, and the scenario SHALL be
wired into both the Makefile (`test-molecule-<tool>`, the `.PHONY` line, and the
`test-molecule` aggregate) and the `.github/workflows/molecule.yml` matrix. A
macOS-only role has no Molecule scenario (the Docker driver has no macOS image)
and SHALL state manual verification steps in its docs page instead.
