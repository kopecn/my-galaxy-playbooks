"""Static contract checks for the Tailscale playbook interface."""

import json
from configparser import ConfigParser
from pathlib import Path

import pytest
import yaml


REPO_ROOT = Path(__file__).resolve().parent.parent
OPERATIONS = ("diagnose", "down", "install", "status", "uninstall", "up", "update")


def _documented_variables():
    """Return root and composed group properties from the variable schema."""
    schema_root = REPO_ROOT / ".schema"
    root = json.loads((schema_root / "ansible-vars.schema.json").read_text())
    properties = dict(root["properties"])
    for reference in root["allOf"]:
        group = json.loads((schema_root / reference["$ref"]).read_text())
        properties.update(group["properties"])
    return properties


@pytest.mark.parametrize("operation", OPERATIONS)
def test_tailscale_operation_has_thin_playbook(operation):
    """Each public operation delegates to the Tailscale role."""
    playbook_path = REPO_ROOT / "playbooks" / f"tailscale_{operation}.yml"
    playbook = yaml.safe_load(playbook_path.read_text())

    assert len(playbook) == 1
    assert playbook[0]["roles"] == [
        {
            "role": "ssh",
            "sshOperation": "prepare_key_connection",
        },
        {
            "role": "tailscale",
            "tailscaleOperation": operation,
        }
    ]


@pytest.mark.parametrize(
    "variable",
    (
        "onePasswordTailscaleAPIKey",
        "onePasswordVault",
        "tailscaleVersion",
    ),
)
def test_tailscale_cli_variables_are_documented(variable):
    """CLI inputs remain discoverable in the inventory variable schema."""
    assert variable in _documented_variables()


def test_tailscale_auth_key_is_controller_managed():
    """The auth key and its reference never come from target inventory."""
    tasks = (REPO_ROOT / "roles" / "tailscale" / "tasks" / "up.yml").read_text()
    role_defaults = yaml.safe_load(
        (REPO_ROOT / "roles" / "tailscale" / "defaults" / "main.yml").read_text()
    )
    schema = _documented_variables()

    assert "tailscaleAuthKeyReference" not in tasks
    assert "hostvars['localhost']" not in tasks
    # Secret resolution is delegated to the shared, controller-side onepassword role.
    assert "name: onepassword" in tasks
    assert "tailscaleAuthKey:" in tasks
    assert "with-op" not in tasks
    assert "{{ onePasswordVault }}" in tasks
    assert "{{ onePasswordTailscaleAPIKey }}" in tasks
    for variable in ("onePasswordVault", "onePasswordTailscaleAPIKey"):
        assert variable in role_defaults
        assert variable in schema


def test_secret_reads_use_the_onepassword_role_not_a_wrapper():
    """Secret reads resolve through the onepassword role on the controller; no
    wrapper script and no raw token env remain in the consuming role."""
    up_tasks = (REPO_ROOT / "roles" / "tailscale" / "tasks" / "up.yml").read_text()
    role_defaults = (REPO_ROOT / "roles" / "onepassword" / "defaults" / "main.yml").read_text()
    role_tasks = (REPO_ROOT / "roles" / "onepassword" / "tasks" / "main.yml").read_text()
    makefile = (REPO_ROOT / "Makefile").read_text()

    assert "with-op" not in up_tasks
    assert "OP_SERVICE_ACCOUNT_TOKEN" not in up_tasks
    assert ".config/op/op-service-account-token" in role_defaults
    assert "community.general.onepassword" in role_tasks
    # The Makefile carries no op wrapper and no apply (`run`) target.
    assert "WITH_OP" not in makefile
    assert "run: ## Apply the playbook" not in makefile


def test_tailscale_status_prints_diagnostics():
    """The status operation reports both connection and network diagnostics."""
    tasks_path = REPO_ROOT / "roles" / "tailscale" / "tasks" / "status.yml"
    tasks = tasks_path.read_text()

    assert "tailscale status" in tasks
    assert "tailscale netcheck" in tasks
    assert tasks.count("ansible.builtin.debug:") == 2


def test_become_password_is_loaded_by_the_shared_ssh_role():
    """Operational playbooks receive sudo credentials from the host Login item."""
    config = ConfigParser()
    config.read(REPO_ROOT / "ansible.cfg")
    ssh_tasks = (
        REPO_ROOT / "roles" / "ssh" / "tasks" / "prepare_connection.yml"
    ).read_text()

    assert "become_password_file" not in config["defaults"]
    assert "ansible_become_password:" in ssh_tasks
    assert "sshConnectionLoadBecomePassword" in ssh_tasks
    assert not (REPO_ROOT / "scripts" / "with-op").exists()
    assert not (REPO_ROOT / "scripts" / "op-become-password").exists()
    assert not (REPO_ROOT / "vars" / "defaults.yml").exists()
