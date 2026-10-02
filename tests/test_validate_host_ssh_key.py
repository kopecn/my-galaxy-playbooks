"""Static contracts for the minimal SSH credential and routing framework."""

import json
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
SSH_ROLE = REPO_ROOT / "roles" / "ssh"
ONEPASSWORD_ROLE = REPO_ROOT / "roles" / "onepassword"


def test_onepassword_queries_use_only_the_short_hostname():
    defaults = (ONEPASSWORD_ROLE / "defaults" / "main.yml").read_text()

    assert "sshKeyPrefix" in defaults
    assert "sshLoginPrefix" in defaults
    assert ".split('.')[0]" in defaults
    assert "/username" in defaults
    assert "/password" in defaults
    assert "private key?ssh-format=openssh" in defaults


def test_every_remote_playbook_runs_credentials_then_router():
    for path in sorted((REPO_ROOT / "playbooks").glob("*.yml")):
        play = yaml.safe_load(path.read_text())[0]
        role_names = [
            role if isinstance(role, str) else role["role"] for role in play["roles"]
        ]
        assert play["gather_facts"] is False, path.name
        assert role_names[0] == "onepassword", path.name
        assert role_names[1] == "ssh", path.name
        expected_tasks = ["ssh_user_pass"]
        if path.name == "samba_install.yml":
            expected_tasks.append("samba")
        if path.name == "tailscale_up.yml":
            expected_tasks.append("tailscale")
        assert play["roles"][0]["onePasswordTasks"] == expected_tasks, path.name


def test_router_preserves_inline_inventory_and_prioritizes_vpn():
    tasks = (SSH_ROLE / "tasks" / "resolve.yml").read_text()

    assert tasks.index("useVpn | bool") < tasks.index("',' in inventory_file")
    assert "{{ inventory_hostname }}" in tasks
    assert "hostName ~ '.local'" in tasks
    assert "vpnHostname ~ '.' ~ vpnDomain" in tasks


def test_router_rejects_ambiguous_bare_inline_targets():
    tasks = (SSH_ROLE / "tasks" / "resolve.yml").read_text()

    assert "Reject ambiguous bare inline SSH targets" in tasks
    assert "or '.' in inventory_hostname" in tasks
    assert "or ':' in inventory_hostname" in tasks
    assert "Inline inventory target" in tasks


def test_router_ignores_dot_ssh_config_and_control_sockets():
    tasks = (SSH_ROLE / "tasks" / "resolve.yml").read_text()

    assert "-F /dev/null" in tasks
    assert "UserKnownHostsFile=/dev/null" in tasks
    assert "GlobalKnownHostsFile=/dev/null" in tasks
    assert "ControlMaster=no" in tasks
    assert "ControlPath=none" in tasks


def test_router_dispatches_ordered_operations_with_resolve_as_default():
    tasks = (SSH_ROLE / "tasks" / "main.yml").read_text()
    defaults = yaml.safe_load((SSH_ROLE / "defaults" / "main.yml").read_text())

    assert defaults["sshOperations"] == ["resolve"]
    assert 'include_tasks: "{{ sshOperation }}.yml"' in tasks
    assert 'loop: "{{ sshOperations }}"' in tasks
    assert "loop_var: sshOperation" in tasks
    assert (SSH_ROLE / "tasks" / "resolve.yml").is_file()


def test_all_ssh_role_defaults_are_in_the_ssh_schema():
    defaults = yaml.safe_load((SSH_ROLE / "defaults" / "main.yml").read_text())
    schema = json.loads(
        (REPO_ROOT / ".schema" / "groups" / "ssh-schema.json").read_text()
    )

    assert set(defaults) <= set(schema["properties"])
