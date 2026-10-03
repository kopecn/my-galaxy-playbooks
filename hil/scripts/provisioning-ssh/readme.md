# E2E HIL Instructions for Provisioning Test

## Scope

Hardware-in-the-loop (HIL) test for the SSH provisioning role. The prep scripts return a real target host to a clean pre-provisioning state (password auth on, user's `~/.ssh` empty), then `provision-full.yml` exercises the full key-handoff on that live host: connect over password auth, install the key, validate key-based login, and disable password auth.

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

Both `enable-user-ssh.sh` and `reload-user-ssh.sh` should have been copied to the host in advance.

run:

```
sudo enable-user-ssh.sh; sudo reload-user-ssh.sh
```

### Run script

```bash
ansible-playbook \
    playbooks/provision-full.yml \
    -e onePasswordVault=Personal-Automation \
    -i '<host-or-ip>,' \
    -e sshProvisioningUsername=<user> \
    -e sshProvisioningPassword=<password> \
    [-e sshFileName=<name>]
```
