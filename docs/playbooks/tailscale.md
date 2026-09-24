# Tailscale

Installs, connects, updates, uninstalls, and reports status for Tailscale.
See [`roles/tailscale`](../../roles/tailscale) and the
[Playbook Layering spec](../../.claude/specs/architecture/playbook-layering.md)
for the layering this role follows.

One thin playbook per operation, all dispatching into the same role via
`tailscaleOperation`:

| Playbook | Operation |
| --- | --- |
| `playbooks/core-platform/tailscale-install.yml` | `install` |
| `playbooks/core-platform/tailscale-up.yml` | `up` — connect to the tailnet |
| `playbooks/core-platform/tailscale-status.yml` | `status` — connection + network diagnostics |
| `playbooks/core-platform/tailscale-update.yml` | `update` |
| `playbooks/core-platform/tailscale-uninstall.yml` | `uninstall` |

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
| `tailscaleAuthKeyReference` | controller's `[local]` `group_vars` (e.g. `inventories/production/group_vars/local.yml`) | **Required for `up`.** A 1Password secret reference (`op://vault/item/field`) to the Tailscale auth key. Resolved from `hostvars['localhost']` and read via the `op` CLI on the controller at run time — never stored in the repo. |
| `tailscaleVersion` | `group_vars`/`host_vars` | Optional version pin for `update` on Debian (`>= 1.36.0`). Omit for latest. Pinning is unsupported on macOS — `update` rejects a pin there. |
| `hostOperatingSystem`, `hostArchitecture` | `host_vars` | Optional declared OS/arch; validated against gathered facts before dispatch. |

Full descriptions: [`.schema/ansible-vars.schema.json`](../../.schema/ansible-vars.schema.json).

`tailscaleHostname`, `tailscaleDomain`, `onePasswordVault`, and
`onePasswordTailscaleAPIKey` are declared in the schema and in
`inventories/production/` but are **not yet consumed** by any task in this
role — they describe intent that isn't wired up yet.

## Usage

`up`, `update`, and `install` shell out to `op` for the auth key, so they run
through `make run`, which wraps the play with `scripts/with-op` to supply the
1Password service-account token; `check` does not.

Connect a host to the tailnet:

```bash
make LIMIT=host-01 PLAYBOOK=playbooks/core-platform/tailscale-up.yml run
```

Check connection status and network diagnostics without changing anything:

```bash
make PLAYBOOK=playbooks/core-platform/tailscale-status.yml run
```

Update Tailscale to the latest version:

```bash
make PLAYBOOK=playbooks/core-platform/tailscale-update.yml run
```

Pin a version on Debian hosts, e.g. `inventories/production/host_vars/host-01.yml`:

```yaml
tailscaleVersion: "1.102.4"
```

Uninstall (runs `serial: 1` — one host at a time):

```bash
make LIMIT=host-01 PLAYBOOK=playbooks/core-platform/tailscale-uninstall.yml run
```

## Verification

`roles/tailscale` has a Molecule scenario covering the Debian install path
only — `up`/`update`/`uninstall` and the Darwin path are manual-only (no
`/dev/net/tun` / `NET_ADMIN` in the Docker driver, no macOS containers):

```bash
make test-molecule-tailscale
```
