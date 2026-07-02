# `samba.yml` — Workstation Configuration

## Purpose

Configure a Samba home share and the UFW rules that expose it.

## Platforms

Debian/Ubuntu only (Samba + UFW are Linux constructs).

## Task sequence

1. `apt install samba`.
2. Template `/etc/samba/smb.conf.d/home-share.conf` (or a dedicated snippet
   included from the main `smb.conf` — avoid hand-editing the monolithic
   file, same drop-in reasoning as `sshd.md`) pointing the share at
   `{{ login_user_home }}`.
3. **Validate before restart**: `ansible.builtin.command: testparm -s`
   registered and asserted clean, mirroring the `sshd -t` pattern in
   `sshd.md` — a malformed `smb.conf` shouldn't ever reach a `restarted`
   handler.
4. Set the Samba user password via `smbpasswd -a -s` fed from a **vaulted**
   variable — never plaintext in `group_vars`. This is the second role
   (after `tailscale.yml`) that needs Ansible Vault; if `tailscale.yml`
   lands first, reuse whatever vault file it establishes rather than
   creating a second one.
5. Enable + start `smbd`/`nmbd`.
6. UFW: `community.general.ufw: rule=allow from_ip=<restricted subnet>
   port=139,445 proto=tcp`, explicitly scoped to a subnet — **not**
   `from_ip=any`. Since `tailscale.yml` is in the same milestone group,
   consider scoping this to the tailnet's CIDR so the file share is reachable
   over the mesh VPN only, not the host's general LAN.

## Safety notes

Two separate risks stack here: (1) a bad `smb.conf` — mitigated by
`testparm -s` before any restart, same pattern as `sshd.md`; (2) an
overly-broad UFW rule turning on unauthenticated-adjacent file sharing on a
production workstation — mitigated by scoping the allow rule to a specific
subnet (ideally the Tailscale CIDR) instead of the whole LAN.

## Testing

`testparm -s` validation and package/service-state assertions are fully
testable in Molecule. UFW inside an unprivileged Docker container doesn't
reliably manipulate real netfilter rules, so the UFW-rule assertion should
be **best-effort** in `verify.yml` (check the rule exists in `ufw status
numbered` output rather than testing actual packet filtering) with a note
that real enforcement is manual-verified on the physical host.

## Wiring

- `playbooks/workstation-config/samba.yml`
- `test-molecule-samba` + CI matrix (config-validation scope, UFW caveat noted)

## Open questions

- Confirm the subnet to scope UFW to — recommend the Tailscale CIDR once
  `tailscale.yml` ships, but needs an explicit decision, not an assumption.
- Vault file location (same open question as `tailscale.md`).
