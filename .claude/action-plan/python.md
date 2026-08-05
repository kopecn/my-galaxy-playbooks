# `python.yml` — Language Toolchains

## Purpose

Install Python 3.13 and `uv`.

## Platforms

Darwin + Debian. Ubuntu 24.04 ("noble") ships Python 3.12 by default — 3.13
isn't in the default apt repos, so this shouldn't fight apt for it.

## Approach

Install `uv` first, then let `uv python install 3.13` manage the actual
Python toolchain — `uv` maintains its own isolated Python builds and is
idempotent by design (`uv python install` is a no-op if the version is
already present), which sidesteps needing a deadsnakes-PPA-style
`apt_repository` task per OS.

## Task sequence

1. `Darwin.yml`: `community.general.homebrew: name=uv`, `become: false`.
2. `Debian.yml`: install `uv` from Astral's pinned-version standalone
   installer via `ansible.builtin.get_url` (checksum-verified,
   `mode: "0755"`) rather than piping `curl | sh` through Ansible — a raw
   `curl | sh` in a task is a supply-chain smell even from an official
   source; pinning the release + verifying its checksum keeps this
   reproducible and auditable.
3. `tasks/main.yml` (shared): `ansible.builtin.command: uv python install 3.13`,
   `changed_when: "'Installed' in uv_install.stdout"` so re-runs report
   `changed: false` correctly.

## Variables

- `python_version: "3.13"` in `defaults/main.yml`, so a future bump is a
  one-line change.

## Testing

Fully testable in Molecule — `uv --version` and `uv python list` (asserting
`3.13` appears and is marked installed) are cheap, deterministic checks with
no kernel/network/desktop dependency.

## Wiring

- `playbooks/language-toolchains/python.yml`
- `test-molecule-python` + CI matrix

## Open questions

- Confirm `uv` itself should be the standing package manager for Python
  dependencies workstation-wide (this repo's own Makefile still uses
  `pip install` directly) — if so, worth a follow-up note in
  `.claude/CLAUDE.md` once this role ships.
