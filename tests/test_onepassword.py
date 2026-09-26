"""Static contract checks for the controller-side onepassword role.

The role resolves requested op:// secrets on the Ansible controller via the
upstream community.general.onepassword lookup and sets each result as a fact.
It replaces the per-role scripts/with-op invocations for secret reads.
"""

from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parent.parent
ROLE = REPO_ROOT / "roles" / "onepassword"


def test_role_resolves_secrets_via_upstream_lookup_and_token_file():
    """Secrets come from the community.general lookup, authed by the token file."""
    tasks = (ROLE / "tasks" / "main.yml").read_text()
    defaults = yaml.safe_load((ROLE / "defaults" / "main.yml").read_text())

    assert "community.general.onepassword" in tasks
    assert "op_token_file" in defaults
    assert ".config/op/op-service-account-token" in defaults["op_token_file"]
    assert "lookup('ansible.builtin.file', op_token_file)" in tasks


def test_role_uses_none_for_optional_section_never_omit():
    """default(omit) makes the lookup silently return an empty secret; None does not."""
    tasks = (ROLE / "tasks" / "main.yml").read_text()

    assert "section=(item.value.section | default(None))" in tasks
    assert "default(omit)" not in tasks


def test_role_never_logs_secrets_or_reimplements_the_wrapper():
    """Resolved values are no_log, and the role holds no wrapper or raw token env."""
    tasks = (ROLE / "tasks" / "main.yml").read_text()

    assert "no_log: true" in tasks
    assert "with-op" not in tasks
    assert "OP_SERVICE_ACCOUNT_TOKEN" not in tasks


def test_role_default_request_map_is_empty():
    """Callers supply op_secrets; the role ships an empty default."""
    defaults = yaml.safe_load((ROLE / "defaults" / "main.yml").read_text())

    assert defaults["op_secrets"] == {}
