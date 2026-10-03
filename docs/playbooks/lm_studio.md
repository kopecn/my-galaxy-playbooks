# LM Studio

Installs, uninstalls, and diagnoses [LM Studio](https://lmstudio.ai) on macOS via
its Homebrew cask. See [`roles/lm_studio`](../../roles/lm_studio) and the
[Playbook Layering spec](../../.claude/specs/architecture/playbook-layering.md)
for the layering this role follows.

The single thin playbook `playbooks/lm_studio.yml` accepts an ordered, non-empty
`lmStudioOperations` array at runtime and dispatches each operation in order:

| Operation | Result |
| --- | --- |
| `install` | Install the LM Studio cask |
| `diagnose` | Print the installed cask version |
| `uninstall` | Uninstall the LM Studio cask |

## Supported hosts

| OS family | Architectures |
| --- | --- |
| Darwin | `x86_64`, `arm64` |

Install channel: the Homebrew cask `lm-studio` on Darwin. LM Studio is macOS-only
in this repo; a non-Darwin host fails the operation with a clear error, and other
hosts and playbooks continue.

## Variables

| Variable | Where set | Purpose |
| --- | --- | --- |
| `lmStudioOperations` | Required `-e` argument; empty role default | Ordered, non-empty array containing `diagnose`, `install`, and/or `uninstall`. |
| `lmStudioPort` | Role default (`roles/lm_studio/defaults/main.yml`), overridden by downstream inventory or `-e` | TCP port the LM Studio server listens on. Defaults to `1234`. Recorded for documentation; the role does not open it (see below). |

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
ansible-playbook playbooks/lm_studio.yml -i '<host-or-ip>,' \
  -e onePasswordVault=Personal-Automation \
  -e '{"lmStudioOperations":["install"]}'
```

Diagnose the installed cask:

```bash
ansible-playbook playbooks/lm_studio.yml -i '<host-or-ip>,' \
  -e onePasswordVault=Personal-Automation \
  -e '{"lmStudioOperations":["diagnose"]}'
```

Uninstall the cask:

```bash
ansible-playbook playbooks/lm_studio.yml -i '<host-or-ip>,' \
  -e onePasswordVault=Personal-Automation \
  -e '{"lmStudioOperations":["uninstall"]}'
```

Multiple values run in order, for example
`-e '{"lmStudioOperations":["install","diagnose"]}'`.

## Verification

This role has no Molecule scenario: it is macOS-only, and the Docker driver has
no macOS image. Verify manually on a Darwin host by running `install`,
`diagnose`, and `uninstall` through `playbooks/lm_studio.yml`.
