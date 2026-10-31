#!/usr/bin/env bash
set -euo pipefail
umask 077
project_dir="$(cd "$(dirname "$0")/.." && pwd)"
backup_root="${FRIENDS_CHAT_BACKUP_DIR:-/var/backups/friends-chat}"
mkdir -p "$backup_root"
chmod 700 "$backup_root"
backup_dir="$(mktemp -d "$backup_root/$(date -u +%Y%m%dT%H%M%SZ)-XXXXXX")"
cd /tmp
runuser -u postgres -- pg_dump -Fc friends_chat > "$backup_dir/database.dump"
tar -czf "$backup_dir/config-and-keys.tar.gz" -C "$project_dir"   state/synapse compose.yaml scripts templates
# Archive readability only, not a full restore test.
runuser -u postgres -- pg_restore --list < "$backup_dir/database.dump" > /dev/null
printf 'Backup created: %s\n' "$backup_dir"
echo 'Contains secrets. Copy to protected off-server storage; do not commit it.'
echo 'Also preserve your Nginx site configuration and /etc/letsencrypt securely.'
