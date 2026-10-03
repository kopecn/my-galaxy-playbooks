# Ollama

Installs, uninstalls, and diagnoses the [Ollama](https://ollama.com) local-LLM
server, and opens its API port in the host firewall. See
[`roles/ollama`](../../roles/ollama) and the
[Playbook Layering spec](../../.claude/specs/architecture/playbook-layering.md)
for the layering this role follows.

The single thin playbook `playbooks/ollama.yml` accepts an ordered, non-empty
`ollamaOperations` array at runtime and dispatches each operation in order:

| Operation | Result |
| --- | --- |
| `install` | Install Ollama and open its API firewall port |
| `diagnose` | Print `ollama --version` and `ollama list` |
| `uninstall` | Uninstall Ollama and remove its firewall rule |

## Supported hosts

| OS family | Architectures |
| --- | --- |
| Darwin | `x86_64`, `arm64` |
| Debian | `x86_64`, `aarch64` |

Install channel per OS family: the official `ollama.com/install.sh` script on
Debian (installs `/usr/local/bin/ollama` and the `ollama` systemd service), the
Homebrew formula + `brew services` on Darwin. A host outside this matrix fails the
operation with a clear error; other hosts and playbooks continue.

## Variables

| Variable | Where set | Purpose |
| --- | --- | --- |
| `ollamaOperations` | Required `-e` argument; empty role default | Ordered, non-empty array containing `diagnose`, `install`, and/or `uninstall`. |
| `ollamaPort` | Role default (`roles/ollama/defaults/main.yml`), overridden by downstream inventory or `-e` | TCP port the Ollama API listens on and that the firewall rule opens. Defaults to `11434`. |

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
ansible-playbook playbooks/ollama.yml -i '<host-or-ip>,' -b \
  -e onePasswordVault=Personal-Automation \
  -e '{"ollamaOperations":["install"]}'
```

Diagnose without changing the host:

```bash
ansible-playbook playbooks/ollama.yml -i '<host-or-ip>,' -b \
  -e onePasswordVault=Personal-Automation \
  -e '{"ollamaOperations":["diagnose"]}'
```

Uninstall Ollama:

```bash
ansible-playbook playbooks/ollama.yml -i '<host-or-ip>,' -b \
  -e onePasswordVault=Personal-Automation \
  -e '{"ollamaOperations":["uninstall"]}'
```

Multiple values run in order, for example
`-e '{"ollamaOperations":["install","diagnose"]}'`.

## Verification

```bash
make test-molecule-ollama
```

The Molecule scenario exercises the Debian install path only (Docker has no macOS
image): it asserts the binary installs, `ollama --version` responds, the service
is running and enabled, and the UFW rule for `11434` is present. The macOS path is
verified manually on a Darwin host.
