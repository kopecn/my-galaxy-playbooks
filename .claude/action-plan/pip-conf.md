# `pip_conf.yml` — Language Toolchains

## Purpose

Configure pip indexes (e.g. a private index / mirror) for the login user.

## Platforms

Cross-platform, but the config file path differs: Linux
`{{ login_user_home }}/.config/pip/pip.conf`, macOS
`{{ login_user_home }}/Library/Application Support/pip/pip.conf`. Worth a
per-OS path variable rather than a full per-OS task split.

## Task sequence

1. Ensure the parent directory exists (`ansible.builtin.file`,
   `become: false`, this is user-level config, not system-level).
2. `ansible.builtin.template` a `pip.conf.j2` from `pip_index_url` /
   `pip_extra_index_urls` (list) / optional `pip_trusted_hosts` variables to
   the OS-specific path above.

## Variables

- `pip_index_url`, `pip_extra_index_urls: []`, `pip_trusted_hosts: []` in
  `defaults/main.yml` (empty/safe fallbacks — real values in
  `inventories/production/group_vars/`).
- If an extra index requires an auth token embedded in the URL, that value
  must come from an Ansible Vault-encrypted var — never committed in
  plaintext `group_vars`.

## Safety notes

Low blast radius — this only affects `pip`'s behavior for the login user, not
system Python. Still, a bad index URL (typo, unreachable host) silently
breaks every future `pip install` on the box, so `validate.yml` should
confirm the file parses as valid `ini` (e.g. `python3 -c "import
configparser; configparser.ConfigParser().read('<path>')"`) rather than just
asserting the file exists.

## Testing

Fully testable in Molecule: template renders, `ansible.builtin.slurp` +
assert expected `index-url` line present, and the ini-parse check above.

## Wiring

- `playbooks/language-toolchains/pip_conf.yml`
- `test-molecule-pip-conf` + CI matrix

## Open questions

- Confirm whether a private index actually exists yet, or whether this
  playbook should ship pointed at plain PyPI as a placeholder until one does.
