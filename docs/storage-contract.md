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

## Buckets

- `civil-atlas-raw`
  - prefix: `sources`
  - purpose: immutable raw captures, manifests, scans, and source payloads
- `civil-atlas-normalized`
  - prefix: `imports`
  - purpose: normalized records and import manifests
- `civil-atlas-derived`
  - prefix: `geometries`
  - purpose: derived geometry, presentation artifacts, and future tiles
- `civil-atlas-exports`
  - prefix: `exports`
  - purpose: researcher exports, classroom bundles, and share artifacts

## Why this slice exists

The repo already has `source_artifacts`, `import_jobs`, review workflow tables,
and provenance docs. This slice closes the gap between those nouns and the
runtime contract that a future self-hosted MinIO or NAS-backed deployment will
need to satisfy.
