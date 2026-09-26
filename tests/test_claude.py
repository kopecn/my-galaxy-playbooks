"""Static contract checks for the Claude CLI playbook interface."""

import json
from pathlib import Path

import pytest
import yaml


REPO_ROOT = Path(__file__).resolve().parent.parent
OPERATIONS = ("diagnose", "install", "uninstall")


@pytest.mark.parametrize("operation", OPERATIONS)
def test_claude_operation_has_thin_playbook(operation):
    """Each public operation delegates to the Claude role."""
    playbook_path = REPO_ROOT / "playbooks" / f"claude_{operation}.yml"
    playbook = yaml.safe_load(playbook_path.read_text())

    assert len(playbook) == 1
    assert playbook[0]["roles"] == [
        {
            "role": "claude",
            "claudeOperation": operation,
        }
    ]


def test_uninstall_always_removes_user_config():
    """Uninstall purges user config unconditionally — no gating variable."""
    tasks = yaml.safe_load(
        (REPO_ROOT / "roles" / "claude" / "tasks" / "uninstall.yml").read_text()
    )
    config_task = next(
        task for task in tasks if task["name"] == "Remove the Claude Code user configuration"
    )

    assert "when" not in config_task
    assert config_task["loop"] == [
        "{{ claudeUserHome }}/.claude",
        "{{ claudeUserHome }}/.claude.json",
    ]

    schema = json.loads((REPO_ROOT / ".schema" / "ansible-vars.schema.json").read_text())
    assert "claudeRemoveConfig" not in schema["properties"]
