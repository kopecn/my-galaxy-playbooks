"""Static safety contracts for the hardware-validated SSH provisioning flow."""

import json
from pathlib import Path

import pytest
import yaml


REPO_ROOT = Path(__file__).resolve().parent.parent
ROLE = REPO_ROOT / "roles" / "ssh_provisioning"
PLAYBOOK_OPERATIONS = {
    "provision-full.yml": [
        "connect",
        "install_key",
        "validate",
        "disable_password",
    ],
    "provision-installSSHKey.yml": ["connect", "install_key"],
    "provision-validate-and-secureSSH.yml": ["validate", "disable_password"],
}


@pytest.mark.parametrize(("playbook_name", "operations"), PLAYBOOK_OPERATIONS.items())
def test_provisioning_playbooks_use_the_ordered_role_interface(
    playbook_name, operations
):
    """Each validated provisioning entry point remains a thin role pipeline."""
    playbook = yaml.safe_load(
        (REPO_ROOT / "playbooks" / playbook_name).read_text()
    )

    assert len(playbook) == 1
    assert playbook[0]["gather_facts"] is False
    assert playbook[0]["roles"] == [
        {"role": "set_facts"},
        {"role": "ssh"},
        {
            "role": "ssh_provisioning",
            "sshProvisioningOperations": operations,
        },
    ]


def test_private_key_stays_local_and_only_the_public_key_reaches_the_host():
    """Generated key material is local; authorized_keys receives only the public key."""
    tasks = (ROLE / "tasks" / "install_key.yml").read_text()

    assert "delegate_to: localhost" in tasks
    assert "ssh-keygen" in tasks
    assert "ansible.posix.authorized_key" in tasks
    assert "sshExistingPublicKey.stdout" in tasks
    assert "sshFileName ~ '.pub'" in tasks
    assert 'mode: "0600"' in tasks
    assert "Remove the temporary keypair directory" in tasks


def test_password_authentication_failure_is_reported_without_exposing_secrets():
    """A rejected bootstrap password produces a specific, redacted failure."""
    tasks = (ROLE / "tasks" / "connect.yml").read_text()

    assert "register: sshProvisioningCredentialCheck" in tasks
    assert "ignore_unreachable: true" in tasks
    assert "'permission denied'" in tasks
    assert "SSH authentication was rejected" in tasks
    assert "Verify the supplied sshProvisioningUsername and sshProvisioningPassword" in tasks
    assert "The password value remains redacted." in tasks
    assert tasks.index("SSH authentication was rejected") < tasks.index(
        "Could not establish SSH"
    )


def test_validation_forces_a_fresh_key_only_connection():
    """The validation gate cannot silently fall back to password authentication."""
    tasks = (ROLE / "tasks" / "validate.yml").read_text()

    assert "PreferredAuthentications=publickey" in tasks
    assert "IdentitiesOnly=yes" in tasks
    assert "PasswordAuthentication=no" in tasks
    assert "BatchMode=yes" in tasks
    assert "Validate that the installed key authenticates" in tasks
    assert "sshProvisioningKeyValidated: true" in tasks


def test_password_disable_is_gated_and_rolls_back_on_failure():
    """Lock-down requires validation and restores sshd_config after any failure."""
    tasks = (ROLE / "tasks" / "disable_password.yml").read_text()

    assert tasks.index("sshProvisioningKeyValidated") < tasks.index(
        "PasswordAuthentication no"
    )
    assert "KbdInteractiveAuthentication no" in tasks
    assert "validate: /usr/sbin/sshd -t -f %s" in tasks
    assert "Read the effective SSH daemon configuration" in tasks
    assert "rescue:" in tasks
    assert "Restore the previous SSH daemon configuration" in tasks
    assert "Reload the restored SSH daemon configuration" in tasks


def test_all_defaulted_variables_are_in_the_companion_schema():
    """Every public role default remains discoverable in inventory tooling."""
    defaults = yaml.safe_load((ROLE / "defaults" / "main.yml").read_text())
    schema = json.loads(
        (REPO_ROOT / ".schema" / "groups" / "sshprovisioning-schema.json").read_text()
    )

    assert set(defaults) <= set(schema["properties"])
