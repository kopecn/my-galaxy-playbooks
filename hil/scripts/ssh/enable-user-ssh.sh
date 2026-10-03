#!/usr/bin/env bash

# Re-enable password SSH and wipe the invoking user's ~/.ssh contents.

set -euo pipefail

[ "$(id -u)" -eq 0 ] || {
  echo "run with sudo" >&2
  exit 1
}

TARGET_USER="${SUDO_USER:-}"

[ -n "$TARGET_USER" ] && [ "$TARGET_USER" != "root" ] || {
  echo "could not safely determine the invoking non-root user" >&2
  exit 1
}

TARGET_HOME="$(getent passwd "$TARGET_USER" | cut -d: -f6)"
TARGET_GROUP="$(id -gn "$TARGET_USER")"
SSH_DIR="${TARGET_HOME}/.ssh"
SSHD_CONFIG="/etc/ssh/sshd_config"
DROP="/etc/ssh/sshd_config.d/00-enable-password-auth.conf"

case "$TARGET_HOME" in
  ""|"/"|"/root")
    echo "refusing unsafe home directory: $TARGET_HOME" >&2
    exit 1
    ;;
esac

PASSWORD_STATE="$(passwd -S "$TARGET_USER" | awk '{print $2}')"

[ "$PASSWORD_STATE" = "P" ] || {
  echo "$TARGET_USER does not have a usable password; refusing to remove keys" >&2
  exit 1
}

# Remove the lock-down block installed by Ansible.
sed -i \
  '/^# BEGIN SSH provisioning password lock-down$/,/^# END SSH provisioning password lock-down$/d' \
  "$SSHD_CONFIG"

# Explicitly enable password authentication.
install -d -m 0755 /etc/ssh/sshd_config.d

cat > "$DROP" <<'EOF'
PasswordAuthentication yes
KbdInteractiveAuthentication yes
EOF

chmod 0644 "$DROP"

/usr/sbin/sshd -t

EFFECTIVE="$(
  /usr/sbin/sshd -T \
    -C "user=${TARGET_USER},host=$(hostname),addr=127.0.0.1"
)"

printf '%s\n' "$EFFECTIVE" |
  grep -qx 'passwordauthentication yes' || {
    echo "PasswordAuthentication is not effectively enabled" >&2
    exit 1
  }

systemctl reload ssh 2>/dev/null || systemctl reload sshd

# Remove all SSH material belonging to the invoking user.
if [ -d "$SSH_DIR" ]; then
  find "$SSH_DIR" -mindepth 1 -depth -delete
fi

install -d \
  -o "$TARGET_USER" \
  -g "$TARGET_GROUP" \
  -m 0700 \
  "$SSH_DIR"

echo "Password SSH enabled and $SSH_DIR wiped for $TARGET_USER."
echo "Keep this session open until a new password-only login succeeds."
