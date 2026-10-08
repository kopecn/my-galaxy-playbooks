---
last_updated: 2026-10-03
semver: 0.2.0
author: Nicholas Bergantz
document_type: specification
scope: project
---

# Playbook Documentation

## Goal

This spec gives the standard documentation contract for each automated domain in
this repository. A reader SHALL be able to find if a domain fits their goal,
start its basic path, know its architecture and workflow, set it up safely, and
check it, and do all this without a read of the implementation.

This specification is the authority on documentation content and accuracy. It
does not say the implementation rules in
[`playbook-layering.md`](playbook-layering.md) or the general test workflow in
[`docs/testing.md`](../../../docs/testing.md) again.

## Domain

A **domain** is the set of playbooks and roles that automate one application or
capability, for example `tailscale`, `vscode`, `samba`, `ssh`, or SSH
provisioning. A domain is the unit that this specification must have
documentation for. A domain can have one playbook, more than one related
playbook, or a reusable role that only other playbooks include.

## Location and discovery

User-facing domain documentation SHALL be in [`docs/`](../../../docs). Playbook
and role domain pages SHALL be at `docs/playbooks/<domain>.md`. User-facing
documentation SHALL NOT be in a role directory, beside a playbook, or in
`.claude/`. `.claude/specs/` contains the governing specifications, not the user
documentation that they need.

Each documented domain SHALL also have a pointer in the **Playbook groupings**
list of [`readme.md`](../../../readme.md). The pointer SHALL name the domain and
each public playbook entry point. Make or change the documentation and its
discovery pointer in the same change that adds or changes the domain's
playbooks, roles, operations, variables, supported hosts, or verification path.

## Required page structure

Each `docs/playbooks/<domain>.md` page SHALL contain these sections in this
sequence. More sections MAY come after or appear where they help the page, but
SHALL NOT replace a required section.

### Scope

`## Scope` SHALL give the domain limit and show each public operation that it
owns. It SHALL state what the domain does, what it does not do when that limit is
not clear, and name the playbook and role entry points that do it.

When a domain has more than one operation, Scope SHALL include a table that gives
each accepted operation value and its actual result. For a role that uses an
operation array in sequence, it SHALL name the plural runtime variable exactly
and state that the array sequence is the execution sequence.

#### Supported Hosts

Scope SHALL contain a `### Supported Hosts` subsection. It SHALL document the
actual operating-system-family and architecture combinations that the role
accepts, with the exact values that `ansible_facts.os_family` and
`ansible_facts.architecture` give. It SHALL also show what occurs for an
unsupported combination. A domain that does not operate on a managed host SHALL
say this clearly, and SHALL NOT invent a host matrix.

### Goal

`## Goal` SHALL show the user result, not the implementation. It SHALL give the
reader sufficient information to find if this is the correct domain or playbook
for the result that they want.

### Invocation

`## Invocation` SHALL show only the smallest basic inclusion or command that is
necessary to start the domain. A reusable role SHALL show the short `roles:` YAML
fragment that a playbook uses, as
[`docs/playbooks/ssh.md`](../../../docs/playbooks/ssh.md) shows. A public playbook
SHALL show one minimal `ansible-playbook` command.

Invocation is short on purpose. More behavior, more than one operation, other
inventory forms, overrides, and more detail belong in **Usage**, not in
Invocation. The example SHALL use placeholders such as `<target>` and `<value>`.
It SHALL NOT contain environment-specific values.

### Architecture

`## Architecture` SHALL contain a Mermaid diagram that shows the domain's static
structure and ownership limits. As a minimum, the diagram SHALL name the public
playbook or the playbook that includes it, each role in use, each external
service or controller that it needs, and the managed host when applicable. Edges
SHALL show the actual inclusion or the data and control dependencies.

### Workflow

`## Workflow` SHALL contain a Mermaid flowchart or sequence diagram that shows the
actual runtime path. It SHALL include these items when they apply:

- operation validation and the dispatch sequence;
- the credential and route lookup;
- the fact collection;
- the safety, authentication, platform, and destructive-action gates;
- the changes to the managed host;
- the verification steps; and
- the important failure or rollback paths.

The diagram SHALL be the same as the task sequence in the implementation. It
SHALL show each gate whose failure stops later work, and SHALL NOT show a path
that is not implemented.

### Variables

`## Variables` SHALL show where configuration belongs before it gives the
variables:

- environment and group-wide values belong in the downstream inventory's
  `group_vars/`;
- host-specific values belong in the downstream inventory's `host_vars/`;
- operation arrays for the invocation only, and one-time overrides, go with
  `-e`; and
- secret values SHALL come through the documented secret resolver or a
  redacted runtime variable, and SHALL NOT go into inventory or documentation.

The section SHALL give each public variable that the domain uses. Each row
SHALL contain:

| Column | Required content |
| --- | --- |
| Variable | The exact camelCase Ansible variable name. |
| Type | The actual type, for example `bool`, `string`, `int`, `array[string]`, or `enum`; enum and array element values SHALL be given. |
| Source | The exact supported source: role default, `group_vars`, `host_vars`, secret resolver, playbook role argument, or runtime `-e`. |
| Default / required | The actual default, or `required` when there is no usable default. |
| Purpose | What the variable controls, and if it is sensitive. |

