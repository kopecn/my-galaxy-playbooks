"""Static contract checks for Samba super-agent-side secret resolution.

Both the Samba username and password resolve on the super agent through the
shared onepassword role rather than a hand-built op read via scripts/with-op.
"""

from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parent.parent
INSTALL = REPO_ROOT / "roles" / "samba" / "tasks" / "install-Debian.yml"


def test_samba_secrets_resolve_through_the_onepassword_role():
    tasks = INSTALL.read_text()
    query_defaults = (
        REPO_ROOT / "roles" / "onepassword" / "defaults" / "main.yml"
    ).read_text()
    playbook = yaml.safe_load(
        (REPO_ROOT / "playbooks" / "samba_install.yml").read_text()
    )

    assert "ansible.builtin.include_role" not in tasks
    assert playbook[0]["roles"][1]["onePasswordTasks"] == [
        "ssh_user_pass",
        "samba",
    ]
    assert "sambaUsername:" in query_defaults
    assert "sambaEffectivePassword:" in query_defaults
    # Keyed on the documented inputs.
    assert "{{ sambaPasswordOpItem }}" in query_defaults
    assert "{{ onePasswordVault }}" in query_defaults


def test_samba_has_no_wrapper_or_hand_built_op_read():
    tasks = INSTALL.read_text()

    assert "with-op" not in tasks
    assert "op --version" not in tasks
    assert "op://" not in tasks
