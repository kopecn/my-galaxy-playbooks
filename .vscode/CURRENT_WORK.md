## ACTIVE WORK

-

## CURRENT WORK

---

### add 1password:
- `brew install 1password-cli`
- `winget install 1password-cli`
- debian:

```
curl -sS https://downloads.1password.com/linux/keys/1password.asc | \
sudo gpg --dearmor --output /usr/share/keyrings/1password-archive-keyring.gpg && \
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/1password-archive-keyring.gpg] https://downloads.1password.com/linux/debian/$(dpkg --print-architecture) stable main" | \
sudo tee /etc/apt/sources.list.d/1password.list && \
sudo mkdir -p /etc/debsig/policies/AC2D62742012EA22/ && \
curl -sS https://downloads.1password.com/linux/debian/debsig/1password.pol | \
sudo tee /etc/debsig/policies/AC2D62742012EA22/1password.pol && \
sudo mkdir -p /usr/share/debsig/keyrings/AC2D62742012EA22 && \
curl -sS https://downloads.1password.com/linux/keys/1password.asc | \
sudo gpg --dearmor --output /usr/share/debsig/keyrings/AC2D62742012EA22/debsig.gpg && \
sudo apt update && sudo apt install 1password-cli
```

- yum

```
sudo rpm --import https://downloads.1password.com/linux/keys/1password.asc
sudo sh -c 'echo -e "[1password]\nname=1Password Stable Channel\nbaseurl=https://downloads.1password.com/linux/rpm/stable/\$basearch\nenabled=1\ngpgcheck=1\nrepo_gpgcheck=1\ngpgkey=\"https://downloads.1password.com/linux/keys/1password.asc\"" > /etc/yum.repos.d/1password.repo'
sudo dnf check-update -y 1password-cli && sudo dnf install 1password-cli
```

- nixOS

```

# NixOS has built-in modules to enable 1Password

# along with some pre-packaged configuration to make

# it work nicely. You can search what options exist

# in NixOS at https://search.nixos.org/options

# Enables the 1Password CLI

programs.\_1password = { enable = true; };

# Enables the 1Password desktop app

programs.\_1password-gui = {
enable = true;

# this makes system auth etc. work properly

polkitPolicyOwners = [ "<your-linux-username>" ];
};

```
