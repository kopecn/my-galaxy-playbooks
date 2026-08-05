# `gnome.yml` — Workstation Configuration

## Purpose

Configure GNOME desktop preferences and dock favorites.

## Platforms

Debian/Ubuntu only, and only meaningful on a host with an actual GNOME
session running (the Framework Desktop, not a headless server).

## Task sequence

1. Use `community.general.dconf` to set keys like
   `org.gnome.shell favorite-apps` (dock pinning), theme/dark-mode
   preference, etc. — one `dconf` task per logical setting, not one giant
   blob, so a failure/diff is legible.
2. `become: false` — dconf writes to the *login user's* session bus, not a
   system-wide store.

## Safety notes — the dbus gotcha

`dconf` requires `DBUS_SESSION_BUS_ADDRESS` (and often `XDG_RUNTIME_DIR`) to
be set, which an Ansible SSH connection does **not** inherit from a live
graphical login by default. The role needs an explicit
`ansible.builtin.set_fact` or task-level `environment:` block computing
`DBUS_SESSION_BUS_ADDRESS: "unix:path=/run/user/{{ login_uid }}/bus"` (with
`login_uid` resolved via `getent passwd` or a registered `id -u` call)
before any `dconf` task runs, or every task in this role will silently fail
to apply against a real desktop session.

## Testing

This is the one role in the roadmap that's structurally hard to test in
Molecule: a headless Docker container has no GNOME shell, no dbus session,
no display. Do **not** fabricate a Molecule scenario that can't actually
exercise dconf — instead:

- Ship a `tasks/validate.yml` that runs `dconf read <key>` against the real
  host and asserts the applied value, invoked manually (or via a future
  `make validate` target, see `validation-hardening.md`).
- Document in `docs/testing.md`, next to the existing vscode
  Darwin-manual-verification note, that this role is manual-only by nature,
  not by omission.

## Wiring

- `playbooks/workstation-config/gnome.yml`
- No `test-molecule-gnome` target — deliberately absent, documented as such.

## Open questions

- Confirm the actual desired dock favorites / theme settings — the roadmap
  doesn't specify values, so `defaults/main.yml` needs a concrete list
  before this is implementable, not just a placeholder.
