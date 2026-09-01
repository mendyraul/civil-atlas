# Database backups and restore drill

Staging creates PostgreSQL custom-format dumps in `./backups` and mirrors them
to the S3-compatible `db-backups` bucket through the `db-backup-upload`
service. The local directory is a short-retention staging buffer, not the
recovery source.

## 3-2-1 policy

- Keep the live database on the staging host.
- Keep the scheduled dump in the local backup directory for 14 days.
- Mirror dumps to the S3-compatible `db-backups` bucket and copy them to a
  separate encrypted host or NAS account before production.

Do not treat RAID, the home-lab host, or the MinIO data volume as the only
backup. Verify that the remote copy is readable and that its age is within the
defined recovery objective.

## Verify a backup landed

```bash
docker compose -f docker-compose.staging.yml logs db-backup --tail=20
docker compose -f docker-compose.staging.yml logs db-backup-upload --tail=20
docker compose -f docker-compose.staging.yml exec db-backup-upload \
  mc ls --recursive staging/db-backups
```

## Restore drill

Run this against a disposable PostgreSQL database, never the active staging
database:

```bash
mkdir -p ./restore-drill
docker compose -f docker-compose.staging.yml exec -T db-backup-upload \
  mc cat staging/db-backups/civil-atlas-<timestamp>.dump \
  > ./restore-drill/civil-atlas-<timestamp>.dump
docker compose -f docker-compose.staging.yml exec db-backup \
  createdb -h <restore-host> -U <restore-user> civil_atlas_restore
docker compose -f docker-compose.staging.yml exec -T db-backup \
  pg_restore --clean --if-exists --no-owner --dbname=postgresql://<restore-user>:<password>@<restore-host>:5432/civil_atlas_restore \
  - < ./restore-drill/civil-atlas-<timestamp>.dump
```

Record the dump timestamp, source bucket, restore target, row counts, and the
operator in the release log. A restore is successful only when the API can
read `/health/ready`, `/api/data-version`, and `/api/v1/world/117` from the
restored database.
