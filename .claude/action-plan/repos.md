# `repos.yml` — Core Platform

## Purpose

Clone repositories and establish the workspace layout under the login user's
home directory.

## Platforms

Cross-platform (Darwin + Debian) — `git` behaves the same on both, so this
role likely doesn't need a per-OS task split at all, just `tasks/main.yml`.

## Role structure

- `defaults/main.yml`: `repos_workspace_root: "{{ login_user_home }}/workspace"`,
  `repos: []` (list of `{name, url, dest, version}` objects, populated per
  inventory the same way `vscode_extensions` is).
- `tasks/main.yml`: ensure `repos_workspace_root` exists
  (`ansible.builtin.file`), then `ansible.builtin.git` per entry in `repos`.

## Task sequence

1. Create the workspace root dir, `become: false` (this is the login user's
   own space, no privilege needed).
2. Loop `repos`, `ansible.builtin.git: repo={{ item.url }} dest={{ repos_workspace_root }}/{{ item.dest }} version={{ item.version | default('HEAD') }}`,
   `become: false`.
3. `update: true` but explicit `force: false` (default) — never let a
   re-run silently discard uncommitted local changes in a cloned repo on a
   real workstation.

## Safety notes

`force: false` is load-bearing: this task runs against long-lived dev
machines where a human may have uncommitted work in a cloned repo. If a
clone's local state diverges enough that Ansible can't fast-forward, the
task should fail and require a human to resolve it, not silently clobber it.

Uses `{{ login_user_home }}` per the repo's home-directory rule — never
`ansible_env.HOME`, which resolves to `/root` when `ansible_become: true` is
set at the group level.

## Testing

Molecule can test this fully — clone a small public repo (not a private one
needing SSH keys the CI runner won't have) into the test container, then
converge a second time to prove idempotency and a third variant that edits a
tracked file locally to prove the role doesn't clobber it (`force: false`
should leave it untouched, task reports `failed`/`changed: false` per
`git`'s own idempotency semantics — assert whichever `git` actually returns).

## Wiring

- `playbooks/core-platform/repos.yml`
- `test-molecule-repos` + CI matrix

## Open questions

- Private repos (if any) need SSH keys already present on the host — this
  role should assume key provisioning is out of scope, not attempt to
  manage it, unless the roadmap wants an explicit `ssh_keys.yml` first.
