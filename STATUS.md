# Civil Atlas — STATUS

_Last updated: 2026-07-25 (Sage)_

## Current focus
Epic #22 (make the atlas map awesome) is in flight, and a long-term strategy is now set for
evolving Civil Atlas into a research-grade atlas on self-hosted storage —
see [`docs/long-term-strategy.md`](docs/long-term-strategy.md).

## Long-term direction (approved)
- Balanced/phased; **hybrid** data sourcing (ingest open datasets, then curate); self-host
  S3 for artifacts + tiles + backups.
- Phases: 0 visual foundation (in flight) → 1 PostGIS + concordance + MinIO/backups →
  2 ingestion pipeline → 3 tiles + self-hosted basemap → 4 review workflow + coverage →
  5 research UX + story/teaching/export.
- Dataset terms tracked in [`docs/licensing-register.md`](docs/licensing-register.md).

## Open PRs
- **PR #30** — Workstream A (cinematic map polish): globe, fly-to, hover, cross-fade, legend,
  route glow + node halos, selection focus; map init-effect recreation bug fixed.
- **PR #32** — Workstream B first task #31: Kushan Empire added to the 117 CE seed.
- **PR (this branch `docs/long-term-strategy`)** — strategy + licensing register docs.

## Queued
- Phase 0 remainder: rest of Workstream B (#14), Workstream D playback/story (#17).
- Phase 1 child issues (decomposed under #16 / #11 / #12) — see epic #22 / #18.
- Later phases 2–5 mapped to #12/#14/#13/#15/#17.

## Notes
- Frontend is API-ready: seed fallback (`HAS_REMOTE_API`) with `WorldPayload` model.
- Seed `sourceCatalog` auto-derives from the civilization/node/route/era/event arrays.
- Current gaps to close in Phase 1: no PostGIS yet (`docker-compose.yml` uses `postgres:16`),
  no ingestion, basemap is an external CDN in `AtlasMap.tsx`.
