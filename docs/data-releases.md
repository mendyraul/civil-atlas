# Reviewed data releases

Apply all database migrations before loading a release. Start with an empty
canonical database without running the seed importer. From `backend`:

```sh
python -m app.data_release export --version 2026.11 --output civil-atlas-2026.11.zip --dry-run
python -m app.data_release export --version 2026.11 --output civil-atlas-2026.11.zip
python -m app.data_release validate civil-atlas-2026.11.zip --version 2026.11
python -m app.data_release load /path/to/civil-atlas-2026.11.zip --dry-run
python -m app.data_release load /path/to/civil-atlas-2026.11.zip
```

`validate` and `load` also accept HTTPS URLs. Redirects may not downgrade to HTTP.
Validation needs no database connection and accepts `--sha256` to pin the whole
candidate ZIP and `--output` to save the exact verified bytes. Output files are
never overwritten. Loading into a nonempty canonical database is refused.

Export takes a consistent snapshot of public historical records, validates public
schemas, review state and dependency closure, and excludes review operations,
credentials and source artifact locations. Unresolved references block export;
reconcile/review them rather than releasing private supporting material.
Placeholders and source-blocked records are ineligible. Knowledge graph links,
relationship endpoints and curated episode/annotation dependencies are checked.
Source properties and qualifier dictionaries are retained as opaque provenance,
not interpreted as application references. Superseded-claim identifiers describe
revision lineage and do not require publishing private historical revisions.

The ZIP contains canonical records, a versioned manifest with counts, source
versions and SHA-256 checksums, ATTRIBUTION.md and DATA_LICENSE.md. Each member is
validated before loading. Unexpected/duplicate members, corruption, unsupported
schemas, invalid records and broken dependencies fail before writes. Loading is
one transaction, including spatial and knowledge projections. Stable source-release
links survive removal of operational import receipts, so withdrawing a source
still hides dependent curated episodes after restoration. Both export and load
limit compressed and expanded archives to 250 MiB.

## Publishing without private infrastructure

The manual GitHub Actions workflow runs on a GitHub-hosted Ubuntu runner. Export
a candidate locally against the intended reviewed database, make the ZIP
available at an HTTPS URL, and supply its version, URL and SHA-256 when dispatching
the workflow. It validates those exact bytes without database credentials and
uploads an artifact. `publish` defaults to false; enabling it creates a versioned
GitHub Release from the validated candidate. The optional `data-release`
environment can use the repository's normal release rules. No home-lab host or
self-hosted Actions runner is required. Public launch and Zenodo DOI creation
remain separate operator tasks; unreviewed seed additions are not a release.

## Docker and self-hosting

Backend builds now use the repository root context:

```sh
docker build -f backend/Dockerfile -t civil-atlas-backend .
```

Compose files specify that context automatically. The image includes the current
attribution and data-license notices, so release export works inside the image.
The root Docker ignore file excludes environment/credential files and unrelated
frontend/development output from the backend build context.

Start the database with `docker compose up -d db`, apply numbered migrations
(including 006), load the release using the backend environment configured for
that database, then start backend and frontend with `docker compose up -d`.
Use a reviewed dataset with the intended coverage before disabling demo mode.

The fresh-database acceptance test exports a dependency-closed synthetic atlas
into a ZIP, loads it into a separate newly migrated database, compares public
world/source/place/event/context/knowledge responses, checks spatial/tenure
projections and proves that source withdrawal still hides a restored episode.
Synthetic acceptance data is not published as historical evidence.
