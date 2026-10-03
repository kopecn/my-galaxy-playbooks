# E2E HIL Testing for Provisioning

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
