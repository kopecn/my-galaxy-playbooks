"""Static contract checks for the LM Studio playbook interface."""

from pathlib import Path

import pytest
import yaml


REPO_ROOT = Path(__file__).resolve().parent.parent
OPERATIONS = ("diagnose", "install", "uninstall")


@pytest.mark.parametrize("operation", OPERATIONS)
def test_lm_studio_operation_has_thin_playbook(operation):
    """Each public operation resolves SSH before invoking the LM Studio role."""
    playbook_path = REPO_ROOT / "playbooks" / f"lm_studio_{operation}.yml"
    playbook = yaml.safe_load(playbook_path.read_text())

    assert len(playbook) == 1
    assert playbook[0]["gather_facts"] is False
    assert playbook[0]["roles"] == [
        {"role": "set_facts"},
        {
            "role": "onepassword",
            "onePasswordTasks": ["ssh_user_pass"],
        },
        {"role": "ssh"},
        {
            "role": "lm_studio",
            "lmStudioOperation": operation,
        },
    ]


def test_lm_studio_gathers_platform_facts_after_ssh_setup():
    """The role gathers facts once credentials and the SSH route are available."""
    tasks_path = REPO_ROOT / "roles" / "lm_studio" / "tasks" / "main.yml"
    tasks = yaml.safe_load(tasks_path.read_text())

    setup_index = next(
        index for index, task in enumerate(tasks) if "ansible.builtin.setup" in task
    )
    architecture_index = next(
        index
        for index, task in enumerate(tasks)
        if "ansible_facts.architecture" in str(task)
    )

    assert setup_index < architecture_index
    assert tasks[setup_index]["ansible.builtin.setup"]["gather_subset"] == ["min"]
