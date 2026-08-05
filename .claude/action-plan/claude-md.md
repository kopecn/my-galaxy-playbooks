# `claude_md.yml` — Workstation Configuration

## Purpose

Deploy `~/.claude/CLAUDE.md` and the shared configuration repository (the
global spec/memory tree referenced by this user's own `~/.claude/CLAUDE.md`)
onto the workstation.

## Relationship to `repos.yml`

This is conceptually a specific instance of `repos.yml`'s git-clone pattern
(clone the shared config repo into `{{ login_user_home }}/.claude`), not a
new mechanism. Prefer reusing `ansible.builtin.git` the same way rather than
inventing a second cloning approach — if `repos.yml` ships first, this role
can just be a thin wrapper that calls the same task pattern against a fixed
destination, or a single extra entry in the `repos` list plus a symlink/copy
step for anything host-specific.

## Task sequence

1. `ansible.builtin.git`: clone/update the shared config repo to
   `{{ login_user_home }}/.claude` (or wherever the repo's own convention
   places it — confirm against the *actual* path this user's global
   `~/.claude/CLAUDE.md` resolves from before hardcoding one).
2. If any host-specific override file is needed (e.g. a `settings.local.json`
   this repo's own `.claude/settings.local.json` suggests exists per-project),
   template it separately — don't let host-specific values leak into the
   shared repo's tracked files.

## Safety notes

`become: false` throughout — this deploys into the login user's home, never
system-wide. Same `force: false` reasoning as `repos.yml`: don't clobber a
human's local edits to their own config repo on a re-run.

## Testing

Fully testable in Molecule: clone succeeds, `~/.claude/CLAUDE.md` exists and
is non-empty, `git -C ~/.claude remote get-url origin` matches the expected
remote.

## Wiring

- `playbooks/workstation-config/claude_md.yml`
- `test-molecule-claude-md` + CI matrix
- Should run **after** `repos.yml` in any combined run if they share
  clone-conflict potential, otherwise order is independent.

## Open questions

- Confirm the actual source repo URL and target path — this plan assumes
  `{{ login_user_home }}/.claude`, matching the global config layout implied
  by this user's own `~/.claude/CLAUDE.md`, but that should be verified, not
  assumed, before implementation.
