# Provenance and Review Foundations

## Buckets

- `raw-sources`
  - `sources/<namespace>/<feature-kind>/<source-record-id>.json`
  - immutable raw captures, scans, notes, manifests, and dataset payloads
- `normalized-sources`
  - `imports/<dataset-slug>/<run-date>/manifest.json`
  - normalized records and import manifests that describe how raw data was
    translated into atlas-native entities
- `derived-tiles`
  - `geometries/<civilization-id>/<layer-id>.geojson`
  - derived boundary variants, influence zones, thumbnails, and later vector
    tiles
- `exports`
  - reserved for researcher exports, classroom bundles, and share artifacts

## Import flow

1. A dataset import creates an `import_job`.
2. Raw payloads land in `raw-sources`.
3. The import manifest and normalized outputs land in `normalized-sources`.
4. Geometry or presentation artifacts generated from normalized records land in
   `derived-tiles`.
5. `source_artifacts` link every stored file back to `source_records`,
   `historical_claims`, `civilization_layers`, and the originating
   `import_job`.
6. `POST /api/ingest-plans` can now generate that lineage bundle before any
   real object storage write happens, which makes the contract testable before
   MinIO is live.

## Review flow

1. Seeded or disputed entities generate `review_assignments`.
2. A reviewer resolves the assignment with a `review_decision`.
3. Any geometry or metadata change gets a `revision_record`.
4. If a revision depends on a stored artifact, the revision points back to that
   artifact id.

Editorial clients submit `POST /api/v1/review-actions` (or the legacy `/api`
route) with the assignment id, reviewer, rationale, and one of `approve`,
`request_changes`, `reject`, or `publish`. The API updates the target status,
records the decision and revision, and only publishes eligible reviewed records.

## Why this structure exists

- It answers where a claim or geometry came from.
- It allows reprocessing and superseding without losing the previous lineage.
- It turns review status into an actual workflow with ownership and audit
  history instead of a decorative badge.
