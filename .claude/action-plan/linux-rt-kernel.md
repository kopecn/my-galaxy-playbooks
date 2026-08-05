# `linux_rt_kernel.yml` — Long-Term Performance (deferred)

## Purpose

Optional PREEMPT_RT kernel role, explicitly gated by the roadmap until the
rest of the workstation automation is feature-complete and stable — this
plan captures the trigger condition and the shape of the work, not a
build-now spec.

## Gate condition

Do not start implementation until:

- Every "Core Platform" and "Language Toolchains" role has been running
  against `inventories/production` for a soak period without incident
  (`validation-hardening.md`'s idempotency audit passing repeatedly counts
  as evidence, an ad hoc claim does not).
- `hwe_kernel.yml` has proven out the reboot-gated pattern in real
  production use — this role inherits and raises the same risk class, so it
  should reuse a pattern already validated once, not pioneer it.

## Anticipated shape (once gated open)

- Debian/Ubuntu only, same single-platform structure as `hwe_kernel.yml`
  (no `Darwin.yml`).
- Install the RT kernel package (or a custom-built one, depending on Ubuntu
  24.04's RT package availability at implementation time — verify rather
  than assume it's in the standard repos).
- **Higher** risk than `hwe_kernel.yml`, not equal: a custom/RT kernel is
  more likely to fail to boot than a stock HWE kernel. Before any
  `hwe_kernel_allow_reboot`-style flag is even offered for this role,
  confirm a GRUB fallback boot entry exists and is verified reachable —
  otherwise a failed boot has no recovery path short of physical access.
- Reuse the install-only-by-default, explicit-opt-in-reboot pattern from
  `hwe-kernel.md` verbatim rather than inventing a new one.

## Testing

Same constraint as `hwe_kernel.yml`: Docker shares the host kernel, so
Molecule can only ever assert the package installs, never that the RT
kernel boots or that PREEMPT_RT is actually active
(`uname -v` containing `PREEMPT_RT`, checked manually). Manual-verification
note belongs in the same `docs/testing.md` section
`validation-hardening.md` establishes.

## Open questions

- This entire plan is provisional until the gate condition is met — revisit
  and flesh out the task sequence at that point rather than building ahead
  of the roadmap's own stated sequencing.
