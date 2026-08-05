# `tailscale.yml` — Core Platform

## Purpose

Configure the Tailscale mesh VPN for network reachability **only** — the
roadmap is explicit that we keep using system `sshd` (not Tailscale SSH), so
this role must not enable `tailscale up --ssh`.

## Platforms

Darwin (Homebrew cask) + Debian (Tailscale's official apt repo, same
deb822 shape as `roles/vscode/tasks/Debian.yml`: add repo + signing key,
flush handlers, install package).

## Task sequence

1. `Darwin.yml`: `community.general.homebrew_cask: name=tailscale`,
   `become: false` (same Homebrew-never-as-root rule as vscode).
2. `Debian.yml`: `deb822_repository` for `pkgs.tailscale.com/stable/ubuntu`,
   notify a handler to `apt update`, flush handlers, `apt install tailscale`.
3. `validate.yml`: check `tailscale status --json` (register, `changed_when: false`).
   If `BackendState != "Running"`, run
   `tailscale up --authkey={{ tailscale_authkey }} --hostname={{ tailscale_hostname }} --ssh=false`,
   otherwise skip — idempotent by checking state first rather than always
   invoking `up`.

## Variables

- `tailscale_authkey`: **must** come from an Ansible Vault-encrypted
  `group_vars`/`host_vars` file, never committed in plaintext. This role
  should just consume the variable, not define a default with a real value.
- `tailscale_hostname`: already present per-host, e.g.
  `inventories/production/host_vars/host-01.yml`.

## Safety notes

`--ssh=false` is the one line that encodes the roadmap's explicit intent —
call it out in a comment in the task itself, not just here, so a future edit
doesn't accidentally flip it. Joining the tailnet changes the host's network
identity; if `tailscale up` is ever run with different flags than a prior
join (e.g., a different `--hostname`), Tailscale will prompt for
re-authorization interactively, which will hang a non-interactive Ansible
run — guard by checking `tailscale status` first as above rather than
re-running `up` unconditionally.

## Testing

Tailscale needs `/dev/net/tun` and `NET_ADMIN`, which aren't reliably
available in the CI Docker driver Molecule uses here. Molecule scenario
should assert package install + config presence only (`tailscale --version`
runs). The actual `tailscale up` / mesh-join / `--ssh=false` behavior is
manual-only, verified with `tailscale status` on the real host and noted in
`docs/testing.md` alongside the other manual-verification playbooks.

## Wiring

- `playbooks/core-platform/tailscale.yml`
- `test-molecule-tailscale` (install-only) + CI matrix
- Vaulted `tailscale_authkey` — needs a decision on where the vault file
  lives before this can be wired into `inventories/production`.

## Open questions

- Where does the Ansible Vault password/file live for this repo? No vault
  usage exists yet — this is the first playbook that needs one.
