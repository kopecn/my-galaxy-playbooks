# `claude_code.yml` — Developer Applications

## Purpose

Install `@anthropic-ai/claude-code` globally via npm.

## Dependency

Requires `nodejs.yml` to have run first (Node 22.x + npm present). This role
should assert `node`/`npm` are on `PATH` rather than silently trying to
install Node itself — the dependency belongs to the roadmap ordering, not to
this role.

## Platforms

Cross-platform — npm behaves the same on Darwin/Debian once Node is present,
so no per-OS task split needed.

## Task sequence

1. Configure a user-level npm global prefix
   (`{{ login_user_home }}/.npm-global`) via `community.general.npm_config`
   or a templated `~/.npmrc`, so global installs don't need root — mirrors
   this repo's existing "never install as root when a user-level install
   works" rule (the same reasoning `roles/vscode/tasks/Darwin.yml` states
   explicitly for Homebrew).
2. `community.general.npm: name=@anthropic-ai/claude-code global=true
   state=present`, `become: false`.
3. `validate.yml`: `claude --version` runs and returns non-empty output.

## Variables

- `claude_code_version: "latest"` in `defaults/main.yml` — consider pinning
  a specific version instead once the workstation rollout stabilizes, so a
  re-run doesn't silently pick up a new major version mid-fleet.

## Testing

Fully testable in Molecule, chained after the `nodejs` role in `converge.yml`
(`roles: [nodejs, claude_code]`) so the scenario exercises the real
dependency order. `claude --version` assertion is cheap and deterministic.

## Wiring

- `playbooks/app-installers/claude_code.yml`
- `test-molecule-claude-code` + CI matrix

## Open questions

- Pin `claude_code_version` to a specific release, or track `latest` and
  accept drift? `state=latest` on every run would fight idempotency
  (Molecule's `idempotence` step fails on any reported `changed`), so
  `state=present` (install-if-missing) is the safer default regardless.
