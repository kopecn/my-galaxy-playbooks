# Host provisioning

## Goal

Bring a new host from password-only SSH access to key-only SSH access, with the generated key stored in 1Password. The workflow is built one gate at a time; this page records the target design, not what is implemented.

## Workflow

```mermaid
flowchart TD
    Start[Entry point: hostname, ssh username, ssh password] --> G1

    subgraph G1[Gate 1: connect]
        Connect[Connect over SSH with username and password]
    end

    G1 -->|connected| G2
    G1 -->|failed| Stop1[Stop: nothing changed]

    subgraph G2[Gate 2: install key]
        Generate[Generate SSH key] --> Push[Push public key to host]
        Push --> Store[Store key in 1Password as sshkey-hostname]
    end

    G2 -->|key installed and stored| G3
    G2 -->|failed| Stop2[Stop: password access still on]

    subgraph G3[Gate 3: validate and lock down]
        Validate{Does the new key log in?}
        Validate -->|yes| Disable[Disable username/password SSH access]
    end

    Validate -->|no| Stop3[Stop: password access still on]
    Disable --> Done[Host is key-only]
```

## Gates

| Gate | Purpose | Passes when |
| --- | --- | --- |
| 1. Connect | Reach the host with the supplied username and password | The SSH login succeeds |
| 2. Install key | Generate a key, push it to the host, store it in 1Password as `sshkey-hostname` | The key is on the host and in 1Password |
| 3. Validate and lock down | Prove the new key works, then turn off password access | Key login succeeds, then password login is disabled |

Password access is only disabled after the key is proven to work, so a failure at any gate leaves the host reachable.
