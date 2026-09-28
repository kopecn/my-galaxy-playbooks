"""Static contracts for controller-side 1Password query roles."""

from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parent.parent
ROLE = REPO_ROOT / "roles" / "onepassword"


def test_role_resolves_secret_maps_and_exact_queries():
    tasks = (ROLE / "tasks" / "main.yml").read_text()
    defaults = yaml.safe_load((ROLE / "defaults" / "main.yml").read_text())

    assert "op_queries" in tasks
    assert "op\n      - read" in tasks
    assert "op_token_file" in defaults
    assert ".config/op/op-service-account-token" in defaults["op_token_file"]
    assert "lookup('ansible.builtin.file', op_token_file)" in tasks


def test_role_never_logs_secrets_or_reimplements_the_wrapper():
    tasks = (ROLE / "tasks" / "main.yml").read_text()

    assert "no_log: true" in tasks
    assert "with-op" not in tasks


def test_role_default_request_map_is_empty():
    defaults = yaml.safe_load((ROLE / "defaults" / "main.yml").read_text())

    assert defaults["op_queries"] == {}


def test_service_roles_populate_separate_query_maps():
    expected = {
        "1password_samba": {"sambaUsername", "sambaEffectivePassword"},
        "1password_tailscale": {"tailscaleAuthKey"},
        "1password_ssh_user_pass": {
            "ansible_user",
            "ansible_password",
            "ansible_private_key",
        },
    }

    for role_name, fact_names in expected.items():
        defaults = yaml.safe_load(
            (REPO_ROOT / "roles" / role_name / "defaults" / "main.yml").read_text()
        )
        query_map = next(
            value for key, value in defaults.items() if key.endswith("Queries")
        )
        assert set(query_map) == fact_names
