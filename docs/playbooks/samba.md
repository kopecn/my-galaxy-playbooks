# Samba

Installs Samba (SMB) with required transport encryption and a provisioned SMB
user account, and prints diagnostics. See [`roles/samba`](../../roles/samba)
and the [Playbook Layering spec](../../.claude/specs/architecture/playbook-layering.md)
for the layering this role follows.

The single thin playbook `playbooks/samba.yml` accepts an ordered, non-empty
`sambaOperations` array at runtime and dispatches each operation in order:

| Operation | Result |
| --- | --- |
| `install` | Install packages, require SMB encryption, and provision the SMB user |
| `uninstall` | Purge Samba, configuration, and passdb |
| `diagnose` | Print `testparm`, `pdbedit`, and `smbstatus` output |

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
| `sambaOperations` | Required `-e` argument; empty role default | Ordered, non-empty array containing `diagnose`, `install`, and/or `uninstall`. |
| `sambaUsername` | Role default (`roles/samba/defaults/main.yml`), overridden by downstream inventory or `-e` | SMB/Unix account name to provision. Required for `install`. When unset, it is resolved on the super agent from the `username` field of `sambaPasswordOpItem` in 1Password. |
| `sambaPasswordOpItem` | Role default (`roles/samba/defaults/main.yml`), overridden by downstream inventory or `-e` | 1Password item name (within `onePasswordVault`) whose `username` and `password` fields hold the Samba account name and password. Resolved on the super agent. Empty default forces an explicit override. |
| `sambaPassword` | Extra var (`-e`), never persisted | Direct password, resolved at run time. Use it to pass a password without 1Password; when unset the password comes from `sambaPasswordOpItem` via 1Password. |
| `onePasswordVault` | Role default (`roles/samba/defaults/main.yml`), overridden by downstream inventory or `-e` | 1Password vault containing the Samba password item. Resolved on the super agent; never read from target inventory. |

Full descriptions: [`.schema/ansible-vars.schema.json`](../../.schema/ansible-vars.schema.json).

The account name and password vary by machine. Because this repository is public
it hosts no inventory, so supply them either as per-variable overrides at run
time (`-e sambaUsername=... -e sambaPasswordOpItem=...`) or from a downstream
galaxy repo's inventory. A user shared across many hosts belongs in that repo's
`group_vars`; a host's own users belong in its `host_vars` — Ansible's variable
precedence expresses the host↔user many-to-many.

## Usage

`install` reads the Samba password from 1Password on the super agent. It does not
read the password or its reference from target-host inventory. Set the vault name
via the role default (`roles/samba/defaults/main.yml`), a downstream inventory,
or `-e` at run time:

```yaml
onePasswordVault: your-vault-name
```

The password is passed directly from the super agent's `op` CLI to `smbpasswd`
over stdin and is never written to inventory or disk. Secret resolution runs
through the shared `onepassword` role on the super agent, which reads
`~/.config/op/op-service-account-token`. Its `samba` task owns the exact
username and password queries, including
when the playbook is started directly or by an IDE.

Install Samba and provision the SMB user on a host, overriding the account name
and 1Password item per variable (no inventory required — `-i '<host-or-ip>,'` is the
target host name or IP, the trailing comma making it an inline inventory). `-b`
escalates privileges on the target; the shared SSH role reads the login
account's sudo password from `user-<short-hostname>`. This remains distinct from
the Samba password:

```bash
ansible-playbook playbooks/samba.yml -i '<host-or-ip>,' -b \
  -e onePasswordVault=Personal-Automation \
  -e '{"sambaOperations":["install"]}' \
  -e sambaUsername=fileshare -e sambaPasswordOpItem='Samba fileshare - <host-or-ip>'
```

To pass a Samba password directly without 1Password, override `sambaPassword`
instead of `sambaPasswordOpItem`:

```bash
ansible-playbook playbooks/samba.yml -i '<host-or-ip>,' -b \
  -e onePasswordVault=Personal-Automation \
  -e '{"sambaOperations":["install"]}' \
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
ansible-playbook playbooks/samba.yml -i '<host-or-ip>,' -b \
  -e onePasswordVault=Personal-Automation \
  -e '{"sambaOperations":["uninstall"]}'
```

This purges the `samba`, `samba-common`, and `samba-common-bin` packages
(`samba-common` owns the default config and state dirs, so purging it lets a
later install restore them) and removes Samba's config and state —
`/etc/samba`, `/var/lib/samba` (the passdb, so **all** SMB users),
`/var/cache/samba`, `/var/log/samba`, `/run/samba`. It does **not** delete Unix
accounts or home directories; those are OS state, not Samba's, and are left
intact.

Print Samba configuration and status without changing anything — `diagnose` reads
`testparm`/`pdbedit`/`smbstatus` as root, using the Login item password
(`serial: 1` — one host at a time):

```bash
ansible-playbook playbooks/samba.yml -i '<host-or-ip>,' -b \
  -e onePasswordVault=Personal-Automation \
  -e '{"sambaOperations":["diagnose"]}'
```

Multiple values run in order, for example
`-e '{"sambaOperations":["install","diagnose"]}'`. The playbook requests the
Samba 1Password fields whenever the array contains `install`.

## Verification

`roles/samba` has a Molecule scenario covering the Debian install path only. The
scenario supplies `sambaPassword` directly because the container cannot reach
the super agent's 1Password:

```bash
make test-molecule-samba
```
