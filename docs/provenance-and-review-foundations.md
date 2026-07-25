# Provenance and Review Foundations

## Buckets

- `civil-atlas-raw`
  - `sources/<namespace>/<feature-kind>/<source-record-id>.json`
  - immutable raw captures, scans, notes, manifests, and dataset payloads
- `civil-atlas-normalized`
  - `imports/<dataset-slug>/<run-date>/manifest.json`
  - normalized records and import manifests that describe how raw data was
    translated into atlas-native entities
- `civil-atlas-derived`
  - `geometries/<civilization-id>/<layer-id>.geojson`
  - derived boundary variants, influence zones, thumbnails, and later vector
    tiles
- `civil-atlas-exports`
  - reserved for researcher exports, classroom bundles, and share artifacts

## Import flow

1. A dataset import creates an `import_job`.
2. Raw payloads land in `civil-atlas-raw`.
3. The import manifest and normalized outputs land in `civil-atlas-normalized`.
4. Geometry or presentation artifacts generated from normalized records land in
   `civil-atlas-derived`.
5. `source_artifacts` link every stored file back to `source_records`,
   `historical_claims`, `civilization_layers`, and the originating
   `import_job`.

## Review flow

1. Seeded or disputed entities generate `review_assignments`.
2. A reviewer resolves the assignment with a `review_decision`.
3. Any geometry or metadata change gets a `revision_record`.
4. If a revision depends on a stored artifact, the revision points back to that
   artifact id.

## Why this structure exists

- It answers where a claim or geometry came from.
- It allows reprocessing and superseding without losing the previous lineage.
- It turns review status into an actual workflow with ownership and audit
  history instead of a decorative badge.
