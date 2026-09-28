"""Static contracts for the minimal SSH credential and routing framework."""

import json
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parent.parent
SSH_ROLE = REPO_ROOT / "roles" / "ssh"
SSH_CREDENTIAL_ROLE = REPO_ROOT / "roles" / "1password_ssh_user_pass"


def test_validation_playbook_uses_the_shared_credential_and_router_roles():
    playbook = yaml.safe_load(
        (REPO_ROOT / "playbooks" / "validate_host_ssh_key.yml").read_text()
    )

    assert len(playbook) == 1
    assert playbook[0]["gather_facts"] is False
    assert playbook[0]["serial"] == 1
    assert playbook[0]["roles"] == [
        {"role": "1password_ssh_user_pass"},
        {"role": "ssh"},
    ]


def test_onepassword_queries_use_only_the_short_hostname():
    defaults = (SSH_CREDENTIAL_ROLE / "defaults" / "main.yml").read_text()

    assert "sshKeyPrefix" in defaults
    assert "sshLoginPrefix" in defaults
    assert ".split('.')[0]" in defaults
    assert "/username" in defaults
    assert "/password" in defaults
    assert "private key?ssh-format=openssh" in defaults


def test_every_remote_playbook_runs_credentials_then_router():
    for path in sorted((REPO_ROOT / "playbooks").glob("*.yml")):
        play = yaml.safe_load(path.read_text())[0]
        assert play["gather_facts"] is False, path.name
        assert play["roles"][0] == {"role": "1password_ssh_user_pass"}, path.name
        assert play["roles"][1] == {"role": "ssh"}, path.name


def test_router_preserves_inline_inventory_and_prioritizes_vpn():
    tasks = (SSH_ROLE / "tasks" / "main.yml").read_text()

    assert tasks.index("useVpn | bool") < tasks.index("',' in inventory_file")
    assert "{{ inventory_hostname }}" in tasks
    assert "{{ hostName }}.local" in tasks
    assert "{{ vpnHostname }}.{{ vpnDomain }}" in tasks


def test_router_ignores_dot_ssh_config_and_control_sockets():
    tasks = (SSH_ROLE / "tasks" / "main.yml").read_text()

    assert "-F /dev/null" in tasks
    assert "UserKnownHostsFile=/dev/null" in tasks
    assert "GlobalKnownHostsFile=/dev/null" in tasks
    assert "ControlMaster=no" in tasks
    assert "ControlPath=none" in tasks


def test_all_ssh_role_defaults_are_in_the_ssh_schema():
    defaults = yaml.safe_load((SSH_ROLE / "defaults" / "main.yml").read_text())
    schema = json.loads(
        (REPO_ROOT / ".schema" / "groups" / "ssh-schema.json").read_text()
    )

    assert set(defaults) <= set(schema["properties"])
