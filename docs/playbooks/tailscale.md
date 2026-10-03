# Tailscale

Installs, connects, disconnects, updates, uninstalls, and reports status and
diagnostics for Tailscale. See [`roles/tailscale`](../../roles/tailscale) and the
[Playbook Layering spec](../../.claude/specs/architecture/playbook-layering.md)
for the layering this role follows.

The single thin playbook `playbooks/tailscale.yml` accepts an ordered,
non-empty `tailscaleOperations` array at `ansible-playbook` runtime. The role
validates every value before running the requested operations in array order.

| Operation | Result |
| --- | --- |
| `install` | Install Tailscale |
| `up` | Connect to the tailnet |
| `down` | Disconnect from the tailnet |
| `status` | Print connection and network diagnostics |
| `diagnose` | Print `tailscale debug prefs` |
| `update` | Update Tailscale |
| `uninstall` | Uninstall Tailscale |

## Supported hosts

| OS family | Architectures |
| --- | --- |
| Darwin | `x86_64`, `arm64` |
| Debian | `x86_64`, `aarch64`, `armv7l` |

Install channel per OS family: Homebrew formula on Darwin, the official
`tailscale.com/install.sh` script on Debian. A host outside this matrix fails
the requested operation list with a clear error; other hosts and playbooks
continue.

## Variables

| Variable | Where set | Purpose |
| --- | --- | --- |
| `tailscaleOperations` | Required `-e` argument; empty role default | Ordered, non-empty array of operations. Valid values are listed above. |
| `onePasswordVault` | `roles/onepassword/defaults/main.yml`, overridden by downstream inventory or `-e` | 1Password vault containing the Tailscale provisioning item. Resolved on the super agent; never read from target inventory. |
| `tailscaleAuthKeyItem` | `roles/tailscale/defaults/main.yml`, overridden by downstream inventory or `-e` | 1Password item ID containing the Tailscale auth key. IDs avoid invalid title characters such as commas in `op://` references. The resolved `tailscaleAuthKey` exists only in memory on the super agent. |
| `tailscaleSSH` | `roles/tailscale/defaults/main.yml`, overridden by downstream inventory or `-e` | Enable Tailscale SSH (the `--ssh` flag) on `up`. Defaults to `false`. |
| `tailscaleVersion` | `group_vars`/`host_vars` or `-e` | Optional version pin for `update` on Debian (`>= 1.36.0`). Omit for latest. Pinning is unsupported on macOS. |

Full descriptions: [`.schema/ansible-vars.schema.json`](../../.schema/ansible-vars.schema.json).

`vpnHostname` is combined with the SSH router's `vpnDomain` when `useVpn` is
enabled. The Tailscale role does not select the SSH route.

## Usage

Pass the operation array as JSON so the CLI preserves its array type. Every
operation escalates on the target, so use `-b`. Target the host with
`-i '<host-or-ip>,'` and supply the vault:

```bash
ansible-playbook playbooks/tailscale.yml -i '<host-or-ip>,' -b \
  -e onePasswordVault=Personal-Automation \
  -e '{"tailscaleOperations":["install"]}'
```

On success, Tailscale is installed. Connect the host to the tailnet:

```bash
ansible-playbook playbooks/tailscale.yml -i '<host-or-ip>,' -b \
  -e onePasswordVault=Personal-Automation \
  -e '{"tailscaleOperations":["up"]}'
```

For `up`, the playbook adds the `tailscale` query to the shared `onepassword`
role. The auth key passes directly from the super agent's `op` CLI to
`tailscale up` over stdin and is never written to inventory or disk. A
`--check` dry-run does not query the key. If the item title differs from the
role default, pass the non-secret item ID separately, for example
`-e tailscaleAuthKeyItem='your-item-id'`; `tailscaleAuthKey` is reserved for the
resolved in-memory secret and is not a user input.

Disconnect the host:

```bash
ansible-playbook playbooks/tailscale.yml -i '<host-or-ip>,' -b \
  -e onePasswordVault=Personal-Automation \
  -e '{"tailscaleOperations":["down"]}'
```

Print connection status and network diagnostics without changing the host:

```bash
ansible-playbook playbooks/tailscale.yml -i '<host-or-ip>,' -b \
  -e onePasswordVault=Personal-Automation \
  -e '{"tailscaleOperations":["status"]}'
```

Print Tailscale preferences without changing the host:

```bash
ansible-playbook playbooks/tailscale.yml -i '<host-or-ip>,' -b \
  -e onePasswordVault=Personal-Automation \
  -e '{"tailscaleOperations":["diagnose"]}'
```

Update to the latest version:

```bash
ansible-playbook playbooks/tailscale.yml -i '<host-or-ip>,' -b \
  -e onePasswordVault=Personal-Automation \
  -e '{"tailscaleOperations":["update"]}'
```

To pin Debian, also pass a version, for example
`-e tailscaleVersion=1.102.4`. Uninstall Tailscale:

```bash
ansible-playbook playbooks/tailscale.yml -i '<host-or-ip>,' -b \
  -e onePasswordVault=Personal-Automation \
  -e '{"tailscaleOperations":["uninstall"]}'
```

Multiple operations run in the supplied order. For example, this installs and
then connects the host in one serial play:

```bash
ansible-playbook playbooks/tailscale.yml -i '<host-or-ip>,' -b \
  -e onePasswordVault=Personal-Automation \
  -e '{"tailscaleOperations":["install","up"]}'
```

An omitted, empty, scalar, or unknown `tailscaleOperations` value fails with a
message listing the supported operations.

## Verification

`roles/tailscale` has a Molecule scenario covering the Debian install path
only. The `up`, `down`, `status`, `diagnose`, `update`, `uninstall`,
ordered multi-operation, and Darwin paths require manual verification:

```bash
make test-molecule-tailscale
```
