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


def test_tailscale_has_one_operation_driven_playbook():
    """One public playbook delegates an ordered operation list to the role."""
    playbook_path = REPO_ROOT / "playbooks" / "tailscale.yml"
    playbook = yaml.safe_load(playbook_path.read_text())

    assert len(playbook) == 1
    assert playbook[0]["serial"] == 1
    roles = playbook[0]["roles"]
    assert [role["role"] for role in roles] == [
        "set_facts",
        "onepassword",
        "ssh",
        "tailscale",
    ]
    assert "tailscaleOperations" in roles[1]["onePasswordTasks"]
    assert "'up' in tailscaleOperations" in roles[1]["onePasswordTasks"]
    assert set((REPO_ROOT / "playbooks").glob("tailscale_*.yml")) == set()


def test_tailscale_role_validates_and_loops_over_operation_array():
    """The public array is validated against the enum and dispatched in order."""
    tasks = (REPO_ROOT / "roles" / "tailscale" / "tasks" / "main.yml").read_text()
    defaults = yaml.safe_load(
        (REPO_ROOT / "roles" / "tailscale" / "defaults" / "main.yml").read_text()
    )
    variables = yaml.safe_load(
        (REPO_ROOT / "roles" / "tailscale" / "vars" / "main.yml").read_text()
    )

    assert defaults["tailscaleOperations"] == []
    assert variables["tailscaleSupportedOperations"] == list(OPERATIONS)
    assert "tailscaleOperations is sequence" in tasks
    assert "tailscaleOperations is not string" in tasks
    assert "tailscaleOperations | length > 0" in tasks
    assert "difference(tailscaleSupportedOperations)" in tasks
    assert 'include_tasks: "{{ tailscaleOperation }}.yml"' in tasks
    assert 'loop: "{{ tailscaleOperations }}"' in tasks
    assert "loop_var: tailscaleOperation" in tasks


@pytest.mark.parametrize(
    "variable",
    (
        "tailscaleAuthKeyItem",
        "tailscaleOperations",
        "onePasswordVault",
        "tailscaleVersion",
    ),
)
def test_tailscale_cli_variables_are_documented(variable):
    """CLI inputs remain discoverable in the inventory variable schema."""
    assert variable in _documented_variables()


def test_tailscale_auth_key_is_super_agent_managed():
    """The auth key and its reference never come from target inventory."""
    tasks = (REPO_ROOT / "roles" / "tailscale" / "tasks" / "up.yml").read_text()
    role_defaults = yaml.safe_load(
        (REPO_ROOT / "roles" / "tailscale" / "defaults" / "main.yml").read_text()
    )
    credential_defaults = (
        REPO_ROOT / "roles" / "onepassword" / "defaults" / "main.yml"
    ).read_text()
    schema = _documented_variables()
    playbook = yaml.safe_load(
        (REPO_ROOT / "playbooks" / "tailscale.yml").read_text()
    )

    assert "tailscaleAuthKeyReference" not in tasks
    assert "ansible.builtin.include_role" not in tasks
    assert "['ssh_user_pass', 'tailscale']" in playbook[0]["roles"][1][
        "onePasswordTasks"
    ]
    assert "with-op" not in tasks
    assert "{{ onePasswordVault }}" in credential_defaults
    assert "{{ tailscaleAuthKeyItem }}" in credential_defaults
    assert "tailscaleAuthKeyItem" in role_defaults
    assert "," not in role_defaults["tailscaleAuthKeyItem"]
    assert "tailscaleAuthKey" not in role_defaults
    assert "onePasswordVault:" in credential_defaults
    for variable in ("onePasswordVault", "tailscaleAuthKeyItem"):
        assert variable in schema


def test_secret_reads_use_the_onepassword_role_not_a_wrapper():
    """Secret reads resolve through the onepassword role on the super agent; no
    wrapper script and no raw token env remain in the consuming role."""
    up_tasks = (REPO_ROOT / "roles" / "tailscale" / "tasks" / "up.yml").read_text()
    role_defaults = (
        REPO_ROOT / "roles" / "onepassword" / "defaults" / "main.yml"
    ).read_text()
    role_tasks = (
        REPO_ROOT / "roles" / "onepassword" / "tasks" / "read_queries.yml"
    ).read_text()
    makefile = (REPO_ROOT / "Makefile").read_text()

    assert "with-op" not in up_tasks
    assert "OP_SERVICE_ACCOUNT_TOKEN" not in up_tasks
    assert ".config/op/op-service-account-token" in role_defaults
    assert "op_queries" in role_tasks
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


def test_become_password_is_loaded_by_the_ssh_credential_role():
    """Operational playbooks receive sudo credentials from the host Login item."""
    config = ConfigParser()
    config.read(REPO_ROOT / "ansible.cfg")
    credential_tasks = (
        REPO_ROOT / "roles" / "onepassword" / "tasks" / "ssh_user_pass.yml"
    ).read_text()

    assert "become_password_file" not in config["defaults"]
    assert "ansible_become_password:" in credential_tasks
    assert not (REPO_ROOT / "scripts" / "with-op").exists()
    assert not (REPO_ROOT / "scripts" / "op-become-password").exists()
    assert not (REPO_ROOT / "vars" / "defaults.yml").exists()
