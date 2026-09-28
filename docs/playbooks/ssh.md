# SSH routing

Every remote playbook enters `1password_ssh_user_pass`, then `ssh`, before its
action role. Credential resolution and routing remain separate steps.

```mermaid
flowchart TD
    Start[Playbook starts] --> Credentials[1password_ssh_user_pass loads username, password, and key]
    Credentials --> Flag{useVpn}
    Flag -->|true| Tail[Use vpnHostname.vpnDomain]
    Flag -->|false| Source{Inventory source}
    Source -->|Inline -i host,| Exact[Use inventory_hostname exactly]
    Source -->|Inventory file| Local[Use hostName.local]
    Exact --> Route[Set ansible_host]
    Local --> Route
    Tail --> Route
    Route --> Ephemeral[Apply ephemeral SSH options]
    Ephemeral --> Action[Run the action role]
```

## Inline inventory

When `useVpn` is false, an inline host list is rigid. The router does not
append, remove, or replace any part of the supplied target.

| Invocation | SSH endpoint |
| --- | --- |
| `-i 'hostname,'` | `hostname` |
| `-i 'hostname.local,'` | `hostname.local` |
| `-i 'hostname.tail313959.ts.net,'` | `hostname.tail313959.ts.net` |

## Inventory file

Routing follows this precedence for every host:

- `useVpn: true` selects `vpnHostname.vpnDomain` first.
- Otherwise, an inline `-i` target is used exactly.
- Otherwise, a host loaded from an inventory file selects `hostName.local`.

The inventory owns `hostName`, `vpnHostname`, `vpnDomain`, and the
`useVpn` flag.

## SSH credentials

The `1password_ssh_user_pass` role loads the SSH username from
`<sshLoginPrefix>-<short-hostname>/username` and assigns it to `ansible_user`.
`sshLoginPrefix` defaults to `user`.

The same role loads the Login item's password into `ansible_password` and
`ansible_become_password`. It loads `<sshKeyPrefix>-<short-hostname>` from
`onePasswordVault`, requests OpenSSH format, and assigns it directly to
`ansible_private_key`. All three queries are declared in
`onePasswordSshUserPassQueries`.

The shared `onepassword` query executor reads its service-account token from
`onePasswordTokenFile`, which defaults
to `~/.config/op/op-service-account-token`. The lookup is protected by
`no_log`.

## SSH isolation

The router passes `-F /dev/null`, so it does not read `~/.ssh/config`. It uses
`/dev/null` for user and global known-host files, disables host-key persistence,
and disables SSH connection sharing and control sockets.

This framework does not validate reachability, gather facts, or add
workflow-specific safety behavior.
