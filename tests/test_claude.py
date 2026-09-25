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
    playbook_path = REPO_ROOT / "playbooks" / "core-platform" / f"claude-{operation}.yml"
    playbook = yaml.safe_load(playbook_path.read_text())

    assert len(playbook) == 1
    assert playbook[0]["vars_files"] == ["../../vars/defaults.yml"]
    assert playbook[0]["roles"] == [
        {
            "role": "claude",
            "claudeOperation": operation,
        }
    ]


def test_claude_remove_config_is_documented():
    """The uninstall config-purge flag remains discoverable in the schema."""
    schema_path = REPO_ROOT / ".schema" / "ansible-vars.schema.json"
    schema = json.loads(schema_path.read_text())

    assert "claudeRemoveConfig" in schema["properties"]
