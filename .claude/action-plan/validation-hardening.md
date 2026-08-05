# Validation & Hardening — cross-cutting (Future)

## Purpose

Not a single playbook — a hardening pass across every role shipped in the
milestones above, closing the gaps that individual action plans deliberately
deferred (kernel reboot behavior, GNOME/dbus, UFW-in-Docker) rather than
faked with a Molecule scenario that couldn't actually exercise them.

## Scope

1. **Idempotency audit**: re-run `make test-molecule` against every role
   twice back-to-back and confirm zero `changed` on the second pass — this
   is already enforced per-scenario by Molecule's `idempotence` step, but a
   fleet-wide audit catches any role whose `changed_when` was left at the
   module default and drifted.
2. **`validate.yml` coverage**: every role should have a `tasks/validate.yml`
   in the shape `roles/vscode/tasks/validate.yml` established — confirm
   `hwe_kernel`, `gnome`, and `samba`'s UFW piece (the roles flagged as
   manual-only in their own action plans) each have one, even without a
   matching Molecule scenario.
3. **`make validate` target**: add a Makefile target that runs each role's
   `validate.yml` directly against `inventories/production` (read-only,
   `--check`-safe assertions only) so the manual-verification roles get a
   repeatable, scriptable check instead of a human running ad hoc commands
   over SSH.
4. **`docs/testing.md` update**: consolidate the "manually verified, not
   simulated" notes scattered across `hwe-kernel.md`, `tailscale.md`, and
   `gnome.md` into one documented list, mirroring the existing vscode
   Darwin-path callout.

## Non-goals

This is explicitly a hardening pass on top of already-shipped roles, not new
functionality — it should not grow new playbooks of its own.

## Wiring

- `Makefile`: new `validate` target (see #3).
- `docs/testing.md`: new "Manually-verified roles" section (see #4).
- No new CI matrix entries — this operates on `inventories/production`
  directly and is not meant to run unattended in CI.
