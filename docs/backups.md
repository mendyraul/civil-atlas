# Database backups and restore drill

Staging uses pgBackRest for the recovery path: PostgreSQL archives WAL and
scheduled full backups to the S3-compatible `db-backups` bucket. It also creates
custom-format dumps in `./backups` as a portable logical-backup fallback and
mirrors them through `db-backup-upload`. The local directory is a short-retention
staging buffer, not the primary recovery source.

The staging database image is built from `ops/pgbackrest/Dockerfile`. Its
`archive_command` is enabled with `wal_level=replica` and uses the S3 settings
provided through environment variables. The pgBackRest repository is isolated
under the `civil-atlas/` prefix inside `db-backups`.

## 3-2-1 policy

- Keep the live database on the staging host.
- Keep the scheduled dump in the local backup directory for 14 days.
- Archive WAL and full backups to the S3-compatible `db-backups` bucket, then
  copy the repository to a separate encrypted host or NAS account before
  production.

Do not treat RAID, the home-lab host, or the MinIO data volume as the only
backup. Verify that the remote copy is readable and that its age is within the
defined recovery objective.

## Verify pgBackRest and a backup landed

Run the repository health check from the staging host:

```bash
./ops/verify-pgbackrest.sh
docker compose -f docker-compose.staging.yml exec db \
  gosu postgres pgbackrest --stanza=civil-atlas info
```

```bash
docker compose -f docker-compose.staging.yml logs db-backup --tail=20
docker compose -f docker-compose.staging.yml logs db-backup-upload --tail=20
docker compose -f docker-compose.staging.yml exec db-backup-upload \
  mc ls --recursive staging/db-backups
```

## Restore drill

Run this against a disposable PostgreSQL database, never the active staging
database. The target must have pgBackRest installed and access to the copied
repository (or use the staging repository for a controlled drill):

```bash
restore_volume=civil-atlas-restore-drill
docker volume create "$restore_volume"
docker compose -f docker-compose.staging.yml run --rm --no-deps --user root \
  -v "$restore_volume:/restore/civil-atlas" --entrypoint /bin/bash db -lc '
  chown -R postgres:postgres /restore/civil-atlas
  PGBACKREST_PG1_PATH=/restore/civil-atlas \
    exec gosu postgres pgbackrest --stanza=civil-atlas --type=immediate \
    --target-action=promote restore
'
```

Start a disposable PostgreSQL container with `restore_volume` mounted as its
`PGDATA`, then verify the restored row counts and PostGIS extension before
removing the volume. Record the backup label, WAL recovery target (or `latest`),
source bucket/prefix, restore target, row counts, and operator in the release
log. A restore is successful only when the API can read `/health/ready`,
`/api/data-version`, and `/api/v1/world/117` from the restored database.

For an operator-facing health check without a restore, run
`./ops/verify-pgbackrest.sh`; it fails if the repository or stanza is unhealthy.
