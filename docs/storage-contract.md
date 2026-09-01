# Storage Contract

Civil Atlas already models provenance and review as if object storage exists.
This document makes that contract explicit so the backend, future MinIO or
NAS-backed storage, and app repos agree on one bucket and prefix layout.

## Runtime contract

The backend exposes the active non-secret storage contract at:

- `/api/storage-contract`
- `/api/v1/storage-contract`

This surface is intended for:

- operator verification
- frontend or tooling introspection
- keeping local, Docker, and self-hosted storage layouts aligned

The backend now also exposes a dry-run ingest planning surface at:

- `POST /api/ingest-plans`
- `POST /api/v1/ingest-plans`

That endpoint does not upload bytes. It takes source-record metadata and
returns the concrete `import_job`, `source_records`, `source_artifacts`,
`review_assignments`, and `revision_records` that would be created under the
active bucket and prefix contract.

## Buckets

- `raw-sources`
  - prefix: `sources`
  - purpose: immutable raw captures, manifests, scans, and source payloads
- `normalized-sources`
  - prefix: `imports`
  - purpose: normalized records and import manifests
- `derived-tiles`
  - prefix: `geometries`
  - purpose: derived geometry, presentation artifacts, and future tiles
- `exports`
  - prefix: `exports`
  - purpose: researcher exports, classroom bundles, and share artifacts

## Why this slice exists

The repo already has `source_artifacts`, `import_jobs`, review workflow tables,
and provenance docs. This slice closes the gap between those nouns and the
runtime contract that a future self-hosted MinIO or NAS-backed deployment will
need to satisfy.

## Ingest plan example

```json
{
  "dataset_slug": "roman-frontier-atlas",
  "dataset_label": "Roman Frontier Atlas",
  "source_type": "historical_atlas",
  "initiated_by": "rico",
  "notes": "Prototype import for Roman boundary comparison.",
  "records": [
    {
      "source_record_id": "roman-frontier-atlas-sheet-12",
      "feature_id": "roman-empire",
      "feature_kind": "civilization",
      "feature_label": "Roman Empire",
      "title": "Roman Frontier Atlas, sheet 12",
      "citation": "Example atlas reference for the Trajanic eastern frontier",
      "filename": "roman-frontier-sheet-12.tif",
      "mime_type": "image/tiff",
      "byte_size": 8123456,
      "sha256": "sha256:example",
      "confidence": "medium_high",
      "review_status": "needs_review",
      "notes": "Candidate scan for Roman eastern campaign geometry.",
      "layer_id": "layer-roman-empire-trajanic-east",
      "create_derived_geometry": true
    }
  ]
}
```

Expected outcome:

- raw object key under `raw-sources/sources/...`
- normalized source record under `normalized-sources/imports/...`
- optional derived geometry under `derived-tiles/geometries/...`
- review assignments for editorial and geometry review when the record is not
  already treated as reviewed
