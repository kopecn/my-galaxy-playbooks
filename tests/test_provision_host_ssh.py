"""Static safety contracts for reusable host SSH provisioning operations."""

import json
from pathlib import Path

import pytest
import yaml


REPO_ROOT = Path(__file__).resolve().parent.parent
ROLE = REPO_ROOT / "roles" / "provision_host"
OPERATIONS = (
    "provision",
    "ensure_key",
    "install_key",
    "disable_password",
)


@pytest.mark.parametrize("operation", OPERATIONS)
def test_operation_has_a_thin_reusable_playbook(operation):
    """The full flow and every reusable phase remain thin role entry points."""
    suffix = "" if operation == "provision" else f"_{operation}"
    playbook = yaml.safe_load(
        (REPO_ROOT / "playbooks" / f"provision_host_ssh{suffix}.yml").read_text()
    )

    assert len(playbook) == 1
    assert playbook[0]["serial"] == 1
    assert playbook[0]["roles"] == [
        {"role": "1password_ssh_user_pass"},
        {"role": "ssh"},
        {
            "role": "provision_host",
            "provisionHostSshOperation": operation,
        }
    ]


def test_private_key_is_created_in_onepassword_and_not_on_the_host():
    """1Password creates the key; only the public half reaches authorized_keys."""
    ensure_tasks = (ROLE / "tasks" / "ensure_key.yml").read_text()
    install_tasks = (ROLE / "tasks" / "install_key.yml").read_text()

    assert "--category=SSH Key" in ensure_tasks
    assert "--ssh-generate-key=" in ensure_tasks
    assert "ansible.posix.authorized_key" in install_tasks
    assert "/public key" in install_tasks
    assert "/private key" not in install_tasks
    assert "exclusive: false" in install_tasks


def test_provisioning_reuses_the_shared_ssh_validator():
    """Provisioning consumes the SSH capability instead of duplicating it."""
    tasks = (ROLE / "tasks" / "validate_host_ssh_key.yml").read_text()

    assert "ansible.builtin.include_role" in tasks
    assert "name: ssh" in tasks
    assert 'sshHost: "{{ provisionHostSshHost }}"' in tasks
    assert 'sshKeyItemName: "{{ provisionHostSshItemName }}"' in tasks


def test_password_disable_revalidates_and_rolls_back_on_failure():
    """The standalone destructive phase has its own gate and recovery path."""
    disable_tasks = (ROLE / "tasks" / "disable_password.yml").read_text()
    harden_tasks = (ROLE / "tasks" / "harden_sshd.yml").read_text()

    assert disable_tasks.index("validate_host_ssh_key.yml") < disable_tasks.index("harden_sshd.yml")
    assert "PasswordAuthentication no" in harden_tasks
    assert "KbdInteractiveAuthentication no" in harden_tasks
    assert "/usr/sbin/sshd\n          - -t" in harden_tasks
    assert "Revalidate a fresh key-only session after SSH reload" in harden_tasks
    assert "rescue:" in harden_tasks
    assert "Restore the previous SSH daemon drop-in" in harden_tasks


def test_all_defaulted_variables_are_in_the_companion_schema():
    """Every public role default remains discoverable in inventory tooling."""
    defaults = yaml.safe_load((ROLE / "defaults" / "main.yml").read_text())
    schema = json.loads(
        (
            REPO_ROOT
            / ".schema"
            / "groups"
            / "provisionhostssh-schema.json"
        ).read_text()
    )
    root_schema = json.loads(
        (REPO_ROOT / ".schema" / "ansible-vars.schema.json").read_text()
    )

    role_variables = {key for key in defaults if key.startswith("provisionHostSsh")}
    assert role_variables <= set(schema["properties"])
    assert {
        "$ref": "groups/provisionhostssh-schema.json"
    } in root_schema["allOf"]
