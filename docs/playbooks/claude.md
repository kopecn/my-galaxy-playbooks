# Claude CLI

Installs, uninstalls, and diagnoses the [Claude Code](https://code.claude.com/docs)
CLI. See [`roles/claude`](../../roles/claude) and the
[Playbook Layering spec](../../.claude/specs/architecture/playbook-layering.md)
for the layering this role follows.

The single thin playbook `playbooks/claude.yml` accepts an ordered, non-empty
`claudeOperations` array at runtime and dispatches each operation in order:

| Operation | Result |
| --- | --- |
| `install` | Install Claude Code |
| `diagnose` | Print `claude --version` and `claude doctor` |
| `uninstall` | Uninstall Claude Code and remove user configuration |

## Supported hosts

| OS family | Architectures |
| --- | --- |
| Darwin | `x86_64`, `arm64` |
| Debian | `x86_64`, `aarch64` |

Install channel: Anthropic's native installer script
(`https://claude.ai/install.sh`) on both OS families. It installs to
`~/.local/bin/claude` as the login user (never root) and self-updates in the
background. A host outside this matrix fails the operation with a clear error;
other hosts and playbooks continue.

Windows is not yet supported by this role.

## Variables

| Variable | Where set | Purpose |
| --- | --- | --- |
| `claudeOperations` | Required `-e` argument; empty role default | Ordered, non-empty array containing `diagnose`, `install`, and/or `uninstall`. |

`uninstall` always removes user config (`~/.claude` and `~/.claude.json`) along
with the CLI itself — settings, MCP configuration, and session history do not
survive an uninstall.

Full descriptions: [`.schema/ansible-vars.schema.json`](../../.schema/ansible-vars.schema.json).

## Usage

Target a host with `-i '<host-or-ip>,'` — the trailing comma makes it an inline inventory (replace `<host-or-ip>` with your host name or IP). The shared SSH role reads the username, key, and sudo password from 1Password before connecting. Only `install` escalates (it apt-installs the `bash`/`curl` prerequisites on Debian); the CLI install step itself, `diagnose`, and `uninstall` all run as the login user.

Install the Claude CLI; `-b` enables sudo and the password comes from `user-<short-hostname>`:

```bash
ansible-playbook playbooks/claude.yml -i '<host-or-ip>,' -b \
  -e onePasswordVault=Personal-Automation \
  -e '{"claudeOperations":["install"]}'
```

Print installation diagnostics (`claude --version` and `claude doctor`) without
changing anything (`serial: 1` — one host at a time):

```bash
ansible-playbook playbooks/claude.yml -i '<host-or-ip>,' \
  -e onePasswordVault=Personal-Automation \
  -e '{"claudeOperations":["diagnose"]}'
```

Uninstall the CLI and remove user config — settings, MCP config, and session
history (`serial: 1` — one host at a time):

```bash
ansible-playbook playbooks/claude.yml -i '<host-or-ip>,' \
  -e onePasswordVault=Personal-Automation \
  -e '{"claudeOperations":["uninstall"]}'
```

Pass multiple values to compose a workflow; for example,
`-e '{"claudeOperations":["install","diagnose"]}'` installs and then verifies.

## Verification

`roles/claude` has a Molecule scenario covering the Debian install path only —
`uninstall`/`diagnose` and the Darwin path are manual-only (Docker has no macOS
containers):

```bash
make test-molecule-claude
```
