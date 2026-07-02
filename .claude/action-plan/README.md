# Action Plans

One file per roadmap playbook (see the roadmap table in chat / project notes).
Each plan follows the pattern proven by `roles/vscode` + `playbooks/app-installers/vscode.yml`:

- `roles/<name>/{defaults,tasks,handlers,meta}/main.yml`, OS-family tasks split
  into `tasks/{Darwin,Debian}.yml` and dispatched from `tasks/main.yml` on
  `ansible_facts.os_family`, plus a `tasks/validate.yml` that runs regardless
  of platform.
- `roles/<name>/molecule/default/{molecule,prepare,converge,verify}.yml` —
  written test-first, per [docs/testing.md](../../docs/testing.md). Wired into
  `Makefile` (`test-molecule-<name>` target, added to the `test-molecule`
  meta-target) and `.github/workflows/molecule.yml`'s matrix.
- A thin `playbooks/<category>/<name>.yml` entry point that just pulls in the
  role.
- Variables live in role `defaults/` (safe fallback) and get their real values
  from `inventories/production/group_vars/`.

Every plan below explicitly calls out what Molecule/Docker **cannot** verify
(kernel switches, GNOME/dbus sessions, UFW inside containers, live network
joins) — those get a manual verification note instead of a fabricated test,
per [docs/testing.md](../../docs/testing.md) and the vscode role's precedent
(Darwin/Homebrew path is documented as manually verified).

Every plan also re-affirms the repo's non-negotiables from
[.claude/CLAUDE.md](../CLAUDE.md): these are long-lived production hosts, use
`{{ login_user_home }}`, and `delegate_to: localhost` tasks need
`vars: { ansible_become: false }` alongside `become: false`.

## Status

| Plan | Milestone | Risk level |
| --- | --- | --- |
| [hwe-kernel.md](hwe-kernel.md) | Core Platform | High — reboot-gated |
| [repos.md](repos.md) | Core Platform | Low |
| [tailscale.md](tailscale.md) | Core Platform | Medium — network identity |
| [sshd.md](sshd.md) | Core Platform | High — remote-access daemon |
| [python.md](python.md) | Language Toolchains | Low |
| [pip-conf.md](pip-conf.md) | Language Toolchains | Low |
| [nodejs.md](nodejs.md) | Language Toolchains | Low |
| [swift.md](swift.md) | Language Toolchains | Low |
| [chrome.md](chrome.md) | Developer Applications | Low |
| [cursor.md](cursor.md) | Developer Applications | Medium — undocumented API dependency |
| [claude-code.md](claude-code.md) | Developer Applications | Low |
| [claude-md.md](claude-md.md) | Workstation Configuration | Low |
| [gnome.md](gnome.md) | Workstation Configuration | Medium — needs a live desktop session |
| [samba.md](samba.md) | Workstation Configuration | Medium — file share + firewall |
| [validation-hardening.md](validation-hardening.md) | Validation & Hardening | N/A — cross-cutting |
| [linux-rt-kernel.md](linux-rt-kernel.md) | Long-Term Performance | High — deferred, gated on stability |
