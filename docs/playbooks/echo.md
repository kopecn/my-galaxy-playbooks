# Echo

Validation toolset. Echoes `echo_phrase` first on the control node (the running
host, via `delegate_to: localhost`) and then on each target host, confirming the
variable resolves the same on both — the intended way to check that a downstream
Galaxy variable override actually reaches the managed nodes.

The thin playbook `playbooks/echo.yml` dispatches into
[`roles/echo`](../../roles/echo), which owns the implementation. See the
[Playbook Layering spec](../../.claude/specs/architecture/playbook-layering.md)
for the layering this follows.

## Supported hosts

Any host reachable by Ansible. The role runs `echo` and is OS/architecture-
agnostic — it declares no support matrix and does not branch on OS.

## Variables

| Variable | Where set | Purpose |
| --- | --- | --- |
| `echo_phrase` | Repository-root `vars/defaults.yml` | Phrase echoed on both the control node and each target host. Override to validate that a downstream override propagates. |

## Usage

Echo escalates nothing — it runs as the login user — so no `-b`/`ansible_become_pass` is needed. Target a host with `-i '<host-or-ip>,'` (the trailing comma makes it an inline inventory; replace `<host-or-ip>` with your host name or IP).

```bash
# Against a target host
ansible-playbook playbooks/echo.yml -i '<host-or-ip>,'

# Overriding the phrase to confirm a downstream override propagates
ansible-playbook playbooks/echo.yml -i '<host-or-ip>,' -e echo_phrase='override reached me'
```

Expected output shows the same phrase from `Control node echoed:` and from each
`<host> echoed:` line.

## Verification

No Molecule scenario yet — the toolset is verified manually with the Usage
commands above. Add a scenario under `roles/echo/molecule/` (and its
`test-molecule-echo` targets in the Makefile and `molecule.yml` matrix) to bring
it under CI; see [`docs/testing.md`](../testing.md).
