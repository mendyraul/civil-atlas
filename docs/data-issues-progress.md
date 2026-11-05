# Data issue delivery

Implementation order: #57, #58, #59, #60, #61. Home-lab rollout (#55) and S3
integration (#62) are deferred. #63 is already completed on main.

## #57 — civilization inventory

Seed 1.2.0 adds 21 source-reported polities with cited claims, original dated
geometry and review assignments. All remain private, including with `--publish`.
The inventory accounts for all 28 prior omissions; seven identity/chronology
cases remain unresolved. Issue #57 cannot be closed until those and editorial
review are resolved. Unchanged seed replay uses a transactional receipt to
preserve subsequent editorial decisions.

Verification: seed dry-run and 30 focused unit/integration tests pass against
PostGIS 16/3.5, including private publication state and review-preserving replay.

No historical records were approved and public demo/deployment settings are unchanged.

## #58 — OpenHistoricalMap

Saved Overpass relation adapter and CLI support are implemented with exact-byte
archives, checked crosswalks, alternative readings, retained source/fixme tags,
explicit omissions and the existing editorial workflow. See `ohm-import.md`.

## #59 — roads and physical geography

Local Itiner-e and AWMC GeoJSON adapters retain exact source properties and
geometry, require release license/citation metadata, and archive mapping inputs.
Roads require cited dates and existing endpoint crosswalks; unsupported rows
remain source records with omissions. Physical features have their own private
record type and optional undated overlay with AWMC/ODbL attribution. See
`geography-import.md`.

## #60 — Wikidata enrichment

Saved SPARQL adapters import explicit statement-backed dates, capital roles,
people, office tenures and events. Migration 006 creates typed knowledge
projections. Public context and the dossier require reviewed dependencies and
filter by selected year. See `wikidata-import.md`. No live queries or historical
publication are performed automatically.

## #61 — reviewed releases

Export/load commands validate public schemas, dependency closure, checksums and
archive limits; load is transactional into an empty migrated database and
rebuilds spatial/knowledge projections. Attribution and the ODbL notice travel
with each archive. The manual release workflow requires a configured private
runner and reviewed dataset. See `data-releases.md`. No real release has been
published; production coverage parity remains an operator/editorial gate.

## Verification

- 124 backend tests pass, including the private editor Chromium test.
- Frontend typecheck, lint and 43 unit tests pass.
- All 17 atlas browser regressions pass, including mobile, accessibility, timeline
  scrubbing, linked cameras, source pages and failed-basemap recovery.
- Three published-data browser scenarios pass, including the new physical
  overlay/attribution and dated leader dossier scenario.
- Standard production build and an independent webpack build pass. A cached
  sandbox-induced Turbopack error cleared after moving generated output aside.
- REUSE licensing validation passes.

Keep #57 open for the seven documented unresolved cases and editorial review.
Update roadmap #67 after merging these software deliveries; retain #55 and #62
as deferred. Real source batches, approval and release publication require their
own evidence and must not be inferred from synthetic acceptance fixtures.
