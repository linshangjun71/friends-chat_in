#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ $# != 1 || ! "$1" =~ ^[a-z0-9_]+$ ]]; then
  echo "Usage: sudo bash scripts/add-user.sh username (lowercase, digits, underscores)" >&2
  exit 1
fi
# Interactive password entry; never put passwords into command arguments.
# A username such as 'admin' does NOT grant server administrator privileges.
docker compose exec synapse register_new_matrix_user   -c /data/homeserver.yaml -u "$1" --no-admin http://127.0.0.1:8008
