# Civil Atlas — STATUS

_Last updated: 2026-07-25 (Sage)_

## Current focus
Epic #22 — Make the atlas map awesome (cinematic polish, richer data, geospatial
backbone, storytelling).

## Open PRs
- **PR #30** — Workstream A (cinematic map polish). Branch `feat/awesome-atlas-map`.
  A1–A7 (#23–#29): globe projection, camera fly-to, hover highlight, cross-fade extents,
  on-map legend, route glow + node halos, selection focus. Also fixes a latent map
  init-effect recreation bug. `tsc` + `next build` clean.
- **PR (this branch `feat/atlas-data-kushan`)** — Workstream B first task #31: adds the
  **Kushan Empire** to the 117 CE seed (civilization + Purushapura/Taxila/Bagram/Mathura
  nodes + two Silk Road routes) plus a palette color. Files: `frontend/data/world117.ts`,
  `frontend/lib/palette.ts`. `tsc` + `next build` clean.

## Queued (decompose next)
- **Workstream B (rest)** → #14. More gap polities / focal years so scrubbing
  600 BCE–1800 CE stays populated.
- **Workstream C — geospatial backbone** (PostGIS + tiles + real GeoJSON) → #16.
- **Workstream D — storytelling / animated playback** (autoplay, era caption, guided
  tour) → #17.

## Notes
- Frontend is API-ready: seed fallback (`HAS_REMOTE_API`) with `WorldPayload` model.
- Seed `sourceCatalog` is auto-derived from the civilization/node/route/era/event arrays,
  so new data only needs adding to those arrays.
- Workstreams A and B are frontend-only; no backend or schema changes.
