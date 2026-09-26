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
| `claudeRemoveConfig` | `group_vars`/`host_vars` or `-e` at run time | When `true`, `uninstall` also removes user config (`~/.claude` and `~/.claude.json`). Defaults to `false`, which keeps settings, MCP configuration, and session history. |
| `hostOperatingSystem`, `hostArchitecture` | `host_vars` | Optional declared OS/arch; validated against gathered facts before dispatch. |

Full descriptions: [`.schema/ansible-vars.schema.json`](../../.schema/ansible-vars.schema.json).

## Usage

Install the Claude CLI:

```bash
make LIMIT=host-01 PLAYBOOK=playbooks/claude_install.yml run
```

Print installation diagnostics (`claude --version` and `claude doctor`) without
changing anything (`serial: 1` — one host at a time):

```bash
make PLAYBOOK=playbooks/claude_diagnose.yml run
```

Uninstall, keeping user config (`serial: 1` — one host at a time):

```bash
make LIMIT=host-01 PLAYBOOK=playbooks/claude_uninstall.yml run
```

Uninstall and also remove user config (settings, MCP config, session history).
Set `claudeRemoveConfig: true` in the host's inventory, or pass it directly:

```bash
ansible-playbook -i inventories/production/hosts.ini --limit host-01 \
  -e claudeRemoveConfig=true \
  playbooks/claude_uninstall.yml
```

## Verification

`roles/claude` has a Molecule scenario covering the Debian install path only —
`uninstall`/`diagnose` and the Darwin path are manual-only (Docker has no macOS
containers):

```bash
make test-molecule-claude
```
