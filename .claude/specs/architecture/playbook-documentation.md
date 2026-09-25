---
last_updated: 2026-09-24
semver: 0.0.1
author: Nicholas Bergantz
scope: project
---

# Playbook Documentation

## Goal

Define the documentation deliverable that accompanies every automated toolset in
this repository, so each toolset is discoverable and usable from a single page.
This spec governs *what documentation must exist and what it contains*; it does
not restate the layering rules in
[`playbook-layering.md`](playbook-layering.md) or the test workflow in
[`docs/testing.md`](../../../docs/testing.md).

## Toolset

A **toolset** is the set of playbooks and the role that automate one tool or
capability — for example `tailscale`, `vscode`, `samba`. A toolset is the unit
this spec requires documentation for.

## Documentation Requirement

Every toolset SHALL have:

- A page at `docs/playbooks/<toolset>.md`.
- A pointer to that page in the **Playbook groupings** list of
  [`readme.md`](../../../readme.md), naming the toolset and its playbook path
  (e.g. `playbooks/core-platform/<toolset>-*.yml`).

The page and the pointer SHALL be created or updated in the same change that
adds or alters the toolset's playbooks, role, or variables. A toolset whose
behavior has changed without a corresponding documentation update is a defect.

## Page Contents

A toolset page SHALL contain, in a form a reader can act on without reading the
role source:

- A title and a one- or two-line summary of what the toolset does, with links to
  its role (`roles/<toolset>`) and to [`playbook-layering.md`](playbook-layering.md).
- When the toolset exposes more than one operation, a table mapping each thin
  playbook to its operation.
- **Supported hosts** — the role's `(operating system × architecture)` matrix,
  and how unsupported hosts fail.
- **Variables** — a table of the toolset's variables giving, for each, where it
  is set and its purpose, with a link to
  [`.schema/ansible-vars.schema.json`](../../../.schema/ansible-vars.schema.json)
  for full descriptions.
- **Usage** — at least one runnable invocation example.
- **Verification** — how the toolset is tested (its Molecule scenario, and any
  paths verified manually).

## Compliance Criteria

Conformance is observable:

- Every toolset under `roles/` has a `docs/playbooks/<toolset>.md` page and a
  matching pointer in `readme.md`.
- Every toolset page contains the sections required above.
- Every variable named on a toolset page is documented in
  [`.schema/ansible-vars.schema.json`](../../../.schema/ansible-vars.schema.json).

## References

- [`playbook-layering.md`](playbook-layering.md) — the layering the documented
  toolsets follow.
- [`docs/testing.md`](../../../docs/testing.md) — the Molecule workflow the
  Verification section points to.