The table SHALL agree with role defaults, role vars, playbook arguments, and
the companion schemas that
[`.schema/ansible-vars.schema.json`](../../../.schema/ansible-vars.schema.json)
composes. Internal facts, registered results, and private implementation
variables SHALL NOT appear as user configuration.

### Usage

`## Usage` is REQUIRED when the domain has a public playbook. It SHALL give
runnable, sanitized examples for each supported public operation and the common
combinations that a user will run. Each example SHALL state the successful result
that you expect, and give the necessary flags or overrides.

Usage MAY give more detail on inventory choices, operation sequence, optional
variables, and failure recovery. It SHALL NOT be the same as the Invocation
section, which is minimal on purpose. An operation that is a stub or is not
implemented SHALL be identified as such, and SHALL NOT be given a command that
does not work.

A role-only domain with no public playbook MAY have no Usage section after it
states in Invocation which playbooks include it.

### Verification

`## Verification` SHALL name the data that shows the documented behavior:

- links to the exact unit or contract test files and the behaviors that they test;
- links to applicable Molecule scenarios;
- the e2e HIL procedure and script paths, with the necessary preconditions and
  the success criteria for each gate; and
- the commands that run those checks.

Verification claims SHALL show what the cited tests actually do. A static test
SHALL NOT be shown as an e2e test, and a Molecule scenario SHALL NOT be claimed
for an unsupported platform. If the necessary HIL coverage is not yet there, the
page SHALL clearly name that verification gap, and SHALL NOT imply that the
hardware validated the workflow.

## Existing patterns to keep

Consistency does not mean you must discard the useful detail that is already in
the domain pages. Authors SHALL use these patterns:

- [`ssh.md`](../../../docs/playbooks/ssh.md) for a short role-inclusion
  **Invocation** that is different from a detailed **Usage**;
- [`samba.md`](../../../docs/playbooks/samba.md) for an operation and result
  table, clear variable ownership, secret-handling limits, and result-focused
  usage for each operation;
- [`tailscale.md`](../../../docs/playbooks/tailscale.md) for operation arrays in
  sequence, supported-host matrices, and complete operation coverage; and
- [`provisioning.md`](../../../docs/playbooks/provisioning.md) for safety gates,
  failure paths, rollback behavior, and e2e HIL-focused workflows.

These pages are source patterns, not exceptions for everything. When they change,
they SHALL come into the required structure, and you SHALL check them against the
current implementation and the sensitive-information rules in this specification.

## Semantic correctness

Documentation is part of the public interface, and you SHALL check it against the
implementation in the same change. Each documented playbook path, role name,
operation, variable name, type, default, allowed value, task sequence, supported
host, invocation flag, test path, and HIL path SHALL be there and work as stated.

Examples SHALL have correct syntax. Playbook examples SHALL use the actual
runtime interface, with JSON or YAML syntax for array extra variables when
necessary. Links SHALL work from the documentation page. Behavior from the past,
removed playbooks, aliases, and planned functions SHALL NOT be shown as current
behavior.

## Sensitive information

Documentation, diagrams, examples, fixtures that documentation quotes, and error
transcripts SHALL NOT contain actual environment-specific or sensitive values.
This includes:

- hostnames, inventory names, IP addresses, or private domains;
- usernames or account identifiers;
- passwords, tokens, authentication keys, or secret references;
- SSH private or public key material; or
- actual SSH key filenames, vault item names, or service-account identifiers.

Use clear placeholders such as `<target>`, `<username>`, `<password>`,
`<ssh-key-name>`, `<vault>`, and `<secret-item>`. When an example with correct
syntax must have an address or DNS name, use an IANA documentation address or the
reserved `example.com` domain. You MAY document variable names and generic
role-default values when they do not give an environment-specific value.

## Compliance criteria

You can observe conformance:

- Each domain page is in `docs/playbooks/` and has a link from `readme.md`.
- Each page contains `Scope`, `Scope > Supported Hosts`, `Goal`,
  `Invocation`, `Architecture`, `Workflow`, `Variables`, and
  `Verification`; a page for a public playbook also contains `Usage`.
- Architecture and Workflow each contain a Mermaid diagram, each with different
  content that is correct for its section.
- Each public operation and variable in the implementation has documentation, and
  each documented operation and variable is in the implementation and schema.
- Verification cites actual unit and contract tests and the applicable e2e HIL
  path, or clearly records the missing HIL coverage.
- Repository searches and a check find no actual environment-specific or secret
  values in documentation.
- Documentation checks, schema tests, `make lint`, and `make test` pass.

## References

- [`playbook-layering.md`](playbook-layering.md) — implementation layering and
  variable ownership.
- [`application-installer-roles.md`](application-installer-roles.md) — the
  operation-sequence contract for application installers.
- [`docs/testing.md`](../../../docs/testing.md) — unit, static, and Molecule
  test workflows.
- [`.schema/ansible-vars.schema.json`](../../../.schema/ansible-vars.schema.json)
  — the standard public-variable schemas.
