# Staging deployment

Staging is database-backed and explicitly disables the frontend demo snapshot.
Keep the deployment behind a reverse proxy or private network until the
editorial review workflow is ready for production traffic.

## Required secret configuration

Copy `.env.example` into the deployment secret store and provide these staging
values (never commit them):

- `STAGING_API_PUBLIC_URL`, `STAGING_CORS_ORIGINS`, `EDITORIAL_API_KEY`
- `STAGING_DATABASE_URL`, `STAGING_POSTGRES_PASSWORD`
- `S3_ACCESS_KEY_ID`, `S3_SECRET_ACCESS_KEY`

The staging Compose file refuses to start when these values are absent. It does
not publish PostgreSQL or MinIO ports publicly, and it sets
`NEXT_PUBLIC_DEMO_MODE=false` at both image build and runtime.

For an existing database volume, apply the numbered SQL files in order before
restarting the backend; new volumes apply them automatically through the
PostgreSQL init directory.

Start it with:

```bash
docker compose -f docker-compose.staging.yml up -d --build
docker compose -f docker-compose.staging.yml run --rm backend python -m app.seed.import_world117 --publish --actor operator:staging
```

The importer is repeatable. Its output includes the manifest version and SHA-256
and those identifiers are also recorded in revision actors. `--publish` is an
explicit release action: public atlas records are released, while import jobs,
review assignments, review decisions, revisions, and source artifacts remain
private operational records. Records marked `needs_review` or `placeholder`
remain unpublished even when the command is run with `--publish`.

## Backups and monitoring

`db-backup` writes daily PostgreSQL custom-format dumps to `./backups` and
retains 14 days by default. Copy those dumps to separate durable storage and
perform a restore drill before promoting a release. The backup loop is not a
substitute for off-host retention.

Monitor `GET /health/live` for process liveness and `GET /health/ready` for a
database-backed readiness signal. Alert on non-200 responses, unhealthy Compose
containers, stale `GET /api/data-version` timestamps, and backup age exceeding
the expected interval.

After the import, verify that `/api/health` reports `database: available` and
that the atlas returns records while demo mode remains false.
