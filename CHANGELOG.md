# Changelog

All notable changes to the `bergantz_galaxy.home` collection are documented here.

## 0.0.3

- Package the repository as the Ansible collection `bergantz_galaxy.home` (add
  `galaxy.yml`, `meta/runtime.yml`).
- Flatten playbooks to the collection top-level `playbooks/` directory and rename
  them to lowercase `_`-separated names so they are addressable downstream by
  fully-qualified collection name (`bergantz_galaxy.home.<name>`).
- Remove project-relative `vars_files` from playbooks; shared values now come
  from each role's `defaults/main.yml` and are overridden by the downstream
  inventory.
