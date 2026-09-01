#!/usr/bin/env bash

set -Eeuo pipefail

compose_file="${COMPOSE_FILE:-docker-compose.staging.yml}"
stanza="${PGBACKREST_STANZA:-civil-atlas}"

docker compose -f "$compose_file" exec -T db \
  gosu postgres pgbackrest --stanza="$stanza" check
docker compose -f "$compose_file" exec -T db \
  gosu postgres pgbackrest --stanza="$stanza" info --output=json

echo "pgBackRest repository is reachable and the stanza is healthy."
echo "For a restore drill, restore the newest full backup into a disposable PostgreSQL instance before promoting it."
