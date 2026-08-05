# `sshd.yml` — Core Platform

## Purpose

Tune `MaxStartups`/`MaxSessions` and validate the result with aggregated
`sshd -T` output across hosts.

## Platforms

Darwin (`/etc/ssh/sshd_config`, service is `com.openssh.sshd` under launchd)
and Debian (`/etc/ssh/sshd_config`, service name is `ssh`, **not** `sshd` —
a real gotcha worth a code comment). Needs the per-OS task split.

## Task sequence

1. Drop a config snippet at `/etc/ssh/sshd_config.d/99-ansible-tuning.conf`
   (`ansible.builtin.template`) rather than editing the monolithic
   `sshd_config` — smaller diff, trivially reversible, and sshd's own
   `Include` ordering means drop-ins already win. Use the module's
   `validate: 'sshd -t -f %s'` parameter so a syntactically broken config is
   rejected **before** it's ever written to the real path.
2. Notify a handler that reloads (never restarts) the service:
   `ansible.builtin.service: name=ssh state=reloaded` (Debian) /
   `launchctl kickstart -k system/com.openssh.sshd` (Darwin) —
   `reloaded`/`kickstart`, not `restarted`, so an in-flight SSH connection
   (including the one Ansible is using) is never dropped.
3. A final validation play (can be `run_once: true` against `hosts: all`
   using `hostvars`, or a separate `validate.yml` included per-host) runs
   `sshd -T` on each host, registers it, and asserts the effective
   `maxstartups`/`maxsessions` lines match the intended values — this is
   the "aggregated `sshd -T` output" the roadmap calls for.

## Safety notes

This is the second-highest-risk playbook after `hwe_kernel.yml`: it modifies
the daemon Ansible itself is connected through. The drop-in-file +
`validate:` + `reloaded`-not-`restarted` combination is the whole safety
story here — do not deviate from it. If `sshd -t` ever fails, the task
fails and the handler never fires, so the live config (and the live
connection) is untouched.

## Testing

This is one of the more testable playbooks in the roadmap — no kernel/GPU/
dbus dependency, and breaking sshd inside an ephemeral Molecule container is
low-stakes. `verify.yml` should: run `sshd -T`, assert `maxstartups` and
`maxsessions` match the configured values, and separately assert the
container's SSH connection is still reachable after converge (proves reload
didn't drop it). Write `verify.yml` first per the repo's test-first
convention, then implement the role to satisfy it.

## Wiring

- `playbooks/core-platform/sshd.yml`
- `test-molecule-sshd` + CI matrix (fully automatable, no manual-only caveat)

## Open questions

- Confirm target `MaxStartups`/`MaxSessions` values — the roadmap doesn't
  specify numbers, and this role needs concrete defaults to have anything to
  assert in `verify.yml`.
