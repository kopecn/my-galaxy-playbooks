# my-galaxy-playbooks

Ansible automation for provisioning dev and production machines: playbooks,
first-party roles, per-environment inventories, and Molecule role tests, with
lint + molecule CI on GitHub Actions.

## Layering

Authoring and deployment follow a mandatory three-layer model — complexity is
pushed down the stack, never smeared across playbooks:

| Layer | Owns | Concern |
| --- | --- | --- |
| Playbooks | intent | *What* to do — "install VS Code", "roll ssh keys". OS/arch-agnostic. |
| Roles | implementation | *How* to do it across the host OS × architecture matrix. |
| Global configuration | data | Flags and parameters describing hosts and features. |

The [Playbook Layering spec](.claude/specs/architecture/playbook-layering.md) is
the authoritative, must-follow contract. In short: playbooks declare intent and
never branch on OS/arch; roles are the only layer that branches on OS ×
architecture, declare their supported combinations, validate declared
`hostOperatingSystem`/`hostArchitecture` against gathered facts, and error
non-fatally on an unsupported host; global config lives in
`inventories/<env>/group_vars/all.yml`. Variable names are camelCase and every
variable is documented in
[`.schema/ansible-vars.schema.json`](.schema/ansible-vars.schema.json).

## Quickstart

```bash
make bootstrap   # install ansible/lint/test/molecule deps + Galaxy collections
make lint        # yamllint + ansible-lint
make check       # dry-run PLAYBOOK against INVENTORY (--check --diff)
make run         # apply PLAYBOOK to INVENTORY
make test        # fast: lint + syntax-check + pytest (no Docker)
make test-all    # test + all Molecule scenarios (requires Docker)
```

`INVENTORY`, `PLAYBOOK`, `LIMIT`, and `TAGS` are overridable on the CLI or via a
git-ignored `.env` (copy from `.env.example`).

## Documentation

- [Repository structure](docs/structure.md) — layout and conventions.
- [Testing with Molecule](docs/testing.md) — the test-first role workflow.
- [Playbook Layering](.claude/specs/architecture/playbook-layering.md) — the
  authoring/deployment contract.
