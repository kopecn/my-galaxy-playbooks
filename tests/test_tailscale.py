"""Static contract checks for the Tailscale playbook interface."""

import json
from configparser import ConfigParser
from pathlib import Path

import pytest
import yaml


REPO_ROOT = Path(__file__).resolve().parent.parent
OPERATIONS = ("diagnose", "down", "install", "status", "uninstall", "up", "update")


@pytest.mark.parametrize("operation", OPERATIONS)
def test_tailscale_operation_has_thin_playbook(operation):
    """Each public operation delegates to the Tailscale role."""
    playbook_path = REPO_ROOT / "playbooks" / f"tailscale_{operation}.yml"
    playbook = yaml.safe_load(playbook_path.read_text())

    assert len(playbook) == 1
    assert playbook[0]["roles"] == [
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
    schema_path = REPO_ROOT / ".schema" / "ansible-vars.schema.json"
    schema = json.loads(schema_path.read_text())

    assert variable in schema["properties"]


def test_tailscale_auth_key_is_controller_managed():
    """The auth key and its reference never come from target inventory."""
    tasks = (REPO_ROOT / "roles" / "tailscale" / "tasks" / "up.yml").read_text()
    role_defaults = yaml.safe_load(
        (REPO_ROOT / "roles" / "tailscale" / "defaults" / "main.yml").read_text()
    )
    schema = json.loads(
        (REPO_ROOT / ".schema" / "ansible-vars.schema.json").read_text()
    )["properties"]

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


def test_become_password_is_inventory_or_cli_driven_not_a_repo_script():
    """The become password comes from downstream inventory (or -e at run time).
    This repo ships no op wrapper, no become-password provider script, and no
    controller-only vars file feeding one."""
    config = ConfigParser()
    config.read(REPO_ROOT / "ansible.cfg")

    # ansible.cfg no longer points privilege escalation at a provider script.
    assert "become_password_file" not in config["defaults"]
    # The op wrapper and the become-password script are gone.
    assert not (REPO_ROOT / "scripts" / "with-op").exists()
    assert not (REPO_ROOT / "scripts" / "op-become-password").exists()
    # The controller-only vars file that fed those scripts is gone.
    assert not (REPO_ROOT / "vars" / "defaults.yml").exists()
