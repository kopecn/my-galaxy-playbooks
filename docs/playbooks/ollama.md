# Ollama

Installs, uninstalls, and diagnoses the [Ollama](https://ollama.com) local-LLM
server, and opens its API port in the host firewall. See
[`roles/ollama`](../../roles/ollama) and the
[Playbook Layering spec](../../.claude/specs/architecture/playbook-layering.md)
for the layering this role follows.

One thin playbook per operation, all dispatching into the same role via
`ollamaOperation`:

| Playbook | Operation |
| --- | --- |
| `playbooks/ollama_install.yml` | `install` |
| `playbooks/ollama_diagnose.yml` | `diagnose` — print `ollama --version` and `ollama list` |
| `playbooks/ollama_uninstall.yml` | `uninstall` |

## Supported hosts

| OS family | Architectures |
| --- | --- |
| Darwin | `x86_64`, `aarch64` |
| Debian | `x86_64`, `aarch64` |

Install channel per OS family: the official `ollama.com/install.sh` script on
Debian (installs `/usr/local/bin/ollama` and the `ollama` systemd service), the
Homebrew formula + `brew services` on Darwin. A host outside this matrix fails the
operation with a clear error; other hosts and playbooks continue.

## Variables

| Variable | Where set | Purpose |
| --- | --- | --- |
| `ollamaPort` | Role default (`roles/ollama/defaults/main.yml`), overridden by downstream inventory or `-e` | TCP port the Ollama API listens on and that the firewall rule opens. Defaults to `11434`. |
| `hostOperatingSystem`, `hostArchitecture` | `host_vars` | Optional declared OS/arch; validated against gathered facts before dispatch. |

Full descriptions: [`.schema/ansible-vars.schema.json`](../../.schema/ansible-vars.schema.json).

## Firewall and serving

`install` opens `ollamaPort` through the host firewall via the shared
[`firewall`](../../roles/firewall) role: on Linux it adds a UFW `allow` rule when
UFW is present (no-op otherwise); macOS is a no-op, as its application firewall is
managed manually. `uninstall` removes the same rule.

Opening the port only makes Ollama reachable once it also binds beyond localhost.
By default Ollama listens on `127.0.0.1:11434`. Binding it to the LAN
(`OLLAMA_HOST=0.0.0.0:11434` in the systemd unit on Linux, or via `launchctl
setenv` on macOS) is a deliberate manual step and is out of this role's scope.

## Usage

```bash
ansible-playbook playbooks/ollama_install.yml \
  -i '<host-or-ip>,' -e onePasswordVault=Personal-Automation
```

Swap `ollama_install.yml` for `ollama_diagnose.yml` or `ollama_uninstall.yml` to
run the other operations.

## Verification

```bash
make test-molecule-ollama
```

The Molecule scenario exercises the Debian install path only (Docker has no macOS
image): it asserts the binary installs, `ollama --version` responds, the service
is running and enabled, and the UFW rule for `11434` is present. The macOS path is
verified manually on a Darwin host.
