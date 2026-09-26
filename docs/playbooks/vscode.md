# VS Code

Installs VS Code and syncs its extensions. See [`roles/vscode`](../../roles/vscode)
and the [Playbook Layering spec](../../.claude/specs/architecture/playbook-layering.md)
for the layering this role follows.

## Supported hosts

| OS family | Architectures |
| --- | --- |
| Darwin | `x86_64`, `aarch64` |
| Debian | `x86_64`, `aarch64`, `armv7l` |

Install channel per OS family: Homebrew cask (`visual-studio-code`) on Darwin,
the Microsoft apt repository on Debian. A host outside this matrix fails the
operation with a clear error; other hosts and playbooks continue.

## Variables

| Variable | Where set | Purpose |
| --- | --- | --- |
| `vscodeExtensions` | `group_vars`/`host_vars` | List of extension IDs to install (e.g. `redhat.vscode-yaml`). Empty list installs none. |
| `hostOperatingSystem`, `hostArchitecture` | `host_vars` | Optional declared OS/arch; validated against gathered facts before dispatch. |

Full descriptions: [`.schema/ansible-vars.schema.json`](../../.schema/ansible-vars.schema.json).

## Usage

Install/update VS Code and sync extensions on the default local inventory
(`tests/inventory/hosts.ini`, the `localhost` loopback):

```bash
make PLAYBOOK=playbooks/vscode.yml run
```

Target just the `[local]` group:

```bash
make LIMIT=local PLAYBOOK=playbooks/vscode.yml run
```

Dry-run before applying (`--check --diff`):

```bash
make PLAYBOOK=playbooks/vscode.yml check
```

Configure the extension list for a group or host in your downstream inventory's
`group_vars`/`host_vars`, or pass it at run time with `-e`:

```yaml
vscodeExtensions:
  - redhat.vscode-yaml
  - ms-python.python
```

## Verification

`roles/vscode` has a Molecule scenario covering the Debian/apt path (Docker
cannot host macOS containers — the Darwin path is verified manually):

```bash
make test-molecule-vscode
```
