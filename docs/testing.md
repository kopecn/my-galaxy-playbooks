# Testing

This repository uses three distinct verification layers: fast static and
contract tests, container-based Molecule scenarios, and live hardware-in-the-loop
(HIL) procedures. Do not describe one layer as another; each proves different
behavior.

## Fast checks

```bash
make test
```

This runs YAML and Ansible linting, syntax-checks every playbook, and executes
the Python contract tests under [`tests/`](../tests). It does not connect to a
managed host and is not an e2e test.

## Molecule

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
make test-molecule-vscode    # vscode role, default scenario
```

To drive molecule directly while iterating on a single scenario (converge and
leave the instance up, re-run asserts, log in, tear down):

```bash
cd roles/vscode
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

## Hardware-in-the-loop testing

HIL procedures execute playbooks against real supported hardware and validate
behavior that static tests or Linux containers cannot prove. The canonical HIL
index is [`hil-test/readme.md`](../hil-test/readme.md); each procedure and its
scripts live directly below [`hil-test/`](../hil-test).

The currently documented procedure is the
[`provisioning-ssh` e2e workflow](../hil-test/provisioning-ssh/readme.md). It
uses these target-side preparation scripts:

- [`enable-user-ssh.sh`](../hil-test/provisioning-ssh/enable-user-ssh.sh)
  returns SSH configuration and the test account to the documented bootstrap
  state.
- [`reload-user-ssh.sh`](../hil-test/provisioning-ssh/reload-user-ssh.sh)
  reloads the SSH daemon and reports its state.

Follow the procedure page in order. Its preparation is destructive to the test
account's SSH material and therefore belongs only on an explicitly designated
HIL target. A successful run must satisfy the procedure's stated gates and final
state; merely completing an Ansible syntax check, static contract test, or
Molecule scenario is not an HIL pass.

Every new HIL workflow SHALL:

1. live under `hil-test/<domain>/` with a `readme.md`;
2. document scope, prerequisites, destructive effects, sanitized invocation,
   gates, success criteria, and recovery;
3. link its scripts using repository-relative paths;
4. use placeholders rather than real hostnames, usernames, passwords, key
   names, vaults, or secret identifiers; and
5. be linked from [`hil-test/readme.md`](../hil-test/readme.md) and the domain's
   `docs/playbooks/<domain>.md` Verification section.
