# `cursor.yml` — Developer Applications

## Purpose

Install the Cursor IDE from an API-discovered `.deb` — Cursor doesn't
publish a stable apt repository the way Microsoft/Google do, so this role
has to hit their download API and install the resulting artifact directly.

## Platforms

Debian only for the API-download path (Darwin ships Cursor as a notarized
`.dmg`/Homebrew cask instead — lower priority, same pattern as vscode's
Darwin path if pursued).

## Task sequence

1. `ansible.builtin.uri`: GET Cursor's download API
   (`https://www.cursor.com/api/download?platform=linux-x64&releaseTrack=stable`),
   register the JSON response.
2. Compare the API's reported version against the currently installed
   version (`ansible.builtin.command: dpkg-query -W -f='${Version}' cursor`,
   `failed_when: false` so a not-yet-installed host doesn't fail the play).
3. Only if versions differ (or nothing installed): `get_url` the `.deb` from
   the API's `downloadUrl` to a temp path, `apt: deb=<path>`, then clean up
   the temp file (`ansible.builtin.file: state=absent`) so re-runs don't
   accumulate stale `.deb`s in `/tmp`.
4. `validate.yml`: confirm the installed version matches what the API
   reported.

## Safety notes

This role depends on an **undocumented, unversioned third-party API** —
Cursor could change the response shape or URL scheme without notice. Treat
the `uri` task's JSON parsing defensively (`ansible.builtin.assert` on the
expected keys existing before using them) so a schema change fails loudly
with a clear message instead of a cryptic KeyError deep in a Jinja
expression.

## Testing

Molecule scenario makes a real outbound call to Cursor's API and downloads a
real `.deb` — acceptable, but this is the one role in the roadmap whose CI
test can fail for reasons entirely outside this repo (Cursor API downtime or
a breaking response-shape change). Mark this explicitly in the Makefile
target's help text so a red CI run here isn't mistaken for a regression in
this repo.

## Wiring

- `playbooks/app-installers/cursor.yml`
- `test-molecule-cursor` + CI matrix (flagged as externally-dependent per above)

## Open questions

- Confirm the API endpoint/response shape at implementation time — Cursor
  doesn't document this contract publicly, so it should be verified with a
  live `curl` before writing the role, not assumed from memory.
