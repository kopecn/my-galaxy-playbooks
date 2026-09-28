"""Static contracts for the shared host SSH key validator."""

import json
import os
from pathlib import Path
import subprocess

import yaml


REPO_ROOT = Path(__file__).resolve().parent.parent
ROLE = REPO_ROOT / "roles" / "ssh"


def test_validation_playbook_is_connectionless_and_thin():
    """Validation starts on the controller and does not ping or gather facts."""
    playbook = yaml.safe_load(
        (REPO_ROOT / "playbooks" / "validate_host_ssh_key.yml").read_text()
    )

    assert len(playbook) == 1
    assert playbook[0]["gather_facts"] is False
    assert playbook[0]["serial"] == 1
    assert playbook[0]["roles"] == [
        {"role": "ssh", "sshOperation": "validate_key"}
    ]


def test_validation_freezes_the_original_inventory_endpoint():
    """Delegation cannot replace the managed endpoint with localhost."""
    defaults = (ROLE / "defaults" / "main.yml").read_text()
    tasks = (ROLE / "tasks" / "validate_key.yml").read_text()

    assert "hostvars[inventory_hostname]['ansible_host']" in defaults
    assert "sshResolvedHost" in tasks
    assert "+ [sshResolvedHost, 'true']" in tasks


def test_validation_probe_uses_the_original_inventory_endpoint(tmp_path):
    """Render the delegated probe and guard against localhost substitution."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    ssh_args_file = tmp_path / "ssh-args"
    token_file = tmp_path / "op-token"
    token_file.write_text("test-service-account-token\n")
    token_file.chmod(0o600)

    fake_op = bin_dir / "op"
    fake_op.write_text(
        "#!/bin/sh\n"
        "if [ \"$1\" = \"--version\" ]; then\n"
        "  printf '%s\\n' '2.0.0-test'\n"
        "elif [ \"$1\" = \"vault\" ] && [ \"$2\" = \"get\" ]; then\n"
        "  printf '%s\\n' '{\"id\":\"vault-id\"}'\n"
        "elif [ \"$1\" = \"item\" ] && [ \"$2\" = \"list\" ]; then\n"
        "  case \"$*\" in\n"
        "    *--categories=Login*)\n"
        "      printf '%s\\n' '[{\"id\":\"login-id\",\"title\":\"user-amelie-computer\"}]' ;;\n"
        "    *)\n"
        "      printf '%s\\n' '[{\"id\":\"item-id\",\"title\":\"sshkey-amelie-computer\"}]' ;;\n"
        "  esac\n"
        "elif [ \"$1\" = \"read\" ]; then\n"
        "  case \"$*\" in\n"
        "    */username*) printf '%s\\n' 'amelie'; exit 0 ;;\n"
        "  esac\n"
        "  for argument in \"$@\"; do\n"
        "    case \"$argument\" in\n"
        "      --out-file=*) output_file=${argument#*=} ;;\n"
        "    esac\n"
        "  done\n"
        "  printf '%s\\n' 'fake-private-key' > \"$output_file\"\n"
        "  chmod 600 \"$output_file\"\n"
        "else\n"
        "  printf '%s\\n' \"unexpected op arguments: $*\" >&2\n"
        "  exit 2\n"
        "fi\n"
    )
    fake_op.chmod(0o755)

    fake_ssh = bin_dir / "ssh"
    fake_ssh.write_text(
        "#!/bin/sh\n"
        "printf '%s\\n' \"$@\" > \"$SSH_ARGS_FILE\"\n"
    )
    fake_ssh.chmod(0o755)

    inventory = tmp_path / "hosts.ini"
    inventory.write_text(
        "[targets]\n"
        "amelie-computer ansible_host=192.0.2.42 "
        "ansible_port=2222\n"
    )

    ansible_temp = tmp_path / "ansible-temp"
    environment = os.environ.copy()
    environment.update(
        {
            "PATH": f"{bin_dir}{os.pathsep}{environment['PATH']}",
            "SSH_ARGS_FILE": str(ssh_args_file),
            "ANSIBLE_LOCAL_TEMP": str(ansible_temp / "local"),
            "ANSIBLE_REMOTE_TEMP": str(ansible_temp / "remote"),
            "ANSIBLE_LOG_PATH": str(ansible_temp / "ansible.log"),
            # The standalone validator invokes raw ssh and never consumes
            # ansible_private_key; its behavioral test does not need an agent.
            "ANSIBLE_SSH_AGENT": "none",
        }
    )

    result = subprocess.run(
        [
            "ansible-playbook",
            "-i",
            str(inventory),
            "playbooks/validate_host_ssh_key.yml",
            "-e",
            f"sshValidationOpTokenFile={token_file}",
            "-e",
            "onePasswordVault=Personal-Automation",
        ],
        cwd=REPO_ROOT,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    ssh_arguments = ssh_args_file.read_text().splitlines()
    assert "192.0.2.42" in ssh_arguments
    assert "localhost" not in ssh_arguments
    assert ssh_arguments[ssh_arguments.index("-F") + 1] == "/dev/null"
    assert ssh_arguments[ssh_arguments.index("-l") + 1] == "amelie"
    assert ssh_arguments[ssh_arguments.index("-p") + 1] == "2222"
    assert any(argument.startswith("UserKnownHostsFile=") for argument in ssh_arguments)


def test_validation_checks_onepassword_then_tries_only_the_exact_key():
    """The role resolves host items and disables every SSH fallback/config."""
    tasks = "\n".join(
        (ROLE / "tasks" / filename).read_text()
        for filename in (
            "validate_key.yml",
            "resolve_key.yml",
            "resolve_login.yml",
        )
    )

    assert "--categories=SSH Key" in tasks
    assert "sshResolvedKeyItemName" in tasks
    assert "--categories=Login" in tasks
    assert "sshResolvedLoginItemName" in tasks
    assert "/username" in tasks
    assert "'-F', '/dev/null'" in tasks
    assert "UserKnownHostsFile=" in tasks
    assert "--file-mode=0600" in tasks
    for setting in (
        "BatchMode=yes",
        "PasswordAuthentication=no",
        "KbdInteractiveAuthentication=no",
        "PreferredAuthentications=publickey",
        "IdentitiesOnly=yes",
        "IdentityAgent=none",
        "ControlMaster=no",
        "ControlPath=none",
    ):
        assert setting in tasks
    assert "always:" in tasks
    assert "state: absent" in tasks


def test_onepassword_item_names_use_only_the_short_hostname():
    """Local, DNS, and Tailnet suffixes never enter 1Password item titles."""
    defaults = (ROLE / "defaults" / "main.yml").read_text()

    assert "sshkey-" in defaults
    assert "user-" in defaults
    assert ".split('.')[0]" in defaults


def test_validation_records_all_three_schema_backed_states():
    """Downstream workflows receive a bounded state for every outcome class."""
    tasks = "\n".join(
        path.read_text() for path in (ROLE / "tasks").glob("*.yml")
    )
    schema = json.loads(
        (REPO_ROOT / ".schema" / "groups" / "ssh-schema.json").read_text()
    )

    state = schema["$defs"]["sshValidationState"]
    assert state["enum"] == ["complete", "unprovisioned", "validationError"]
    for value in state["enum"]:
        assert value in tasks


def test_all_ssh_role_defaults_are_in_the_ssh_schema():
    """Every public SSH validation input is discoverable in host_vars tooling."""
    defaults = yaml.safe_load((ROLE / "defaults" / "main.yml").read_text())
    schema = json.loads(
        (REPO_ROOT / ".schema" / "groups" / "ssh-schema.json").read_text()
    )
    root_schema = json.loads(
        (REPO_ROOT / ".schema" / "ansible-vars.schema.json").read_text()
    )

    ssh_variables = {key for key in defaults if key.startswith("ssh")}
    assert ssh_variables <= set(schema["properties"])
    assert {"$ref": "groups/ssh-schema.json"} in root_schema["allOf"]


def test_every_remote_playbook_prepares_an_explicit_onepassword_connection():
    """No operational entry point may connect before the shared SSH role."""
    password_playbooks = {
        "provision_host_ssh.yml",
        "provision_host_ssh_ensure_key.yml",
        "provision_host_ssh_install_key.yml",
    }
    validation_playbook = "validate_host_ssh_key.yml"

    for path in sorted((REPO_ROOT / "playbooks").glob("*.yml")):
        play = yaml.safe_load(path.read_text())[0]
        assert play["gather_facts"] is False, path.name
        first_role = play["roles"][0]
        assert first_role["role"] == "ssh", path.name

        if path.name == validation_playbook:
            expected_operation = "validate_key"
        elif path.name in password_playbooks:
            expected_operation = "prepare_password_connection"
        else:
            expected_operation = "prepare_key_connection"

        assert first_role["sshOperation"] == expected_operation, path.name


def test_operational_connections_ignore_dot_ssh_and_use_in_memory_keys():
    """Connection preparation uses only per-run config and credential state."""
    tasks = (ROLE / "tasks" / "prepare_connection.yml").read_text()
    defaults = (ROLE / "defaults" / "main.yml").read_text()
    config = (REPO_ROOT / "ansible.cfg").read_text()

    assert "-F /dev/null" in tasks
    assert "ansible_user:" in tasks
    assert "ansible_private_key:" in tasks
    assert "ansible_password:" in tasks
    assert "ansible_become_password:" in tasks
    assert "sshConnectionKnownHostsFile" in tasks
    assert "DEFAULT_LOCAL_TMP" in defaults
    assert (
        "lookup('ansible.builtin.env', 'HOME') }}/.ansible/known_hosts"
        not in defaults
    )
    assert "Create the controller-owned SSH state directory" not in tasks
    assert "Create the controller-owned known-hosts file" not in tasks
    assert "ssh_agent = auto" in config
