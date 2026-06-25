# automation-ansible

Ansible automation repo — playbooks, roles, and inventories with linting and CI.

## Quick start

```bash
make bootstrap   # install deps + Galaxy collections, verify prerequisites
make lint        # yamllint + ansible-lint
make check       # dry-run site.yml against production
make run         # apply site.yml
```

Run `make help` for all targets.

## Testing

Roles are unit-tested with [Molecule](docs/testing.md) (Docker driver):

```bash
make test        # fast: lint + syntax-check + pytest (no Docker)
make test-all    # everything, including Molecule (requires Docker)
```

## Layout

- `playbooks/` — entry-point playbooks (`site.yml`); keep them thin
- `roles/` — first-party roles
- `galaxy_roles/` — Galaxy-installed roles/collections (git-ignored)
- `inventories/` — `production` / `staging` inventories
- `files/`, `templates/` — static files and Jinja2 templates
- `tests/`, `docs/`, `examples/` — tests, docs, usage examples

## Collections

Pinned in `requirements.yml`: `community.general`, `awx.awx`, `ansible.posix`, `kubernetes.core`.

## License

MIT
