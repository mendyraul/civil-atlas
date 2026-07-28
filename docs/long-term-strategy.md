# Long-Term Strategy — Best Data, Best Graphics, Self-Hosted Storage

This document is the durable, repo-facing version of the Civil Atlas long-term strategy:
how to populate the atlas with the best historical data and give it the best graphical
representation, on self-hosted object storage. It builds on the roadmap in issue #18 and the
canonical model in [`data-model.md`](./data-model.md) and [`source-of-truth.md`](./source-of-truth.md).

## Decisions

- **Sequencing:** balanced and phased — data → infra → graphics → research/story, in
  dependency order.
- **Data sourcing:** hybrid — ingest open datasets, then curate and review on top.
- **Storage:** self-host S3-compatible object storage for source artifacts, generated tiles,
  and backups; keep app/DB deployment flexible.

## Reality check

Raw storage volume is *not* the bottleneck — vector geometry and tiles are GB-scale, not TB
(unless we also store scanned source imagery). The genuinely hard parts are geometry sourcing
and licensing, temporal modeling, cross-dataset reconciliation, and human review labor.
Self-hosted S3 is a good call, but it solves the easy problem; budget effort for modeling and
curation.

## Guiding principles (invariant)

1. **No single source of truth** — the DB is the canonical *operational* model; every object
   points back to sources + claims + confidence + review.
2. **Ingest, then curate** — importers populate breadth; the claims/confidence layer and
   review workflow raise per-object quality. Never overwrite reviewed data on re-import;
   imports land as *proposed* (`seeded`) claims/variants.
3. **Represent disagreement, don't flatten it** — reuse `variant_group` /
   `interpretation_kind` so maximal-campaign reach, administered core, and cultural extent
   coexist. Symbology must encode uncertainty; never render approximate as exact.
4. **Provenance is first-class** — store source license, retrieval date, and dataset version
   so every geometry is attributable and reproducible.

## Pillar 1 — Best information (hybrid sourcing)

**Identity backbone.** A concordance so every canonical object carries external IDs
(Wikidata QID as the glue; World Historical Gazetteer as the place-reconciliation hub). New
`external_ids` table linking entity ↔ {wikidata, whg, pleiades, geonames, ohm}.

**Primary datasets** (see [`licensing-register.md`](./licensing-register.md) for terms):
OpenHistoricalMap (historical boundaries), World Historical Gazetteer (places + time-scoped
names), Pleiades (ancient world), Wikidata (metadata + glue), Natural Earth (modern base +
basemap), GeoNames (labels), CShapes 2.0 (modern state boundaries), DARE/DARMC (Roman-era
fidelity), Seshat (polity attributes). Commercial sets (Euratlas, Centennia) are references,
not ingested/redistributed geometry.

**Ingestion pipeline** (design in #12): raw downloads → `raw-sources` bucket (immutable,
versioned) → deterministic, idempotent ETL → normalized `historical_claims` +
`civilization_layers` variants with `review_status = 'seeded'` and a source-linked
`evidence_link`. Quality tiers per region/era (#14). Review workflow (#13) promotes
seeded → reviewed and resolves competing variants.

## Pillar 2 — Best graphical representation

- **PostGIS** geometry with valid-time bounds and spatial indexes (#16); JSON seed kept as a
  fallback importer.
- **Temporal:** discrete dated boundary snapshots cross-faded over the timeline (honest — no
  faked topology morphing).
- **Tiles without a tile server:** Tippecanoe → **PMTiles** served by range request straight
  from S3/NAS.
- **Self-hosted basemap:** replace the external CDN with a self-hosted dark style +
  glyphs/sprites (Protomaps/OpenMapTiles PMTiles).
- **Symbology:** encode confidence/review into style (dashing = approximate, opacity =
  confidence), on-map legend, per-variant toggles, choropleth-by-uncertainty. Globe + fly-to
  + hover from epic #22 are the interaction base.

## Pillar 3 — Self-hosted storage (artifacts + tiles + backups)

S3-compatible server on the NAS (MinIO or Garage). Buckets: `raw-sources` (versioned
originals), `derived-tiles` (PMTiles), `db-backups`, `exports`. Backups use pgBackRest/wal-g
PITR into `db-backups` following **3-2-1** (a copy off the NAS — RAID is not a backup). App +
PostGIS stay flexible; the object store is the durable, portable core, wired via the existing
`DATABASE_URL` / `NEXT_PUBLIC_API_BASE_URL` env pattern.

## Phased roadmap

| Phase | Focus | Issues | Milestone |
|-------|-------|--------|-----------|
| 0 | Finish visual foundation (in flight) | #22 (PR #30/#32), #14, #17 | Map polish + first data gap closed |
| 1 | Canonical + infra foundation | #16, #11, #12 | Boundary served from PostGIS via API; DB backing up to S3 |
| 2 | Ingestion pipeline (hybrid) | #12, #14 | 117 CE core regenerated from imports + review |
| 3 | Tiles + self-hosted basemap | #16 | `/atlas` renders PMTiles with zero external-CDN requests |
| 4 | Review workflow + coverage | #13, #14 | Seeded → reviewed at scale; region/era packs |
| 5 | Research UX + story/teaching/export | #15, #17 | Comparison, shareable views, provenance panel, narratives |

## Execution notes

Each phase decomposes into atomic child issues (≤3 files) under its roadmap issue, ships via
PR (no direct commits to main), and keeps `tsc --noEmit` + `next build` green with the seed
fallback intact. A licensing register is maintained before any dataset's data ships.
