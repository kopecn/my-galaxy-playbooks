# Samba

Installs Samba (SMB) with required transport encryption and a provisioned SMB
user account, and prints diagnostics. See [`roles/samba`](../../roles/samba)
and the [Playbook Layering spec](../../.claude/specs/architecture/playbook-layering.md)
for the layering this role follows.

One thin playbook per operation, all dispatching into the same role via
`sambaOperation`:

| Playbook | Operation |
| --- | --- |
| `playbooks/core-platform/samba-install.yml` | `install` — packages, `smb encrypt = required`, SMB user |
| `playbooks/core-platform/samba-uninstall.yml` | `uninstall` — full teardown: purge Samba, config, and passdb |
| `playbooks/core-platform/samba-diagnose.yml` | `diagnose` — print `testparm`, `pdbedit`, `smbstatus` |

## Supported hosts

| OS family | Architectures |
| --- | --- |
| Debian | `x86_64`, `aarch64`, `armv7l` |

Debian-family only: Samba is installed from the `samba` + `samba-common-bin` apt
packages. macOS ships its own SMB server and is not covered — a host outside
this matrix fails the operation with a clear error; other hosts and playbooks
continue.

## Variables

| Variable | Where set | Purpose |
| --- | --- | --- |
| `sambaUsername` | `vars/defaults.yml` (global default), overridden per variable | SMB/Unix account name to provision. Required for `install`. Empty default forces an explicit override. |
| `sambaPasswordOpItem` | `vars/defaults.yml` (global default), overridden per variable | 1Password item name (within `onePasswordVault`) whose `password` field holds the Samba password. Resolved on the controller. Empty default forces an explicit override. |
| `sambaPassword` | Extra var (`-e`), never persisted | Direct password, resolved at run time. Use it to pass a password without 1Password; when unset the password comes from `sambaPasswordOpItem` via 1Password. |
| `onePasswordVault` | `vars/defaults.yml` | 1Password vault containing the Samba password item. Loaded on the controller; never read from target inventory. |
| `hostOperatingSystem`, `hostArchitecture` | override or `host_vars` | Optional declared OS/arch; validated against gathered facts before dispatch. |

Full descriptions: [`.schema/ansible-vars.schema.json`](../../.schema/ansible-vars.schema.json).

The account name and password vary by machine. Because this repository is public
it hosts no inventory, so supply them either as per-variable overrides at run
time (`-e sambaUsername=... -e sambaPasswordOpItem=...`) or from a downstream
galaxy repo's inventory. A user shared across many hosts belongs in that repo's
`group_vars`; a host's own users belong in its `host_vars` — Ansible's variable
precedence expresses the host↔user many-to-many.

## Usage

`install` reads the Samba password from 1Password on the controller. It does not
read the password or its reference from target-host inventory. Configure the
vault name in the repository-root `vars/defaults.yml` file:

```yaml
onePasswordVault: your-vault-name
```

The password is passed directly from the controller's `op` CLI to `smbpasswd`
over stdin and is never written to inventory or disk. The controller-side task
invokes `scripts/with-op` directly, so it always loads
`~/.config/op/op-service-account-token`, including when the playbook is started
directly or by an IDE.

Install Samba and provision the SMB user on a host, overriding the account name
and 1Password item per variable (no inventory required). `-b` escalates
privileges on the target, so pass the host's **sudo password** as
`ansible_become_password` — this is the login account's sudo password, distinct
from the Samba password:

```bash
ansible-playbook playbooks/core-platform/samba-install.yml -i 'host-01,' -b \
  -e ansible_become_password='<sudo-password>' \
  -e sambaUsername=fileshare -e sambaPasswordOpItem='Samba fileshare - host-01'
```

To pass a Samba password directly without 1Password, override `sambaPassword`
instead of `sambaPasswordOpItem` (still alongside the sudo password):

```bash
ansible-playbook playbooks/core-platform/samba-install.yml -i 'host-01,' -b \
  -e ansible_become_password='<sudo-password>' \
  -e sambaUsername=fileshare -e sambaPassword='<samba-password>'
```

A downstream galaxy repo can set the same variables per host in its
`host_vars`/`group_vars` instead of passing them on the command line.

The SMB password is set only when the user is absent from the Samba passdb, so
re-runs are idempotent. Rotating an existing user's password is not performed by
`install`.

Fully remove Samba from a host — a clean teardown so a later `install` starts
from scratch (`serial: 1` — one host at a time):

```bash
ansible-playbook playbooks/core-platform/samba-uninstall.yml -i 'host-01,' -b \
  -e ansible_become_password='<sudo-password>'
```

This purges the `samba`, `samba-common`, and `samba-common-bin` packages
(`samba-common` owns the default config and state dirs, so purging it lets a
later install restore them) and removes Samba's config and state —
`/etc/samba`, `/var/lib/samba` (the passdb, so **all** SMB users),
`/var/cache/samba`, `/var/log/samba`, `/run/samba`. It does **not** delete Unix
accounts or home directories; those are OS state, not Samba's, and are left
intact.

Print Samba configuration and status without changing anything (`serial: 1` —
one host at a time):

```bash
make PLAYBOOK=playbooks/core-platform/samba-diagnose.yml run
```

## Verification

`roles/samba` has a Molecule scenario covering the Debian install path only. The
scenario supplies `sambaPassword` directly because the container cannot reach
the controller's 1Password:

```bash
make test-molecule-samba
```
