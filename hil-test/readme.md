# Hardware-in-the-loop testing

These procedures validate playbooks against explicitly designated physical
targets. They are manual, potentially destructive, and separate from static
tests and container-based Molecule scenarios. See
[`docs/testing.md`](../docs/testing.md) for the repository's verification
layers.

## Procedures

| Domain | Procedure | Final success state |
| --- | --- | --- |
| SSH provisioning | [`provisioning-ssh/readme.md`](provisioning-ssh/readme.md) | The complete provisioning workflow passes and the target accepts key-only SSH. |

Use only sanitized placeholders in HIL documentation and captured output. Never
commit a real hostname, username, password, SSH key name, private domain, vault,
token, or secret-item identifier.
