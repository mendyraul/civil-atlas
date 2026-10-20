# Local Pleiades ingestion pilot

The operator CLI imports selected Pleiades records from a local JSON snapshot.
It never fetches or publishes data. Use Python 3.12 and the dependencies in
`backend/requirements.txt`. Actual imports require PostgreSQL with the existing
`db/init` migrations applied; validation-only runs need no database.

## Capture and validate

Obtain a snapshot from the [official Pleiades downloads](https://pleiades.stoa.org/downloads)
or an individual place's `/json` endpoint. Preserve its original bytes and record
the actual retrieval timestamp. Supported inputs are an individual place object,
an array of place objects, or the comprehensive dump's `@graph`, optionally gzip
compressed. This bounded pilot loads the snapshot into memory; prefer a small
snapshot when working locally.

From `backend`, validate the included attributed Rome sample:

```bash
python -m app.ingestion.cli \
  --snapshot tests/fixtures/pleiades/rome.json \
  --place-id 423025 \
  --dataset-version rome-fixture-v1 \
  --retrieved-at 2026-09-25T18:22:31Z \
  --actor operator:local \
  --artifact-dir .local-artifacts \
  --dry-run
```

The fixture is a field subset of the downloaded record, not a full upstream
capture. Its original source and contributor attribution are recorded alongside
the fixture. The timestamp above identifies the fixture capture. For your own
snapshot, supply its real retrieval timestamp, a new dataset version, and one
`--place-id` per selected record. Missing or duplicate selected IDs fail the run.

The JSON result reports counts, omission reasons, job ID, and raw/manifest hashes.
A dry run validates source data without connecting to PostgreSQL or creating any
files. Database version conflicts are checked during actual import.

## Import, inspect, and review

Run the same command without `--dry-run` to import. The archive contains:

- `raw-sources/sha256/<raw_sha256>`: exact input bytes, including gzip if supplied.
- `normalized-sources/sha256/<manifest_sha256>`: normalized records, selected IDs,
  omissions, dataset and adapter versions, retrieval timestamp, and raw hash.

These paths are relative to `--artifact-dir`. Database artifacts use
`storage_provider=local`; they do not claim that files were uploaded to S3.
Back up this directory with the database. Existing bytes are verified and never
overwritten. An integrity failure requires restoring the correct artifact from
a trusted copy before retrying.

Use the existing protected endpoints to inspect the run and review assignments:
`GET /api/v1/import-jobs`, `GET /api/v1/artifacts`, and
`GET /api/v1/review-assignments`, with the `X-Editorial-Key` header when configured.
Open the archived manifest to inspect unpublished source records and places.
Review IDs are stable, for example `review-source_records-pleiades-record-423025`.

Submit decisions to `POST /api/v1/review-actions` using the existing interface:

```json
{
  "assignment_id": "review-source_records-pleiades-record-423025",
  "decision_type": "approve",
  "reviewer": "operator:reviewer",
  "rationale": "Explain the checked provenance and remaining uncertainty."
}
```

All imported sources, source records, eligible places, and evidence links start
unpublished and `needs_review`, each with an assignment. **The existing review API
publishes an eligible target when approved.** Review each related record before
approval; this pilot does not add a bundled publication action. Operational jobs,
artifacts, assignments, and revision records remain private.

## Normalization and uncertainty

Identifiers are namespaced (`pleiades-423025`, `pleiades-source-423025`, etc.) and
never automatically merged into seeded places. Source citations retain contributor
names and rights statements. The adapter accepts Pleiades CC BY 3.0 records and
requires a recognizable rights statement; unrecognized rights need investigation.

Places require a finite, in-range `reprPoint` in longitude/latitude order, published
source status, and explicit integer start/end years in chronological order. Dates
come from top-level `start`/`end`, or from published `locations` whose explicit
intervals overlap or touch. Disjoint or incomplete intervals are retained as
evidence without creating a place. Names, connections, modern names, and named
periods are not used to invent occupation dates. Raw records preserve all supplied
uncertainty and geometry. Normalized confidence is `low` with a rationale pending
editorial review. No boundaries, routes, civilization membership, or atlas nodes
are inferred.

The checked-in Rome sample has no explicit location dates, so its expected output
is one source and one source record, with no place or evidence link. Synthetic
unit-test dates exercise place import behavior without presenting invented dates
as historical fixture data.

## Replay, revisions, and failures

Replay using the archived raw bytes as `--snapshot`, and copy the selection,
version, and retrieval timestamp from the archived manifest. Keep the adapter
version unchanged for an exact replay. Successful receipts are immutable: replay
verifies/restores archive files and leaves existing reviews and records untouched,
even when a newer import has superseded that receipt.

Changed inputs, including selection or retrieval timestamp, require a new dataset
version. A new version resets imported targets to unpublished `needs_review`,
updates their existing assignments, and preserves prior decisions and revisions.
If a selected place loses supported dates or coordinates, its previous place and
evidence are unpublished and cannot be approved until a valid reimport. Records
outside the explicit selection are not removed or updated.

Imports serialize per adapter namespace and commit database changes in one
transaction. A failed transaction leaves no partial database run. Content-addressed
files may remain after a failure; they are harmless and reused on retry. Exit code
1 indicates invalid input, an archive integrity problem, or database failure.
Live fetching, S3 storage, staging restore drills, and editor screens remain later
increments.
