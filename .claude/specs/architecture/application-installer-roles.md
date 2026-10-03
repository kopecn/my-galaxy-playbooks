---
last_updated: 2026-10-03
semver: 0.3.0
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
`<tool>Operations` array. Its operation set is tool-specific. A full lifecycle
installer SHOULD expose these common operations when it implements them:

- `install`
- `uninstall`
- `diagnose`

Single-purpose installers SHALL expose only implemented operations rather than
stub operations. The complete operation enum SHALL be declared in
`roles/<tool>/vars/main.yml` as `<tool>SupportedOperations`. Tool-specific
operations beyond the common three are permitted when their task files, schema,
documentation, and tests are shipped together.

## Dispatch

`roles/<tool>/tasks/main.yml` SHALL, in order:

1. Assert `<tool>Operations` is a non-empty sequence, is not a string, and its
   difference from `<tool>SupportedOperations` is empty.
2. Gather the target's minimum fact subset with `ansible.builtin.setup`. This
   MUST happen inside the role, after the playbook's `ssh` role has resolved the
   route; installer playbooks keep `gather_facts: false` because credentials and
   routing are not available at play start.
3. Fail non-fatally (`ansible.builtin.fail`) with a clear message naming the host
   when the `(OS family × architecture)` pair is not in `<tool>SupportMatrix`.
4. Loop over `<tool>Operations` with
   `include_tasks: "{{ <tool>Operation }}.yml"`, preserving caller order and
   setting `loop_control.loop_var: <tool>Operation`.

`<tool>SupportMatrix` (OS family → supported architectures) SHALL live in
`roles/<tool>/vars/main.yml`. Its keys and values SHALL match
`ansible_facts.os_family` and `ansible_facts.architecture` exactly. Roles SHALL
NOT normalize, alias, copy, or override those facts through intermediate
platform variables.

## OS branching

Where an operation differs by OS family, the operation file SHALL branch with
`include_tasks: <operation>-<OsFamily>.yml` (for example `install-Darwin.yml`,
`install-Debian.yml`) guarded directly by
`when: ansible_facts.os_family == '<family>'`. A role that supports only one OS
family SHALL still gate unsupported hosts through
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
`firewallPort` and a `firewallComment`; `uninstall` SHALL pass
`firewallState: absent` to remove the rule. The firewall role SHALL consume
`ansible_facts.os_family` directly. Installer roles SHALL NOT call firewall
modules (`community.general.ufw`, etc.) directly. The firewall role opens ports
on Linux (UFW when present) and no-ops on macOS.

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

Static contract tests SHALL enumerate every application installer and assert
that each has exactly one `playbooks/<tool>.yml` entry point, no
`playbooks/<tool>_<operation>.yml` variants, an empty `<tool>Operations`
default, a matching `<tool>SupportedOperations` enum, ordered loop dispatch,
and a composed schema definition whose item enum matches the role enum. This
test is the repository-wide regression gate for the pattern.

Where the role has a Linux (Debian) install path, it SHALL ship a Molecule
`default` scenario (`molecule/default/{molecule,prepare,converge,verify}.yml`)
exercising that path, with `verify.yml` authored first, and the scenario SHALL be
wired into both the Makefile (`test-molecule-<tool>`, the `.PHONY` line, and the
`test-molecule` aggregate) and the `.github/workflows/molecule.yml` matrix. A
macOS-only role has no Molecule scenario (the Docker driver has no macOS image)
and SHALL state manual verification steps in its docs page instead.
