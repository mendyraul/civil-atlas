# Home-lab deployment with separate database, storage and API hosts

This is the split-host procedure for #66 and #55. It prepares the application;
it is not evidence that Proxmox guests, DNS, storage, backups or the tunnel are
already installed. Record real host names, capacity, access and software
versions before applying it. Keep the public frontend in demo mode until the
acceptance checks below pass.

## Layout and setup order

| Order | Workload | Placement and initial sizing assumption |
| --- | --- | --- |
| 1 | PostgreSQL 16 with PostGIS 3.5 | Native installation in an LXC; 50 GB NVMe volume. Database storage must not be an NFS/SMB mount. |
| 2 | S3-compatible object storage | Separate VM or supported TrueNAS app with its own dataset; 250 GB initial allowance for snapshots, releases and backups. |
| 3 | FastAPI and tunnel/reverse proxy | Small VM with Docker; private connectivity to database and storage. |
| 4 | HTTPS API hostname | Publish the API through the chosen proxy/tunnel; retain private administration. |
| 5 | Vercel frontend | Set the reachable API URL and verify database-backed behavior before leaving demo mode. |

These storage figures are planning estimates from the issue, not measured
usage. Self-hosted basemap tiles are a separate capacity decision.

Use the [Proxmox administrator guide](https://pve.proxmox.com/pve-docs/),
[PostgreSQL installation guide](https://www.postgresql.org/download/linux/)
and [PostGIS installation guide](https://postgis.net/documentation/getting_started/)
for the chosen guest OS. Record installed versions and confirm PostGIS with
`SELECT PostGIS_Full_Version();`. No host networking is changed by this repo.

## Select a maintained object store

Checked October 27, 2026: the [MinIO community repository](https://github.com/minio/minio)
is archived and states that it is no longer maintained; its community
distribution is source-only. The existing development/staging MinIO Compose
service is not an endorsement of that distribution for a new public deployment.
Select a maintained S3-compatible service and pin/test its actual distribution
before installing it. Keep the storage console and API private.

The application currently archives importer snapshots locally; #62 tracks the
S3 storage implementation. Configuring S3 variables does not upload those
snapshots. Preserve the `import-artifacts` volume separately until that backend
is implemented and verified. Configure native database backups separately from
the API VM; the split-host Compose file does not install pgBackRest.

## Database and migration preparation

Create the database and a dedicated application role on the PostgreSQL LXC.
Restrict database access to the API VM and authorized migration/backup hosts.
Keep port 5432 off public interfaces. Use a migration account with the rights
needed to install extensions, then keep application credentials separate.

Store connection details in private libpq service/pass files, not the repo.
For a **fresh database**, from the repository root:

```sh
for migration in db/init/*.sql; do
  psql 'service=civil-atlas-migrations' -v ON_ERROR_STOP=1 -f "$migration"
done
```

On an existing database, record which migrations are applied and run only the
remaining numbered files in order after a backup. Do not infer schema recovery
from a code rollback.

To move a development database, first confirm its intended content/review state.
Use a custom-format dump and restore into a clean target:

```sh
pg_dump 'service=civil-atlas-source' --format=custom --file=civil-atlas.dump
pg_restore --no-owner --dbname='service=civil-atlas-restore' civil-atlas.dump
```

The service names must identify the intended source and isolated target. A
rebuild from migrations, seed and saved imports is an alternative; preserve
review decisions and versioned source artifacts when choosing between them.

## API VM configuration

Copy `.env.home-lab.example` to the host's private secret location and replace
every placeholder. `DATABASE_URL` must use the actual LXC endpoint, with URI-
encoded credentials; `S3_ENDPOINT` must identify the selected private store.
`CORS_ORIGINS` is a comma-separated list of exact frontend origins. Use a
fresh editorial key for the deployment. Never put these values in Vercel
`NEXT_PUBLIC_*` variables.

Use the API-only Compose file for this layout. The all-in-one
`docker-compose.staging.yml` assumes its own database and MinIO services and
must not be used unchanged for a separate PostgreSQL LXC.

```sh
export CIVIL_ATLAS_API_ENV_FILE=/etc/civil-atlas/api.env
docker compose -f docker-compose.api.yml config --quiet
docker compose -f docker-compose.api.yml up -d --build backend
docker compose -f docker-compose.api.yml run --rm backend python -m app.seed.import_world117 --dry-run
```

After reviewing the seed and migration results, release eligible seed records
with the explicit `--publish --actor operator:home-lab` importer options.
Records marked `needs_review` remain private. Import the saved Cliopatria
snapshot using [the importer guide](cliopatria-import.md), with
`--artifact-dir /var/lib/civil-atlas/import-artifacts`, then review the proposed
records before publication. The Docker volume persists across one-off runs.

Verify `/health/live`, `/health/ready`, `/api/data-version` and
`/api/v1/world/117`. Confirm public endpoints exclude unpublished records and
editorial endpoints reject requests without `X-Editorial-Key`.

## HTTPS and Vercel

Run the chosen tunnel/proxy on the API VM, targeting its loopback API port.
Publish only the intended HTTPS API hostname. Keep PostgreSQL, object storage,
Docker and administration ports private; restrict editorial access separately.
Verify HTTPS and CORS from the intended frontend origins before changing Vercel.

Before cutover, compare the API with the existing 38-polity, 600 BCE–1800 CE
preview, including its 1,002 dated boundaries. A working `/world/117` response
alone is not coverage parity. Keep the current public preview until the reviewed
API preserves that timeline and the sourced geography. Do not promote the static
preview's source-check flags into database approval automatically. Migration of
that wider collection is separate work from the bounded Kushan seed change.

Follow [Vercel configuration](vercel.md): the project root is `frontend`.
Set `NEXT_PUBLIC_API_BASE_URL` to the HTTPS API origin without a trailing slash.
Set `NEXT_PUBLIC_DEMO_MODE=false` in both build and runtime configuration only
after the API and recovery checks pass, then rebuild/redeploy the recorded
commit. Check atlas, search, sources and dossiers against the real API.

## Recovery acceptance

- Schedule native PostgreSQL backups and copy them to encrypted storage off the
  lab. Protect the artifact volume and object-store data with their own backup
  policy. A second dataset on the same host is not an off-host copy.
- Restore into an isolated database; verify counts, source versions, review
  state, representative queries and API behavior. Record measured recovery time.
- Probe API uptime, readiness and backup age independently. Record alert
  destinations and test delivery. Plan for a failed API VM, database host,
  home connection or tunnel; do not treat the Vercel shell as backend availability.
- Record deployed source/image references, migration state, source snapshot
  hashes, review/publication decisions, backup location and rollback procedure.

Only after those checks may #55's live-rollout criteria be marked complete.

## Operator handoff before #55

Record these inputs in the private deployment worksheet; the repository must
contain configuration names and verification results, not credential values:

| Input | Required evidence |
| --- | --- |
| PostgreSQL LXC and API VM | Confirmed host names, addresses, access, capacity and installed versions |
| Storage provider | Maintained distribution/version, private S3 endpoint, scoped bucket permissions and a test-object readback |
| API hostname and tunnel | Domain/account ownership, ingress destination, private editorial route policy and HTTPS checks |
| Secrets | Host credential-store locations, a rotated editorial key, app database role and storage key scopes |
| Frontend origins | Exact preview/production origins verified through CORS; no wildcard authorization for editorial access |
| Recovery destination | Encrypted off-host backup location, retention, artifact-volume protection and a measured clean restore |
| Dataset cutover | Approved import/review records and timeline/geometry comparison against the current public preview |

Public ingress must not rely on the editorial key as its only network boundary.
Restrict both `/api/v1/` and `/api/` editorial route aliases at the proxy/tunnel
or private-access layer; the application key remains required behind it. Keep
the storage console, PostgreSQL, Docker and SSH off the public ingress.

The provider-neutral guide is complete without inventing these inputs. Host
provisioning, storage selection, recovery evidence and the public cutover remain
explicit #55 work, not consequences of a green Compose validation job.
