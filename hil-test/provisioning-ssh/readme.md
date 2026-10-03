# E2E HIL Instructions for Provisioning Test

## Scope

Hardware-in-the-loop (HIL) test for the SSH provisioning role. The prep scripts return a real target host to a clean pre-provisioning state (password auth on, user's `~/.ssh` empty), then `provision-full.yml` exercises the full key-handoff on that live host: connect over password auth, install the key, validate key-based login, and disable password auth.

> **Destructive:** preparation removes the designated test account's existing
> `~/.ssh` directory. Run this procedure only on an approved HIL target with a
> recovery path and local administrative access.

## Workflow

```mermaid
flowchart TD
    start([HIL run begins])

    subgraph TARGET[On the target host - local sudo]
        direction TB
        copy[/enable-user-ssh.sh and reload-user-ssh.sh<br/>copied to the host in advance/]
        enable["sudo enable-user-ssh.sh<br/>remove Ansible lock-down, re-enable<br/>password auth, wipe the user's ~/.ssh"]
        reload["sudo reload-user-ssh.sh<br/>reload sshd, confirm active, show recent logs"]
        copy --> enable --> reload
    end

    subgraph CONTROL[On the Ansible control node - over SSH]
        direction TB
        play["play: provision-full.yml<br/>hosts all, gather_facts false"]
        role_facts[role set_facts]
        role_ssh[role ssh]
        role_prov["role ssh_provisioning<br/>sshProvisioningOperations"]
        play --> role_facts --> role_ssh --> role_prov

        subgraph GATES[ssh_provisioning gates, dispatched in list order]
            direction TB
            connect["connect<br/>reach host over password auth"]
            installkey["install_key<br/>deploy the SSH public key"]
            validate["validate<br/>confirm key-based login works"]
            disable["disable_password<br/>lock down to key-only auth"]
            connect --> installkey --> validate --> disable
        end

        role_prov --> GATES
    end

    start --> TARGET
    reload -. target now accepts password SSH .-> play
    disable --> done([Target provisioned: key-only SSH])
```

## Instructions

### Prep the target

Copy [`enable-user-ssh.sh`](enable-user-ssh.sh) and
[`reload-user-ssh.sh`](reload-user-ssh.sh) to the approved HIL target in
advance. From a local administrative session on that target, run:

```bash
sudo ./enable-user-ssh.sh
sudo ./reload-user-ssh.sh
```

### Run script

```bash
printf 'Host: '; read -r HOST; \
export OP_ITEM="user-$HOST"; \
export OP_VAULT='Personal-Automation'; \
export SSH_FILE="sshkey-$HOST"; \
export SSH_USER="op://$OP_VAULT/$OP_ITEM/username"; \
export SSH_PASSWORD="op://$OP_VAULT/$OP_ITEM/password"; \
ansible-playbook playbooks/provision-full.yml \
  -i "$HOST.local," \
  -e "sshProvisioningUsername=$(op read "$SSH_USER")" \
  -e "sshProvisioningPassword=$(op read "$SSH_PASSWORD")" \
  -e "sshFileName=$SSH_FILE"
```


export HOST='robonb'; \
export OP_VAULT='Personal-Automation'; \
export OP_ITEM="user-$HOST"; \
export SSH_FILE="sshkey-$HOST"; \
export SSH_USER="op://$OP_VAULT/$OP_ITEM/username"; \
export SSH_PASSWORD="op://$OP_VAULT/$OP_ITEM/password"; \
op read "$SSH_USER"; \
op read "$SSH_PASSWORD"



## Success criteria

The run passes `connect`, `install_key`, `validate`, and `disable_password` in
that order. The installed key succeeds with password fallback disabled, the SSH
daemon accepts its updated configuration, and effective password and
keyboard-interactive authentication are both disabled.

## Recovery

If the workflow stops before lock-down, password authentication remains enabled.
If lock-down configuration or reload fails, the role restores and reloads the
previous SSH daemon configuration. If remote access is unavailable, use the
target's local administrative session to rerun the two preparation scripts.
