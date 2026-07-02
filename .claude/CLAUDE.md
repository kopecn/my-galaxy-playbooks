#  — Ansible for Setting up Dev and Production Automation Machines

## Overview

<tbd>

## Critical Rules

### Ansible hosts are long-lived production systems

Every task that runs modifies real system state that persists across all
subsequent runs. There is no kill-and-restart. A bad change compounds through
every future playbook run. Never experiment with module parameters or patterns
— verify first. Before suggesting any change, think through what happens if it
fails mid-run on a live host.

### Home directory paths

Use `{{ login_user_home }}` for user home paths. This fact is captured once in
`prefetch_credentials.yml` with `become: false` so it resolves to the login
user's home on any OS (macOS `/Users/…`, Linux `/home/…`).

Do **not** use `{{ ansible_user_dir }}` or `{{ ansible_env.HOME }}` directly —
when `ansible_become: true` is active (set in group_vars), both resolve to
`/root/`. Do **not** hardcode `/home/{{ ansible_user }}`.


### delegate_to: localhost and become

When a task uses `delegate_to: localhost`, the host-level `ansible_become: true` (from group_vars) overrides task-level `become: false`. Always add `vars: ansible_become: false` alongside `become: false` on delegated tasks.
