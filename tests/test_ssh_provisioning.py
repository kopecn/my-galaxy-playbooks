"""Safety contracts for the local-key SSH provisioning workflow."""

import json
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parent.parent
ROLE = REPO_ROOT / "roles" / "ssh_provisioning"


def test_password_disable_is_gated_by_key_only_validation():
    """Password access cannot be disabled before the installed key is proven."""
    tasks = (ROLE / "tasks" / "disable_password.yml").read_text()

    assert tasks.index("sshProvisioningKeyValidated") < tasks.index(
        "PasswordAuthentication no"
    )
    assert "PasswordAuthentication=no" in (
        ROLE / "tasks" / "validate.yml"
    ).read_text()


def test_secure_playbook_runs_the_password_disable_operation():
    """The validate-and-secure entry point executes the complete final gate."""
    playbook = yaml.safe_load(
        (
            REPO_ROOT / "playbooks" / "provision-validate-and-secureSSH.yml"
        ).read_text()
    )

    assert playbook[0]["roles"][-1] == {
        "role": "ssh_provisioning",
        "sshProvisioningOperations": ["validate", "disable_password"],
    }


def test_role_dispatches_requested_operations_in_list_order():
    """Provisioning follows the repository's plural operation contract."""
    tasks = (ROLE / "tasks" / "main.yml").read_text()
    defaults = yaml.safe_load((ROLE / "defaults" / "main.yml").read_text())
    variables = yaml.safe_load((ROLE / "vars" / "main.yml").read_text())

    assert defaults["sshProvisioningOperations"] == []
    assert variables["sshProvisioningSupportedOperations"] == [
        "connect",
        "install_key",
        "validate",
        "disable_password",
    ]
    assert 'include_tasks: "{{ sshProvisioningOperation }}.yml"' in tasks
    assert 'loop: "{{ sshProvisioningOperations }}"' in tasks
    assert "loop_var: sshProvisioningOperation" in tasks


def test_install_playbook_requests_a_plural_operation_list():
    """The key-install entry point uses the ordered list interface."""
    playbook = yaml.safe_load(
        (REPO_ROOT / "playbooks" / "provision-installSSHKey.yml").read_text()
    )

    assert playbook[0]["roles"][-1] == {
        "role": "ssh_provisioning",
        "sshProvisioningOperations": ["connect", "install_key"],
    }


def test_all_role_defaults_are_in_the_companion_schema():
    """Every public provisioning default remains discoverable."""
    defaults = yaml.safe_load((ROLE / "defaults" / "main.yml").read_text())
    schema = json.loads(
        (
            REPO_ROOT / ".schema" / "groups" / "sshprovisioning-schema.json"
        ).read_text()
    )

    assert set(defaults) <= set(schema["properties"])
