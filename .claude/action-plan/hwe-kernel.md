# `hwe_kernel.yml` — Core Platform

## Purpose

Install `linux-generic-hwe-24.04` so the Framework Desktop's newer AMD
silicon (Wi-Fi/Bluetooth/GPU) is actually supported by the kernel Ubuntu
24.04 ships with by default.

## Platforms

Debian/Ubuntu only. `roles/hwe_kernel` should assert
`ansible_facts.distribution == 'Ubuntu'` and
`ansible_facts.distribution_version is version('24.04', '>=')` up front and
fail loudly otherwise — this package doesn't exist on other releases and
silently no-op-ing would hide a misconfigured inventory.

## Role structure

No `Darwin.yml` — this role only has one platform, so `tasks/main.yml` can
contain the logic directly (skip the per-OS dispatch pattern vscode uses,
it'd be dead weight for a single-platform role).

## Task sequence

1. Assert platform (above).
2. `apt install linux-generic-hwe-24.04` (`state: present`, not `latest` —
   don't silently pull a newer HWE stack on a re-run).
3. Check whether the *running* kernel matches the *installed* kernel:
   compare `ansible_facts.kernel` against the newest `vmlinuz-*` in `/boot`
   (or read `/var/run/reboot-required`). Register this as a fact.
4. **Do not reboot automatically.** Set `hwe_kernel_reboot_required: true/false`
   and surface it with `ansible.builtin.debug` / `ansible.builtin.fail` (if
   `hwe_kernel_require_confirmation: true`, the default) so a human decides
   when to reboot a production host.
5. Only if an explicit `hwe_kernel_allow_reboot: true` override is set, use
   `ansible.builtin.reboot` with a generous `reboot_timeout` and
   `post_reboot_delay`, then re-verify `ansible_facts.kernel` changed.

## Safety notes

This is the highest-risk playbook in the roadmap: a bad HWE kernel that
doesn't boot turns a remote host into a brick with no out-of-band console
assumed. Default to **install-only, reboot-gated**. Document in the role's
`README`/`meta` that step 5 should only be flipped on for a host you have
physical or IPMI/BMC access to, never blindly against `inventories/production`.

## Testing

Docker containers share the host kernel — Molecule cannot exercise the
kernel switch or boot behavior at all. Molecule scenario is limited to
asserting the package installs and `apt-cache policy linux-generic-hwe-24.04`
resolves. The actual "does the new kernel boot and does hardware work"
verification is manual-only, done on the physical Framework Desktop, and
should be documented as a checklist in `docs/testing.md` next to the vscode
Darwin-path precedent (manually verified, not simulated).

## Wiring

- `playbooks/core-platform/hwe_kernel.yml`
- `test-molecule-hwe-kernel` in `Makefile` (install-assertion only) + CI matrix
- Note the manual-verification requirement in `docs/testing.md`

## Open questions

- Confirm reboot policy: fully manual (recommended) vs. opt-in flag as above.
- Confirm whether this repo has any out-of-band recovery path for the
  Framework Desktop before we ever flip `hwe_kernel_allow_reboot: true`.
