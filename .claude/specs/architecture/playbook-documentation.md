---
last_updated: 2026-10-03
semver: 0.2.0
author: Nicholas Bergantz
scope: project
---

# Playbook Documentation

## Goal

Define the canonical documentation contract for every automated domain in this
repository. A reader SHALL be able to determine whether a domain fits their
goal, invoke its basic path, understand its architecture and workflow, configure
it safely, and verify it without reading the implementation.

This specification governs documentation content and accuracy. It does not
restate the implementation rules in
[`playbook-layering.md`](playbook-layering.md) or the general test workflow in
[`docs/testing.md`](../../../docs/testing.md).

## Domain

A **domain** is the set of playbooks and roles that automate one application or
capability, such as `tailscale`, `vscode`, `samba`, `ssh`, or SSH
provisioning. A domain is the unit this specification requires documentation
for. A domain may expose one playbook, several related playbooks, or a reusable
role that is only included by other playbooks.

## Location and discovery

User-facing domain documentation SHALL live under [`docs/`](../../../docs).
Playbook and role domain pages SHALL be located at
`docs/playbooks/<domain>.md`. User-facing documentation SHALL NOT be placed in
a role directory, beside a playbook, or under `.claude/`;
`.claude/specs/` contains the governing specifications, not the user
documentation they require.

Every documented domain SHALL also have a pointer in the **Playbook groupings**
list of [`readme.md`](../../../readme.md). The pointer SHALL name the domain and
each public playbook entry point. Documentation and its discovery pointer SHALL
be created or updated in the same change that adds or alters the domain's
playbooks, roles, operations, variables, supported hosts, or verification path.

## Required page structure

Every `docs/playbooks/<domain>.md` page SHALL contain the following sections in
this order. Additional sections MAY follow or appear where they improve the
page, but SHALL NOT replace a required section.

### Scope

`## Scope` SHALL define the domain boundary and accurately describe every
public operation it owns. It SHALL state what the domain does, what it does not
do when that boundary may be ambiguous, and identify the playbook and role entry
points that implement it.

When a domain exposes multiple operations, Scope SHALL include a table that
lists every accepted operation value and its actual result. For a role using an
ordered operation array, it SHALL name the exact plural runtime variable and
state that array order is execution order.

#### Supported Hosts

Scope SHALL contain a `### Supported Hosts` subsection. It SHALL document the
actual operating-system-family and architecture combinations accepted by the
role, using the exact values returned by `ansible_facts.os_family` and
`ansible_facts.architecture`. It SHALL also describe what happens for an
unsupported combination. Domains that do not execute on a managed host SHALL
say so explicitly instead of inventing a host matrix.

### Goal

`## Goal` SHALL describe the user outcome, not the implementation. It SHALL give
the reader enough information to decide whether this is the correct domain or
playbook for the result they want.

### Invocation

`## Invocation` SHALL show only the smallest basic inclusion or command needed
to enter the domain. A reusable role SHALL show the short `roles:` YAML
fragment used by a playbook, following
[`docs/playbooks/ssh.md`](../../../docs/playbooks/ssh.md). A public playbook
SHALL show one minimal `ansible-playbook` command.

Invocation is intentionally brief. Optional behavior, multiple operations,
alternate inventory forms, overrides, and explanation belong in **Usage**, not
Invocation. The example SHALL use placeholders such as `<target>` and
`<value>`; it SHALL NOT contain environment-specific values.

### Architecture

`## Architecture` SHALL contain a Mermaid diagram showing the domain's static
structure and ownership boundaries. At minimum, the diagram SHALL identify the
public playbook or including playbook, each participating role, external
service or controller dependency, and the managed host when applicable. Edges
SHALL represent actual inclusion or data/control dependencies.

### Workflow

`## Workflow` SHALL contain a Mermaid flowchart or sequence diagram showing the
actual runtime path. It SHALL include, as applicable:

- operation validation and ordered dispatch;
- credential and route resolution;
- fact gathering;
- safety, authentication, platform, and destructive-action gates;
- changes made to the managed host;
- verification steps; and
- meaningful failure or rollback paths.

The diagram SHALL match the implemented task order. It SHALL NOT omit a gate
whose failure prevents later work or depict an unimplemented path.

### Variables

`## Variables` SHALL explain where configuration belongs before listing it:

- environment and group-wide values belong in the downstream inventory's
  `group_vars/`;
- host-specific values belong in the downstream inventory's `host_vars/`;
- invocation-only operation arrays and one-time overrides are passed with
  `-e`; and
- secret values SHALL be supplied through the documented secret resolver or a
  redacted runtime variable, never committed to inventory or documentation.

The section SHALL list every public variable consumed by the domain. Each row
SHALL include:

| Column | Required content |
| --- | --- |
| Variable | Exact camelCase Ansible variable name. |
| Type | Concrete type such as `bool`, `string`, `int`, `array[string]`, or `enum`; enum and array element values SHALL be listed. |
| Source | Exact supported source: role default, `group_vars`, `host_vars`, secret resolver, playbook role argument, or runtime `-e`. |
| Default / required | The real default, or `required` when no usable default exists. |
| Purpose | The behavior controlled by the variable, including whether it is sensitive. |

