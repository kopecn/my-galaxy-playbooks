# `chrome.yml` — Developer Applications

## Purpose

Install Google Chrome Stable.

## Platforms

Darwin (Homebrew cask) + Debian (Google's official apt repo).

## Task sequence

1. `Darwin.yml`: `community.general.homebrew_cask: name=google-chrome`,
   `become: false`.
2. `Debian.yml`: this is close to a direct copy of `roles/vscode/tasks/Debian.yml`'s
   shape — `deb822_repository` pointed at
   `dl.google.com/linux/chrome/deb/`, Google's signing key via `signed_by`,
   notify the apt-cache-update handler, flush handlers, `apt install
   google-chrome-stable`.
3. `validate.yml`: `google-chrome --version` (headless-safe, doesn't launch
   a browser window).

## Testing

Fully testable in Molecule, same shape as `roles/vscode`'s scenario — package
installed via dpkg query, `google-chrome --version` returns 3 words
(`Google Chrome <version>`).

## Wiring

- `playbooks/app-installers/chrome.yml` (same category dir as
  `playbooks/app-installers/vscode.yml`)
- `test-molecule-chrome` + CI matrix

## Open questions

- None — lowest-risk item in the roadmap, near-identical to the proven
  vscode pattern.
