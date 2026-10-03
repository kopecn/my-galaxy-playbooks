"""Static contract checks for the Claude CLI playbook interface."""

import json
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parent.parent
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
