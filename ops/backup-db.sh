#!/usr/bin/env sh
set -eu

: "${PGHOST:?PGHOST is required}"
: "${PGUSER:?PGUSER is required}"
: "${PGDATABASE:?PGDATABASE is required}"
: "${PGPASSWORD:?PGPASSWORD is required}"

backup_dir="${BACKUP_DIR:-./backups}"
retention_days="${BACKUP_RETENTION_DAYS:-14}"
mkdir -p "$backup_dir"
timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
output="$backup_dir/civil-atlas-$timestamp.dump"

pg_dump --format=custom --file="$output"
find "$backup_dir" -type f -name 'civil-atlas-*.dump' -mtime "+$retention_days" -delete
printf '%s\n' "$output"
