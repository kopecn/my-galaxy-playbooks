# Repository structure

| Path               | Purpose                                                        |
| ------------------ | -------------------------------------------------------------- |
| `playbooks/`       | Thin entry-point playbooks (`site.yml`). Logic lives in roles. |
| `roles/`           | First-party roles maintained in this repo.                     |
| `galaxy_roles/`    | Roles & collections installed from Galaxy (git-ignored).       |
| `inventories/`     | Per-environment inventories (`production`, `staging`).         |
| `templates/`       | Jinja2 templates rendered to hosts.                            |
| `examples/`        | Usage examples and reference snippets.                         |
| `tests/`           | Smoke / molecule-style tests.                                  |
| `docs/`            | Project documentation.                                         |

## Layering

Authoring and deployment follow a mandatory three-layer model. The
[Playbook Layering spec](../.claude/specs/architecture/playbook-layering.md) is
authoritative; the summary here orients where things live:

- **Playbooks** declare *intent* ("install VS Code") and stay OS/architecture-
  agnostic — no OS/arch branching.
- **Roles** implement intent and are the only layer that branches on OS ×
  architecture. A role declares its supported `(OS × arch)` set, validates the
  declared `hostOperatingSystem`/`hostArchitecture` against gathered facts, and
  errors — without aborting the run — when a combination is unsupported.
- **Global configuration** supplies flags and parameters for all hosts in
  `inventories/<env>/group_vars/all.yml`, with per-host declared facts in
  `host_vars/`.

## Conventions

- Keep playbooks thin; put reusable logic in roles.
- Global configuration lives in `group_vars/all.yml`; per-host declared facts in
  `host_vars/`; role `defaults/` stays role-local (never cross-host config).
- Variable names are camelCase, and every variable is documented in
  [`.schema/ansible-vars.schema.json`](../.schema/ansible-vars.schema.json).
- Every task is named and idempotent. Prefer modules over `command`/`shell`.
- No plaintext secrets — use Ansible Vault or an external secret store.
- Dry-run with `make check` before applying to production.
