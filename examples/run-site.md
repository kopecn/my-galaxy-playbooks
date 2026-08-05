# Usage examples

Install dependencies and verify prerequisites:

```bash
make bootstrap
```

Lint everything:

```bash
make lint
```

Dry-run (check mode) against staging:

```bash
make check INVENTORY=inventories/staging/hosts.yml
```


Run the localhost smoke test:

```bash
ansible-playbook -i localhost, -c local tests/test_site.yml
```
