# Repository structure

| Path               | Purpose                                                        |
| ------------------ | -------------------------------------------------------------- |
| `playbooks/`       | Thin entry-point playbooks (`site.yml`). Logic lives in roles. |
| `roles/`           | First-party roles maintained in this repo.                     |
| `galaxy_roles/`    | Roles & collections installed from Galaxy (git-ignored).       |
| `inventories/`     | Per-environment inventories (`production`, `staging`).         |
| `files/`           | Static files copied verbatim to hosts.                         |
| `templates/`       | Jinja2 templates rendered to hosts.                            |
| `examples/`        | Usage examples and reference snippets.                         |
| `tests/`           | Smoke / molecule-style tests.                                  |
| `docs/`            | Project documentation.                                         |

## Conventions

- Keep playbooks thin; put reusable logic in roles.
- Separate variables by scope: role `defaults/` < inventory `group_vars/` < `host_vars/`.
- Every task is named and idempotent. Prefer modules over `command`/`shell`.
- No plaintext secrets — use Ansible Vault or an external secret store.
- Dry-run with `make check` before applying to production.
