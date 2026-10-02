# LM Studio

Installs, uninstalls, and diagnoses [LM Studio](https://lmstudio.ai) on macOS via
its Homebrew cask. See [`roles/lm_studio`](../../roles/lm_studio) and the
[Playbook Layering spec](../../.claude/specs/architecture/playbook-layering.md)
for the layering this role follows.

One thin playbook per operation, all dispatching into the same role via
`lmStudioOperation`:

| Playbook | Operation |
| --- | --- |
| `playbooks/lm_studio_install.yml` | `install` |
| `playbooks/lm_studio_diagnose.yml` | `diagnose` — print the installed cask version |
| `playbooks/lm_studio_uninstall.yml` | `uninstall` |

## Supported hosts

| OS family | Architectures |
| --- | --- |
| Darwin | `x86_64`, `aarch64` |

Install channel: the Homebrew cask `lm-studio` on Darwin. LM Studio is macOS-only
in this repo; a non-Darwin host fails the operation with a clear error, and other
hosts and playbooks continue.

## Variables

| Variable | Where set | Purpose |
| --- | --- | --- |
| `lmStudioPort` | Role default (`roles/lm_studio/defaults/main.yml`), overridden by downstream inventory or `-e` | TCP port the LM Studio server listens on. Defaults to `1234`. Recorded for documentation; the role does not open it (see below). |
| `hostOperatingSystem`, `hostArchitecture` | `host_vars` | Optional declared OS/arch; validated against gathered facts before dispatch. |

Full descriptions: [`.schema/ansible-vars.schema.json`](../../.schema/ansible-vars.schema.json).

## Firewall and serving

LM Studio ships as a desktop app. Enabling its local server, serving it on the
LAN, and allowing it through the macOS application firewall are done in the app
(or via the `lms` CLI) and are out of this role's scope. The shared
[`firewall`](../../roles/firewall) role opens ports only on Linux (UFW), so it is
not invoked here. `lmStudioPort` documents the server's default port for when you
configure serving by hand.

## Usage

```bash
ansible-playbook playbooks/lm_studio_install.yml \
  -i '<host-or-ip>,' -e onePasswordVault=Personal-Automation
```

Swap `lm_studio_install.yml` for `lm_studio_diagnose.yml` or
`lm_studio_uninstall.yml` to run the other operations.

## Verification

This role has no Molecule scenario: it is macOS-only, and the Docker driver has no
macOS image. Verify manually on a Darwin host — run `lm_studio_install.yml`,
confirm `lm_studio_diagnose.yml` reports a cask version, then
`lm_studio_uninstall.yml` removes it.
