# Testing with Molecule

Roles are tested with [Molecule](https://ansible.readthedocs.io/projects/molecule/)
using the Docker driver. Tests are written test-first: define the expected
behavior in `verify.yml`, then make the role satisfy it.

## Layout

```
.config/molecule/config.yml          # shared base config (driver, verifier, deps)
roles/<role>/molecule/<scenario>/
├── molecule.yml                      # platforms + scenario-specific overrides
├── prepare.yml                       # puts the instance in a known start state
├── converge.yml                      # applies the role (run twice → idempotency)
└── verify.yml                        # Ansible asserts describing behavior
```

The shared config is applied via `MOLECULE_GLOBAL_CONFIG`, which the Makefile
exports automatically — so scenario `molecule.yml` files only declare platforms.

## The test sequence

Each molecule target runs `molecule test`, which executes:
`dependency → destroy → syntax → create → prepare → converge → idempotence →
verify → destroy`. The **idempotence** step re-runs `converge.yml` and fails if
any task reports `changed`, enforcing the idempotency rule for the role.

## Prerequisites

- Docker running locally
- `make bootstrap` (installs molecule, the docker plugin, and the
  `community.docker` collection, then verifies prerequisites)

## Commands

Molecule runs as part of the layered test targets:

```bash
make test                  # fast: lint + syntax-check + pytest (no Docker)
make test-molecule         # all molecule scenarios (requires Docker)
make test-all              # test + test-molecule
```

There is one make target per role/scenario, each running the full
`molecule test` sequence:

```bash
make test-molecule-example   # example role, default scenario
```

To drive molecule directly while iterating on a single scenario (converge and
leave the instance up, re-run asserts, log in, tear down):

```bash
cd roles/example
molecule converge -s default   # apply the role, keep the instance running
molecule verify   -s default   # re-run verify.yml assertions
molecule login    -s default   # shell into the instance to debug
molecule destroy  -s default   # tear it down
```

`MOLECULE_GLOBAL_CONFIG` is exported by the Makefile; running molecule directly
in a shell picks it up only if that variable is set, so prefer the make targets
or `export MOLECULE_GLOBAL_CONFIG=$PWD/.config/molecule/config.yml` first.

## Adding a scenario

```bash
cd roles/<role>
molecule init scenario <scenario> -r <role>
```

Then:

1. Write `verify.yml` first (the failing spec) and implement the role until it
   passes.
2. Add a `test-molecule-<name>` target in the Makefile that runs
   `cd roles/<role> && molecule test -s <scenario>`, and list it under
   `test-molecule`.
3. Add that target to the matrix in `.github/workflows/molecule.yml` so CI
   covers it.

## Writing `verify.yml`

- One behavioral concept per `assert` block; give it a descriptive name.
- Use Ansible facts (`stat`, `slurp`, `command` with `changed_when: false`) —
  no external mocks.
- Assert observable outcomes (file exists, service running, content correct),
  not implementation details.
