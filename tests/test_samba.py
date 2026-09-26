"""Static contract checks for Samba controller-side secret resolution.

Both the Samba username and password resolve on the controller through the
shared onepassword role rather than a hand-built op read via scripts/with-op.
"""

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
INSTALL = REPO_ROOT / "roles" / "samba" / "tasks" / "install-Debian.yml"


def test_samba_secrets_resolve_through_the_onepassword_role():
    tasks = INSTALL.read_text()

    assert "name: onepassword" in tasks
    # Username and password are requested as op_secrets facts.
    assert "sambaUsername:" in tasks
    assert "sambaEffectivePassword:" in tasks
    # Keyed on the documented inputs.
    assert "{{ sambaPasswordOpItem }}" in tasks
    assert "{{ onePasswordVault }}" in tasks


def test_samba_has_no_wrapper_or_hand_built_op_read():
    tasks = INSTALL.read_text()

    assert "with-op" not in tasks
    assert "op --version" not in tasks
    assert "op://" not in tasks
