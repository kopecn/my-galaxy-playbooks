"""Static contracts for super-agent-side 1Password query roles."""

from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
ROLE = REPO_ROOT / "roles" / "onepassword"


def test_role_resolves_secret_maps_and_exact_queries():
    tasks = (ROLE / "tasks" / "read_queries.yml").read_text()
    defaults = yaml.safe_load((ROLE / "defaults" / "main.yml").read_text())

    assert "op_queries" in tasks
    assert "op\n      - read" in tasks
    assert "opServiceAccountTokenFullPath" in defaults
    assert (
        ".config/op/op-service-account-token"
        == defaults["opServiceAccountTokenHomePath"]
    )
    assert "superAgentHomeDir" in defaults["opServiceAccountTokenFullPath"]
    assert "opServiceAccountTokenHomePath" in defaults["opServiceAccountTokenFullPath"]
    assert "lookup('ansible.builtin.file', opServiceAccountTokenFullPath)" in tasks


def test_role_never_logs_secrets_or_reimplements_the_wrapper():
    tasks = (ROLE / "tasks" / "read_queries.yml").read_text()

    assert "no_log: true" in tasks
    assert "with-op" not in tasks


def test_query_failures_report_only_logical_field_names():
    """A failed op read is actionable without exposing references or values."""
    tasks = (ROLE / "tasks" / "read_queries.yml").read_text()

    assert "failed_when: false" in tasks
    assert "opQueryFailures" in tasks
    assert "map(attribute='item.key')" in tasks
    assert "Secret references and values remain redacted." in tasks


def test_role_default_request_map_is_empty():
    defaults = yaml.safe_load((ROLE / "defaults" / "main.yml").read_text())

    assert defaults["op_queries"] == {}


def test_service_roles_populate_separate_query_maps():
    expected = {
        "onePasswordSambaQueries": {"sambaUsername", "sambaEffectivePassword"},
        "onePasswordTailscaleQueries": {"tailscaleAuthKey"},
        "onePasswordSshUserPassQueries": {
            "ansible_user",
            "ansible_password",
            "ansible_private_key",
        },
    }
    defaults = yaml.safe_load((ROLE / "defaults" / "main.yml").read_text())

    for query_name, fact_names in expected.items():
        assert set(defaults[query_name]) == fact_names


def test_service_workflows_are_task_files_in_the_onepassword_role():
    for task_file in ("ssh_user_pass.yml", "samba.yml", "tailscale.yml"):
        assert (ROLE / "tasks" / task_file).is_file()
