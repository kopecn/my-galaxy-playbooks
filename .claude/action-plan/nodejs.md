# `nodejs.yml` — Language Toolchains

## Purpose

Install Node.js 22.x. This is a hard prerequisite for `claude_code.yml`
(global npm install), so it must ship first within the Language Toolchains
milestone.

## Platforms

Darwin (Homebrew) + Debian (NodeSource apt repo).

## Task sequence

1. `Darwin.yml`: `community.general.homebrew: name=node@22`, `become: false`,
   plus a `brew link --overwrite node@22` step since Homebrew doesn't
   symlink versioned formulae by default.
2. `Debian.yml`: NodeSource publishes a setup script that itself adds the
   repo + key — avoid piping that script through Ansible (same objection as
   the `uv` installer in `python.md`). Prefer the documented manual
   apt-repo steps: `get_url` the NodeSource GPG key to
   `/etc/apt/keyrings/nodesource.asc`, then `apt_repository` (or
   `deb822_repository` if NodeSource's feed supports it — verify at
   implementation time) pointed at `deb.nodesource.com/node_22.x`, flush
   handlers, `apt install nodejs`. Same shape as `vscode`'s `Debian.yml`.

## Variables

- `nodejs_version: "22"` in `defaults/main.yml`.

## Testing

Fully testable in Molecule — `node --version` starts with `v22`, `npm
--version` runs. No kernel/network/desktop dependency.

## Wiring

- `playbooks/language-toolchains/nodejs.yml`
- `test-molecule-nodejs` + CI matrix

## Open questions

- None — this is a low-risk, well-trodden install path mirroring vscode's
  Debian pattern almost exactly.
