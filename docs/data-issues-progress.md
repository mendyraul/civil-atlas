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
with each archive. The manual release workflow validates a checksummed exported candidate on a
GitHub-hosted runner without database access. See `data-releases.md`. No real release has been
published; production coverage parity remains an operator/editorial gate.

## Verification

- 141 backend tests pass, including the private editor Chromium test.
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


## Upstream-input and restoration audit — November 5, 2026

The initial green CI run at `fb791c0` was followed by an audit against actual
upstream inputs rather than synthetic fixtures alone:

- Itiner-e static 2024 v1.3 stores all 14,769 records as 3D single-part
  MultiLineStrings in EPSG:3395. Adapter v2 reprojects horizontal coordinates,
  retains source/elevation bytes in the archive and recognizes actual ID/name
  fields. A full-file dry run retains all source records and produces the one
  explicitly mapped test route with 14,768 explicit omissions.
- The real OHM relation 2849539 uses canonical Q2277 and an admin-centre node.
  Its independent crosswalk, metadata-node handling, topology validation and
  date conversion import the original private reading without omissions.
- The saved real Wikidata P39 query preserves Trajan's Roman emperor office,
  tenure qualifiers, date precision and calendar. RDF BCE numbering is converted
  explicitly; capital/event paths and related entity lifetimes are also tested.
- Release acceptance now exports 19 dependency-closed synthetic records from one
  newly migrated database into another, compares public atlas/source/place/event/
  context/knowledge responses and episodes, verifies projections, excludes private
  operational data and tests source withdrawal after restoration.
- Candidate validation is database-free and pins file SHA-256/version. The manual
  workflow runs on GitHub-hosted infrastructure. The Docker backend includes
  attribution/license notices and passes both real OHM dry-run and release
  validation checks on Python 3.13.

Upstream fixture READMEs record exact hashes, URLs and license evidence. These
mechanical tests do not constitute historical/editorial approval. The seven #57
cases and actual reviewed-dataset publication remain explicitly outstanding.
