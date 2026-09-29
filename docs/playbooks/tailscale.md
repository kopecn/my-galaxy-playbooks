# Tailscale

Installs, connects, disconnects, updates, uninstalls, and reports status and
diagnostics for Tailscale.
See [`roles/tailscale`](../../roles/tailscale) and the
[Playbook Layering spec](../../.claude/specs/architecture/playbook-layering.md)
for the layering this role follows.

One thin playbook per operation, all dispatching into the same role via
`tailscaleOperation`:

| Playbook | Operation |
| --- | --- |
| `playbooks/tailscale_install.yml` | `install` |
| `playbooks/tailscale_up.yml` | `up` — connect to the tailnet |
| `playbooks/tailscale_down.yml` | `down` — disconnect from the tailnet |
| `playbooks/tailscale_status.yml` | `status` — connection + network diagnostics |
| `playbooks/tailscale_diagnose.yml` | `diagnose` — print `tailscale debug prefs` |
| `playbooks/tailscale_update.yml` | `update` |
| `playbooks/tailscale_uninstall.yml` | `uninstall` |

## Supported hosts

| OS family | Architectures |
| --- | --- |
| Darwin | `x86_64`, `aarch64` |
| Debian | `x86_64`, `aarch64`, `armv7l` |

Install channel per OS family: Homebrew formula on Darwin, the official
`tailscale.com/install.sh` script on Debian. A host outside this matrix fails
the operation with a clear error; other hosts and playbooks continue.

## Variables

| Variable | Where set | Purpose |
| --- | --- | --- |
| `onePasswordVault` | Role default (`roles/tailscale/defaults/main.yml`), overridden by downstream inventory or `-e` | 1Password vault containing the Tailscale provisioning item. Resolved on the super agent; never read from target inventory. |
| `onePasswordTailscaleAPIKey` | Role default (`roles/tailscale/defaults/main.yml`), overridden by downstream inventory or `-e` | 1Password item containing the Tailscale auth key. Resolved on the super agent; never read from target inventory. |
| `tailscaleSSH` | Role default (`roles/tailscale/defaults/main.yml`), overridden by downstream inventory or `-e` | Enable Tailscale SSH (the `--ssh` flag) on `up`. Defaults to `true`; set `false` to bring the node up without Tailscale SSH. |
| `tailscaleVersion` | `group_vars`/`host_vars` | Optional version pin for `update` on Debian (`>= 1.36.0`). Omit for latest. Pinning is unsupported on macOS — `update` rejects a pin there. |
| `hostOperatingSystem`, `hostArchitecture` | `host_vars` | Optional declared OS/arch; validated against gathered facts before dispatch. |

Full descriptions: [`.schema/ansible-vars.schema.json`](../../.schema/ansible-vars.schema.json).

`vpnHostname` is combined with the SSH router's `vpnDomain` when
`useVpn` is enabled. The Tailscale role does not select the SSH route.

## Usage

`up` reads the Tailscale auth key from 1Password on the super agent. It does
not read the key or its reference from target-host inventory. Set the vault and
item names via the role defaults (`roles/tailscale/defaults/main.yml`), a
downstream inventory, or `-e` at run time:

```yaml
onePasswordVault: your-vault-name
onePasswordTailscaleAPIKey: your-item-name
```

The key itself is passed
directly from the super agent's `op` CLI to `tailscale up` over stdin and is
never written to inventory or disk.

Secret resolution runs through the shared `onepassword` role on the super agent,
which reads `~/.config/op/op-service-account-token`. The
`tailscale` task owns the exact auth-key query. A `--check` dry-run does not
query 1Password.

Every Tailscale operation escalates on the target, so use `-b`. The shared SSH
role reads the username, key, and sudo password from 1Password. Target the host
with `-i '<host-or-ip>,'` and supply the vault.

Connect a host to the tailnet:

```bash
ansible-playbook playbooks/tailscale_up.yml -i '<host-or-ip>,' -b -e onePasswordVault=Personal-Automation
```

Disconnect a host from the tailnet (`serial: 1` — one host at a time):

```bash
ansible-playbook playbooks/tailscale_down.yml -i '<host-or-ip>,' -b -e onePasswordVault=Personal-Automation
```

Check connection status and network diagnostics without changing anything:

```bash
ansible-playbook playbooks/tailscale_status.yml -i '<host-or-ip>,' -b -e onePasswordVault=Personal-Automation
```

Print Tailscale preferences (`tailscale debug prefs`) without changing anything:

```bash
ansible-playbook playbooks/tailscale_diagnose.yml -i '<host-or-ip>,' -b -e onePasswordVault=Personal-Automation
```

Update Tailscale to the latest version:

```bash
ansible-playbook playbooks/tailscale_update.yml -i '<host-or-ip>,' -b -e onePasswordVault=Personal-Automation
```

Pin a version on Debian hosts in your downstream inventory's `host_vars`, e.g.
`host_vars/<host-or-ip>.yml`:

```yaml
tailscaleVersion: "1.102.4"
```

Uninstall (runs `serial: 1` — one host at a time):

```bash
ansible-playbook playbooks/tailscale_uninstall.yml -i '<host-or-ip>,' -b -e onePasswordVault=Personal-Automation
```

## Verification

`roles/tailscale` has a Molecule scenario covering the Debian install path
only — `up`/`update`/`uninstall` and the Darwin path are manual-only (no
`/dev/net/tun` / `NET_ADMIN` in the Docker driver, no macOS containers):

```bash
make test-molecule-tailscale
```
