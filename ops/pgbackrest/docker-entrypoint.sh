#!/usr/bin/env bash

set -Eeuo pipefail

backup_interval_seconds="${CIVIL_ATLAS_PGBACKREST_BACKUP_INTERVAL_SECONDS:-86400}"
stanza="${PGBACKREST_STANZA:-civil-atlas}"
database_user="${POSTGRES_USER:-postgres}"
database_name="${POSTGRES_DB:-postgres}"
init_marker=/var/lib/postgresql/data/.civil-atlas-init-complete
archive_ready_marker=/var/lib/postgresql/data/.pgbackrest-stanza-ready
fresh_database=false

if [[ ! -f "$init_marker" ]]; then
  fresh_database=true
fi

# Keep the official image initialization and signal handling, while allowing
# pgBackRest to run in the same container as PostgreSQL. The archive_command
# below executes as the postgres user and uses the S3 settings from the
# container environment.
/usr/local/bin/docker-entrypoint.sh "$@" &
postgres_pid=$!

cleanup() {
  kill "$postgres_pid" 2>/dev/null || true
}
trap cleanup TERM INT

until pg_isready -U "$database_user" -d "$database_name" >/dev/null 2>&1; do
  if ! kill -0 "$postgres_pid" 2>/dev/null; then
    wait "$postgres_pid"
    exit $?
  fi
  sleep 2
done

initial_server_start="$(gosu postgres psql --username="$database_user" \
  --dbname="$database_name" --tuples-only --no-align \
  --command="SELECT pg_postmaster_start_time()" 2>/dev/null || true)"

# pg_isready also returns success during the official image's first-run
# initialization. Wait for the explicit marker written by the final numbered
# init script so stanza-create cannot race migrations (and so custom
# POSTGRES_USER works).
until [[ -f "$init_marker" ]] && gosu postgres psql \
  --username="$database_user" --dbname="$database_name" \
  --command="SELECT 1" >/dev/null 2>&1; do
  if ! kill -0 "$postgres_pid" 2>/dev/null; then
    wait "$postgres_pid"
    exit $?
  fi
  sleep 2
done

# On first boot the official image temporarily starts PostgreSQL to run the
# numbered init scripts, then restarts it. Wait through that deliberate
# disconnect before touching pgBackRest, otherwise stanza-create can race the
# initialization shutdown.
if [[ "$fresh_database" == true ]]; then
  while true; do
    current_server_start="$(gosu postgres psql --username="$database_user" \
      --dbname="$database_name" --tuples-only --no-align \
      --command="SELECT pg_postmaster_start_time()" 2>/dev/null || true)"
    if [[ -n "$current_server_start" && "$current_server_start" != "$initial_server_start" ]]; then
      break
    fi
    if ! kill -0 "$postgres_pid" 2>/dev/null; then
      wait "$postgres_pid"
      exit $?
    fi
    sleep 2
  done
fi

run_pgbackrest() {
  gosu postgres pgbackrest --stanza="$stanza" "$@"
}

# A failed stanza check must fail the database container: silently running
# without WAL archiving would undermine the recovery contract.
run_pgbackrest stanza-create --log-level-console=info
touch "$archive_ready_marker"
run_pgbackrest check --log-level-console=info

(
  while kill -0 "$postgres_pid" 2>/dev/null; do
    run_pgbackrest backup --type=full --log-level-console=info
    sleep "$backup_interval_seconds"
  done
) &
backup_pid=$!

set +e
wait "$postgres_pid"
postgres_status=$?
kill "$backup_pid" 2>/dev/null || true
wait "$backup_pid" 2>/dev/null || true
exit "$postgres_status"
