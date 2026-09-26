"""Static contract checks for the Tailscale playbook interface."""

import json
import os
import subprocess
from configparser import ConfigParser
from pathlib import Path

import pytest
import yaml


REPO_ROOT = Path(__file__).resolve().parent.parent
OPERATIONS = ("diagnose", "down", "install", "status", "uninstall", "up", "update")
WITH_OP = REPO_ROOT / "scripts" / "with-op"
OP_BECOME_PASSWORD = REPO_ROOT / "scripts" / "op-become-password"


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


@pytest.mark.parametrize("token", [None, "", "\n"])
def test_with_op_blocks_invalid_service_account_token(tmp_path, token):
    """The wrapper fails clearly before executing without a usable token."""
    if token is not None:
        secrets_dir = tmp_path / ".config" / "op"
        secrets_dir.mkdir(parents=True)
        (secrets_dir / "op-service-account-token").write_text(token)

    result = subprocess.run(
        [WITH_OP, "true"],
        capture_output=True,
        check=False,
        env={**os.environ, "HOME": str(tmp_path)},
        text=True,
    )

    assert result.returncode != 0
    assert "op service account token has not been set up" in result.stderr


def test_with_op_exports_service_account_token(tmp_path):
    """The wrapper exports the token and replaces itself with the command."""
    secrets_dir = tmp_path / ".config" / "op"
    secrets_dir.mkdir(parents=True)
    token_file = secrets_dir / "op-service-account-token"
    token_file.write_text("test-service-account-token\n")

    result = subprocess.run(
        [WITH_OP, "bash", "-c", 'test "$OP_SERVICE_ACCOUNT_TOKEN" = "test-service-account-token"'],
        capture_output=True,
        check=False,
        env={**os.environ, "HOME": str(tmp_path)},
        text=True,
    )

    assert result.returncode == 0, result.stderr


def test_secret_reads_use_the_onepassword_role_not_the_makefile_wrapper():
    """Playbook secret reads resolve through the onepassword role; the Makefile no
    longer pipes every run through the op wrapper."""
    up_tasks = (REPO_ROOT / "roles" / "tailscale" / "tasks" / "up.yml").read_text()
    role_defaults = (REPO_ROOT / "roles" / "onepassword" / "defaults" / "main.yml").read_text()
    role_tasks = (REPO_ROOT / "roles" / "onepassword" / "tasks" / "main.yml").read_text()
    makefile = (REPO_ROOT / "Makefile").read_text()

    # The consuming role no longer shells the wrapper or handles the raw token.
    assert "with-op" not in up_tasks
    assert "OP_SERVICE_ACCOUNT_TOKEN" not in up_tasks
    # The onepassword role is the single place secret reads load the controller token.
    assert "${HOME}/.config/op/op-service-account-token" in WITH_OP.read_text()
    assert ".config/op/op-service-account-token" in role_defaults
    assert "community.general.onepassword" in role_tasks
    # The Makefile run target no longer wraps ansible-playbook in the op token.
    assert "WITH_OP" not in makefile
    assert "run: ## Apply the playbook" in makefile


def test_become_password_path_still_self_wraps_the_token():
    """The become-password path is unchanged and keeps its own wrapper (handled next)."""
    op_become = OP_BECOME_PASSWORD.read_text()

    assert "with-op" in op_become
    assert "vars/defaults.yml" in op_become
    assert "onePasswordVault" in op_become


def test_tailscale_status_prints_diagnostics():
    """The status operation reports both connection and network diagnostics."""
    tasks_path = REPO_ROOT / "roles" / "tailscale" / "tasks" / "status.yml"
    tasks = tasks_path.read_text()

    assert "tailscale status" in tasks
    assert "tailscale netcheck" in tasks
    assert tasks.count("ansible.builtin.debug:") == 2


def test_become_password_uses_global_provider(tmp_path):
    """Privilege escalation resolves independently of the inventory source."""
    config = ConfigParser()
    config.read(REPO_ROOT / "ansible.cfg")

    assert config["defaults"]["become_password_file"] == "scripts/op-become-password"

    secrets_dir = tmp_path / ".config" / "op"
    secrets_dir.mkdir(parents=True)
    (secrets_dir / "op-service-account-token").write_text("test-service-account-token\n")

    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    fake_op = bin_dir / "op"
    fake_op.write_text("#!/usr/bin/env bash\nprintf 'test`sudo-password'\n")
    fake_op.chmod(0o755)

    result = subprocess.run(
        [OP_BECOME_PASSWORD],
        capture_output=True,
        check=False,
        env={
            **os.environ,
            "HOME": str(tmp_path),
            "PATH": f"{bin_dir}:{os.environ['PATH']}",
        },
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout == "test`sudo-password"