The table SHALL agree with role defaults, role vars, playbook arguments, and
the companion schemas composed by
[`.schema/ansible-vars.schema.json`](../../../.schema/ansible-vars.schema.json).
Internal facts, registered results, and private implementation variables SHALL
not be presented as user configuration.

### Usage

`## Usage` is REQUIRED when the domain exposes a public playbook. It SHALL
provide runnable, sanitized examples for every supported public operation and
the common compositions a user is expected to run. Each example SHALL state
the expected successful outcome and explain required flags or overrides.

Usage MAY expand on inventory choices, operation ordering, optional variables,
and failure recovery. It SHALL NOT duplicate the intentionally minimal
Invocation section. An operation that is a stub or is not implemented SHALL be
identified as such instead of receiving a fabricated command.

A role-only domain with no public playbook MAY omit Usage after stating in
Invocation which playbooks include it.

### Verification

`## Verification` SHALL identify the evidence that supports the documented
behavior:

- links to the exact unit or contract test files and the behaviors they assert;
- links to applicable Molecule scenarios;
- the e2e HIL procedure and script paths, including required preconditions and
  the success criteria for each gate; and
- the commands used to run those checks.

Verification claims SHALL describe what the cited tests actually execute. A
static test SHALL NOT be described as an e2e test, and a Molecule scenario SHALL
NOT be claimed for an unsupported platform. If required HIL coverage does not
yet exist, the page SHALL explicitly identify that verification gap and SHALL
not imply that the workflow was hardware-validated.

## Existing patterns to preserve

Consistency does not require discarding the useful detail already present in
the domain pages. Authors SHALL draw from these established patterns:

- [`ssh.md`](../../../docs/playbooks/ssh.md) for a short role-inclusion
  **Invocation** distinct from detailed **Usage**;
- [`samba.md`](../../../docs/playbooks/samba.md) for an operation/result table,
  explicit variable ownership, secret-handling boundaries, and outcome-focused
  usage for each operation;
- [`tailscale.md`](../../../docs/playbooks/tailscale.md) for ordered operation
  arrays, supported-host matrices, and complete operation coverage; and
- [`provisioning.md`](../../../docs/playbooks/provisioning.md) for safety gates,
  failure paths, rollback behavior, and e2e HIL-oriented workflows.

These pages are source patterns, not blanket exceptions. When they are changed,
they SHALL be brought into the required structure and checked against the
current implementation and sensitive-information rules in this specification.

## Semantic correctness

Documentation is part of the public interface and SHALL be reviewed against the
implementation in the same change. Every documented playbook path, role name,
operation, variable name, type, default, allowed value, task order, supported
host, invocation flag, test path, and HIL path SHALL exist and behave as stated.

Examples SHALL be syntactically valid. Playbook examples SHALL use the actual
runtime interface, including JSON/YAML syntax for array extra variables where
required. Links SHALL resolve from the documentation page. Historical behavior,
removed playbooks, aliases, and planned functionality SHALL NOT be described as
current behavior.

## Sensitive information

Documentation, diagrams, examples, fixtures quoted in documentation, and error
transcripts SHALL NOT contain real environment-specific or sensitive values,
including:

- hostnames, inventory names, IP addresses, or private domains;
- usernames or account identifiers;
- passwords, tokens, authentication keys, or secret references;
- SSH private or public key material; or
- real SSH key filenames, vault item names, or service-account identifiers.

Use obvious placeholders such as `<target>`, `<username>`, `<password>`,
`<ssh-key-name>`, `<vault>`, and `<secret-item>`. When a syntactically
valid example requires an address or DNS name, use an IANA documentation
address or the reserved `example.com` domain. Variable names and generic
role-default values MAY be documented when they do not reveal an
environment-specific value.

## Compliance criteria

Conformance is observable:

- Every domain page is under `docs/playbooks/` and is linked from
  `readme.md`.
- Every page contains `Scope`, `Scope > Supported Hosts`, `Goal`,
  `Invocation`, `Architecture`, `Workflow`, `Variables`, and
  `Verification`; a page for a public playbook also contains `Usage`.
- Architecture and Workflow each contain a Mermaid diagram with different,
  section-appropriate content.
- Every public operation and variable in the implementation is documented, and
  every documented operation and variable exists in the implementation and
  schema.
- Verification cites real unit/contract tests and the applicable e2e HIL path
  or explicitly records the missing HIL coverage.
- Repository searches and review find no real environment-specific or secret
  values in documentation.
- Documentation checks, schema tests, `make lint`, and `make test` pass.

## References

- [`playbook-layering.md`](playbook-layering.md) — implementation layering and
  variable ownership.
- [`application-installer-roles.md`](application-installer-roles.md) — the
  ordered-operation contract for application installers.
- [`docs/testing.md`](../../../docs/testing.md) — unit, static, and Molecule
  test workflows.
- [`.schema/ansible-vars.schema.json`](../../../.schema/ansible-vars.schema.json)
  — canonical public-variable schemas.
