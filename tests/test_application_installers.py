"""Repository-wide contracts for canonical application installer interfaces."""

import json
from pathlib import Path

import pytest
import yaml


REPO_ROOT = Path(__file__).resolve().parent.parent
INSTALLERS = {
    "claude": ("claude", "claude", ("diagnose", "install", "uninstall")),
    "lm_studio": (
        "lm_studio",
        "lmStudio",
        ("diagnose", "install", "uninstall"),
    ),
    "ollama": ("ollama", "ollama", ("diagnose", "install", "uninstall")),
    "samba": ("samba", "samba", ("diagnose", "install", "uninstall")),
    "tailscale": (
        "tailscale",
        "tailscale",
        ("diagnose", "down", "install", "status", "uninstall", "up", "update"),
    ),
    "vscode": ("vscode", "vscode", ("install",)),
}


@pytest.mark.parametrize(
    ("playbook_name", "role_name", "variable_prefix", "operations"),
    tuple((playbook, *contract) for playbook, contract in INSTALLERS.items()),
)
def test_installer_has_one_runtime_operation_playbook(
    playbook_name, role_name, variable_prefix, operations
):
    """Every installer exposes one serial playbook and no operation variants."""
    path = REPO_ROOT / "playbooks" / f"{playbook_name}.yml"
    play = yaml.safe_load(path.read_text())[0]
    role_names = [role["role"] for role in play["roles"]]

    assert play["gather_facts"] is False
    assert play["serial"] == 1
    assert role_names == ["set_facts", "onepassword", "ssh", role_name]
    assert not list((REPO_ROOT / "playbooks").glob(f"{playbook_name}_*.yml"))


@pytest.mark.parametrize(
    ("playbook_name", "role_name", "variable_prefix", "operations"),
    tuple((playbook, *contract) for playbook, contract in INSTALLERS.items()),
)
def test_installer_validates_and_dispatches_ordered_array(
    playbook_name, role_name, variable_prefix, operations
):
    """Defaults, enum, schema, and loop dispatch share one public contract."""
    role = REPO_ROOT / "roles" / role_name
    plural = f"{variable_prefix}Operations"
    singular = f"{variable_prefix}Operation"
    supported = f"{variable_prefix}SupportedOperations"
    defaults = yaml.safe_load((role / "defaults" / "main.yml").read_text())
    variables = yaml.safe_load((role / "vars" / "main.yml").read_text())
    task_directory = role / "tasks"
    tasks = (task_directory / "main.yml").read_text()
    all_tasks = "\n".join(path.read_text() for path in task_directory.glob("*.yml"))
    schema = json.loads(
        (REPO_ROOT / ".schema" / "groups" / f"{playbook_name}-schema.json").read_text()
    )

    assert defaults[plural] == []
    assert variables[supported] == list(operations)
    assert f"{plural} is sequence" in tasks
    assert f"{plural} is not string" in tasks
    assert f"{plural} | length > 0" in tasks
    assert f"difference({supported})" in tasks
    assert f'include_tasks: "{{{{ {singular} }}}}.yml"' in tasks
    assert f'loop: "{{{{ {plural} }}}}"' in tasks
    assert f"loop_var: {singular}" in tasks
    assert "ansible.builtin.setup:" in tasks
    assert "gather_subset:\n      - min" in tasks
    assert "ansible.builtin.set_fact:" not in tasks
    assert "ansible_facts.os_family" in tasks
    assert "ansible_facts.architecture" in tasks
    assert "hostOperatingSystem" not in all_tasks
    assert "hostArchitecture" not in all_tasks
    assert f"{variable_prefix}OsFamily" not in all_tasks
    assert f"{variable_prefix}EffectiveArch" not in all_tasks
    assert schema["$defs"][plural]["type"] == "array"
    assert schema["$defs"][plural]["minItems"] == 1
    assert schema["$defs"][plural]["items"]["enum"] == list(operations)


def test_installer_operation_schemas_are_composed_into_root():
    """Every public runtime array is discoverable through the root schema."""
    root = json.loads(
        (REPO_ROOT / ".schema" / "ansible-vars.schema.json").read_text()
    )
    references = {entry["$ref"] for entry in root["allOf"]}

    for playbook_name in INSTALLERS:
        assert f"groups/{playbook_name}-schema.json" in references


def test_platform_dispatch_uses_native_ansible_fact_values_only():
    """No inventory or role-local platform aliases sit between facts and roles."""
    host_schema = json.loads(
        (REPO_ROOT / ".schema" / "groups" / "host-schema.json").read_text()
    )

    assert "hostOperatingSystem" not in host_schema["properties"]
    assert "hostArchitecture" not in host_schema["properties"]

    for _, (role_name, variable_prefix, _) in INSTALLERS.items():
        variables = yaml.safe_load(
            (REPO_ROOT / "roles" / role_name / "vars" / "main.yml").read_text()
        )
        support_matrix = variables[f"{variable_prefix}SupportMatrix"]
        if "Darwin" in support_matrix:
            assert "arm64" in support_matrix["Darwin"]
            assert "aarch64" not in support_matrix["Darwin"]

    firewall_tasks = (
        REPO_ROOT / "roles" / "firewall" / "tasks" / "main.yml"
    ).read_text()
    assert "firewallOsFamily" not in firewall_tasks
    assert "ansible_facts.os_family" in firewall_tasks
