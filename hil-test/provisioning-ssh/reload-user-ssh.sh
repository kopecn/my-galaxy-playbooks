#!/usr/bin/env bash

set -euo pipefail

systemctl reload ssh
systemctl is-active --quiet ssh
journalctl -u ssh --since "1 minute ago" --no-pager
