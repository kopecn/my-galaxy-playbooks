# VS Code

Installs VS Code and syncs its extensions. See [`roles/vscode`](../../roles/vscode)
and the [Playbook Layering spec](../../.claude/specs/architecture/playbook-layering.md)
for the layering this role follows.

The single thin playbook `playbooks/vscode.yml` accepts an ordered, non-empty
`vscodeOperations` array at runtime. Its supported operation is `install`, which
installs or updates VS Code, validates it, and syncs configured extensions.

## Supported hosts

| OS family | Architectures |
| --- | --- |
| Darwin | `x86_64`, `arm64` |
| Debian | `x86_64`, `aarch64`, `armv7l` |

Install channel per OS family: Homebrew cask (`visual-studio-code`) on Darwin,
the Microsoft apt repository on Debian. A host outside this matrix fails the
operation with a clear error; other hosts and playbooks continue.

## Variables

| Variable | Where set | Purpose |
| --- | --- | --- |
| `vscodeOperations` | Required `-e` argument; empty role default | Ordered, non-empty array. The currently supported value is `install`. |
| `vscodeExtensions` | `group_vars`/`host_vars` | List of extension IDs to install (e.g. `redhat.vscode-yaml`). Empty list installs none. |

Full descriptions: [`.schema/ansible-vars.schema.json`](../../.schema/ansible-vars.schema.json).

## Usage

Install/update VS Code and sync extensions on a target host. On Debian the apt install escalates, so use `-b`; the sudo password is read from `user-<short-hostname>` in 1Password (the Homebrew-cask path on macOS escalates nothing, but the flag is harmless there). Target the host with `-i '<host-or-ip>,'` — the trailing comma makes it an inline inventory:

```bash
ansible-playbook playbooks/vscode.yml -i '<host-or-ip>,' -b \
  -e onePasswordVault=Personal-Automation \
  -e '{"vscodeOperations":["install"]}'
```

Dry-run before applying (`--check --diff`):

```bash
ansible-playbook playbooks/vscode.yml -i '<host-or-ip>,' -b --check --diff \
  -e onePasswordVault=Personal-Automation \
  -e '{"vscodeOperations":["install"]}'
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
