# Claude CLI

Installs, uninstalls, and diagnoses the [Claude Code](https://code.claude.com/docs)
CLI. See [`roles/claude`](../../roles/claude) and the
[Playbook Layering spec](../../.claude/specs/architecture/playbook-layering.md)
for the layering this role follows.

One thin playbook per operation, all dispatching into the same role via
`claudeOperation`:

| Playbook | Operation |
| --- | --- |
| `playbooks/claude_install.yml` | `install` |
| `playbooks/claude_diagnose.yml` | `diagnose` — print `claude --version` and `claude doctor` |
| `playbooks/claude_uninstall.yml` | `uninstall` |

## Supported hosts

| OS family | Architectures |
| --- | --- |
| Darwin | `x86_64`, `aarch64` |
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
| `hostOperatingSystem`, `hostArchitecture` | `host_vars` | Optional declared OS/arch; validated against gathered facts before dispatch. |

`uninstall` always removes user config (`~/.claude` and `~/.claude.json`) along
with the CLI itself — settings, MCP configuration, and session history do not
survive an uninstall.

Full descriptions: [`.schema/ansible-vars.schema.json`](../../.schema/ansible-vars.schema.json).

## Usage

Target a host with `-i '<host-or-ip>,'` — the trailing comma makes it an inline inventory (replace `<host-or-ip>` with your host name or IP). Only `install` escalates (it apt-installs the `bash`/`curl` prerequisites on Debian); the CLI install step itself, `diagnose`, and `uninstall` all run as the login user, so they take no `-b`/`ansible_become_pass`.

Install the Claude CLI — `-b` with `ansible_become_pass` supplies the target's sudo password for the Debian prerequisites:

```bash
ansible-playbook playbooks/claude_install.yml -i '<host-or-ip>,' -b -e 'ansible_become_pass=<password>'
```

Print installation diagnostics (`claude --version` and `claude doctor`) without
changing anything (`serial: 1` — one host at a time):

```bash
ansible-playbook playbooks/claude_diagnose.yml -i '<host-or-ip>,'
```

Uninstall the CLI and remove user config — settings, MCP config, and session
history (`serial: 1` — one host at a time):

```bash
ansible-playbook playbooks/claude_uninstall.yml -i '<host-or-ip>,'
```

## Verification

`roles/claude` has a Molecule scenario covering the Debian install path only —
`uninstall`/`diagnose` and the Darwin path are manual-only (Docker has no macOS
containers):

```bash
make test-molecule-claude
```
