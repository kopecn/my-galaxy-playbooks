# E2E HIL Testing for Provisioning

## Scope

Hardware-in-the-loop (HIL) test for SSH provisioning: on a real target host, reset SSH back to password authentication and wipe the user's existing SSH material, then run the full provisioning playbook end-to-end to verify it connects over password auth, installs the key, validates it, and disables password login.

## Workflow

```mermaid
flowchart TD
    A([Start: real target host]) --> B[Copy enable-user-ssh.sh and<br/>reload-user-ssh.sh to the host]
    B --> C["sudo enable-user-ssh.sh<br/>(re-enable password auth, wipe ~/.ssh)"]
    C --> D["sudo reload-user-ssh.sh<br/>(reload sshd, show recent logs)"]
    D --> E[Run ansible-playbook<br/>playbooks/provision-full.yml]
    E --> F[set_facts role]
    F --> G[ssh role]
    G --> H[ssh_provisioning role]

    subgraph OPS[ssh_provisioning operations]
        direction TB
        H1[connect] --> H2[install_key]
        H2 --> H3[validate]
        H3 --> H4[disable_password]
    end

    H --> OPS
    OPS --> Z([Target provisioned: key-only SSH])
```

## Prep the target

Both `enable-user-ssh.sh` and `reload-user-ssh.sh` should have been copied to the host in advance.

run:
```
sudo enable-user-ssh.sh; sudo reload-user-ssh.sh
```

## Run script

```bash
ansible-playbook \
    playbooks/provision-full.yml \
    -e onePasswordVault=Personal-Automation \
    -i '<host-or-ip>,' \
    -e sshProvisioningUsername=<user> \
    -e sshProvisioningPassword=<password> \
    [-e sshFileName=<name>]
```
