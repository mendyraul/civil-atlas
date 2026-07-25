# Licensing Register

Tracks the license and attribution obligations of every external dataset **before** its data
is ingested or shipped. Ingestion of a dataset is blocked until it has a row here with a
resolved status. See [`long-term-strategy.md`](./long-term-strategy.md).

## Status legend

- `approved` — cleared for ingestion + redistribution under the noted obligations.
- `attribution` — usable; requires visible attribution.
- `share-alike` — usable; derived data must be released under a compatible license.
- `reference-only` — may be consulted by editors, **not** ingested or redistributed.
- `review` — terms not yet confirmed; do not ingest.

## Register

| Dataset | Best for | License | Status | Obligations / notes |
|---|---|---|---|---|
| OpenHistoricalMap | Time-aware historical boundaries & features | ODbL 1.0 | share-alike | Attribution + share-alike on derived DB; keep "© OpenHistoricalMap contributors". |
| World Historical Gazetteer | Places, time-scoped names, reconciliation | CC-BY 4.0 | attribution | Cite WHG; preserve source attestations. |
| Pleiades | Greco-Roman / ancient-world places | CC-BY 3.0 | attribution | Cite Pleiades + contributors. |
| Wikidata | Entity metadata, coordinates, dates, IDs (glue) | CC0 1.0 | approved | No obligation; still record provenance internally. |
| Natural Earth | Modern base geometry, self-hosted basemap | Public domain | approved | No obligation. |
| GeoNames | Modern place names / coordinates (labels) | CC-BY 4.0 | attribution | Cite GeoNames. |
| CShapes 2.0 | Modern state boundaries (1886→present) | CC-BY-NC-SA (verify) | review | Confirm non-commercial terms before ingest; may restrict use. |
| DARE / DARMC (Harvard) | Roman-era geometry (higher fidelity) | Mixed CC (per layer) | review | Check per-layer terms; some CC-BY, some restricted. |
| Seshat Global History Databank | Structured polity attributes | Academic / custom | review | Confirm redistribution terms; likely citation + conditions. |
| Euratlas | Historical boundaries (reference) | Commercial | reference-only | Do not ingest or redistribute geometry. |
| Centennia | Historical boundaries (reference) | Commercial | reference-only | Do not ingest or redistribute geometry. |

## Attribution surface

Datasets with `attribution` or `share-alike` status must be credited in a visible
"Data sources" surface in the app (e.g. an About/Sources page and map attribution control),
and their obligations recorded on the relevant `sources` rows via `evidence_links`.
