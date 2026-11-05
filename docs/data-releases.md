# Reviewed data releases

Apply all database migrations before loading a release. Start with an empty
database, without running the seed importer. From `backend`:

```sh
python -m app.data_release export --version 2026.11 --output civil-atlas-2026.11.zip --dry-run
python -m app.data_release export --version 2026.11 --output civil-atlas-2026.11.zip
python -m app.data_release load /path/to/civil-atlas-2026.11.zip --dry-run
python -m app.data_release load /path/to/civil-atlas-2026.11.zip
```

Load also accepts an HTTPS URL. An existing output file is never overwritten;
loading into a nonempty canonical database is refused. Export takes a consistent
snapshot of public historical records, validates schemas and public references,
and excludes review operations, credentials and source artifact locations.
Unresolved public dependencies block export: review/reconcile the underlying
records rather than releasing private supporting material automatically.

The ZIP contains canonical records, a versioned manifest with counts, source
versions and SHA-256 checksums, ATTRIBUTION.md and DATA_LICENSE.md. Validate every
member before loading. Unexpected/duplicate members, corrupt checksums, unknown
schemas, invalid records and broken references fail before writes. Loading is
one transaction, including spatial projections; failure rolls it back.
The reader limits both compressed and expanded archives to 250 MiB.

A manual GitHub Actions workflow exports a reviewed release on a self-hosted
runner with access to the intended database. Configure the `data-release`
environment and its `DATABASE_URL` secret, review the dry-run report, then run the
workflow with publication enabled. Public launch and Zenodo DOI creation remain
separate operator tasks. Do not publish the unreviewed seed additions as a release.

For self-hosting, start the database with `docker compose up -d db`, apply the
numbered migrations, load the release using the backend environment configured
for that database, then start backend and frontend with `docker compose up -d`.
Leave demo mode disabled only when the API supplies the intended reviewed coverage.
