"""Static contract checks for the Tailscale playbook interface."""

import json
import os
import subprocess
from configparser import ConfigParser
from pathlib import Path

import pytest
import yaml


REPO_ROOT = Path(__file__).resolve().parent.parent
OPERATIONS = ("install", "status", "uninstall", "up", "update")
WITH_OP = REPO_ROOT / "scripts" / "with-op"
OP_BECOME_PASSWORD = REPO_ROOT / "scripts" / "op-become-password"


@pytest.mark.parametrize("operation", OPERATIONS)
def test_tailscale_operation_has_thin_playbook(operation):
    """Each public operation delegates to the Tailscale role."""
    playbook_path = REPO_ROOT / "playbooks" / "core-platform" / f"tailscale-{operation}.yml"
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
        "tailscaleAuthKeyReference",
        "tailscaleVersion",
    ),
)
def test_tailscale_cli_variables_are_documented(variable):
    """CLI inputs remain discoverable in the inventory variable schema."""
    schema_path = REPO_ROOT / ".schema" / "ansible-vars.schema.json"
    schema = json.loads(schema_path.read_text())

    assert variable in schema["properties"]


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


def test_op_authentication_has_one_entry_point():
    """Token loading stays in the wrapper and make run uses that entry point."""
    tasks_path = REPO_ROOT / "roles" / "tailscale" / "tasks" / "up.yml"
    tasks = tasks_path.read_text()
    makefile = (REPO_ROOT / "Makefile").read_text()

    assert "op-service-account-token" not in tasks
    assert "OP_SERVICE_ACCOUNT_TOKEN" not in tasks
    assert "WITH_OP := scripts/with-op" in makefile
    assert "$(WITH_OP) ansible-playbook $(ANSIBLE_PLAYBOOK_OPTS) $(PLAYBOOK)" in makefile
    assert "${HOME}/.config/op/op-service-account-token" in WITH_OP.read_text()


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

    group_vars_path = REPO_ROOT / "inventories" / "production" / "group_vars" / "all.yml"
    group_vars = yaml.safe_load(group_vars_path.read_text())
    assert "ansible_become_pass" not in group_vars
    assert "onePasswordHostSudoPassword" not in group_vars

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
