# `swift.yml` — Language Toolchains

## Purpose

Install Swift 6.0.3, pinned (not "whatever Xcode/apt currently ships").

## Platforms

Primarily Debian/Ubuntu (the roadmap's target hardware is the Framework
Desktop). Darwin already gets a Swift toolchain via Xcode Command Line
Tools, so the Darwin path here is about pinning a specific *additional*
toolchain, not the system default — lower priority than the Linux path.

## Approach

Prefer `swiftly` (Swift.org's official toolchain version manager — the
Swift-world analogue of `uv`/`rustup`) over hand-rolling tarball
downloads/extraction/PATH management. `swiftly install 6.0.3` is idempotent
by design and avoids re-implementing checksum verification and `/opt`
layout by hand.

## Task sequence

1. `Debian.yml`: install `swiftly` via its official install script — same
   objection as `python.md`/`nodejs.md` to piping `curl | sh` blindly
   through Ansible: pin the release, verify the downloaded artifact's
   checksum with `get_url`'s `checksum:` parameter before executing
   anything.
2. `tasks/main.yml` (shared): `swiftly install 6.0.3`, `become: false` (this
   installs into the login user's home, not system-wide), `changed_when`
   keyed off swiftly's own "already installed" output so re-runs are clean.
3. `swiftly use 6.0.3` to set it as the active toolchain for the login user.

## Variables

- `swift_version: "6.0.3"` in `defaults/main.yml`.

## Testing

Fully testable in Molecule: `swift --version` reports `6.0.3`. No
kernel/desktop dependency, though the Debian install may need a somewhat
heavier base image (Swift's toolchain has its own runtime deps like `libcurl`,
`libpython`, etc. — confirm `geerlingguy/docker-ubuntu2404-ansible` has them
or extend `prepare.yml` to install them).

## Wiring

- `playbooks/language-toolchains/swift.yml`
- `test-molecule-swift` + CI matrix

## Open questions

- Confirm `swiftly` is acceptable as a new tool dependency vs. a manual
  tarball install — recommend `swiftly` for the same reason `uv` was chosen
  for Python: idempotent by design instead of reimplemented by hand.
