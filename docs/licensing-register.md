# Licensing Register

Tracks the license and attribution obligations of every external dataset **before** its data
is ingested or shipped. Ingestion of a dataset is blocked until it has a row here with a
resolved status. See [`long-term-strategy.md`](./long-term-strategy.md) and the research in
[`historical-data-sources-audit.md`](./historical-data-sources-audit.md).

## Outbound licenses (what Civil Atlas itself uses)

Civil Atlas is open source and non-commercial.

| Area | License | Declared in |
|---|---|---|
| Code and configuration | AGPL-3.0-or-later | [`LICENSE`](../LICENSE) |
| Historical database (manifests, exports, public API data) | ODbL 1.0 | [`DATA_LICENSE.md`](../DATA_LICENSE.md) |
| Documentation | CC BY 4.0 | [`LICENSES/CC-BY-4.0.txt`](../LICENSES/CC-BY-4.0.txt) |

[`REUSE.toml`](../REUSE.toml) maps paths to licenses. Upstream credit lines live in
[`ATTRIBUTION.md`](../ATTRIBUTION.md).

## Inbound rule

Because published data is released under the ODbL, a source may be ingested only if its
license lets us redistribute it inside an ODbL database:

- **Allowed:** CC0, public domain / PDDL, CC BY 3.0 or 4.0 (credit carried through
  `ATTRIBUTION.md` and per-record citations), ODbL.
- **Reference-only:** non-commercial (NC), no-derivatives (ND), GPL, CC BY-SA, custom
  "academic use" terms, and anything forbidding redistribution. **Civil Atlas being
  non-commercial does not make NC data usable.** NC is not an open license, and mixing it
  in would stop others from reusing our dataset.

The importer enforces this with `backend/app/ingestion/licenses.py`.

## Status legend

- `approved`: cleared for ingestion and redistribution under the noted obligations.
- `attribution`: usable; requires visible attribution.
- `share-alike`: usable; derived data must be released under a compatible license (ODbL is).
- `reference-only`: may be consulted by editors, **not** ingested or redistributed.
- `review`: terms not yet confirmed; do not ingest.

"Verified" means the license was read from the source's own LICENSE file or live API output.
"Reported" means it came from a catalog or project page; confirm before the first import.

## Register

| Dataset | Best for | License | Status | Obligations / notes |
|---|---|---|---|---|
| Cliopatria (Seshat) | World polity borders, 3400 BCE–2024 CE | CC BY 4.0 (verified, `LICENSE.md`) | attribution | Credit Cliopatria/Seshat and cite Bennett et al. 2025. Imported via `cliopatria.py`. |
| OpenHistoricalMap | Time-aware historical boundaries & features | CC0 1.0 (verified, Overpass output; default since Aug 2022) | approved | No obligation; credit appreciated. A few features carry their own `license=*` tag; skip those. |
| Pleiades | Greco-Roman / ancient-world places | CC BY 3.0 | attribution | Cite Pleiades + contributors. |
| Itiner-e | Roman road network | CC BY 4.0 (reported, project About page) | attribution | Use the Zenodo static release for reproducible imports. |
| AWMC geodata | Roman provinces, roads, aqueducts, ancient coastlines/rivers | ODbL 1.0 (verified, README) | share-alike | Credit AWMC. Older AWMC releases were CC BY-NC, so use only the GitHub GeoJSON. |
| Wikidata | Entity metadata, coordinates, dates, IDs (glue) | CC0 1.0 | approved | No obligation; still record provenance internally. |
| Met Museum Kushan essay | Editorial capital/context reference | No content reuse grant established | reference-only | Bibliographic metadata and an editorial reference only; no essay text or images imported. Draft dynasty dates and capital scope need review before publication. |
| Natural Earth | Modern base geometry, self-hosted basemap | Public domain | approved | No obligation. |
| GeoNames | Modern place names / coordinates (labels) | CC BY 4.0 | attribution | Cite GeoNames. |
| World Historical Gazetteer | Places, time-scoped names, reconciliation | Per dataset (CC0 / CC BY / CC BY-SA / NC) | review | Ingest only datasets that are individually CC0 or CC BY; cite WHG + contributor. |
| HGIS de las Indias | Spanish America 1701–1808 places & territories | CC BY 4.0 on WHG (reported) | review | Confirm per dataset; the project wiki is CC BY-SA. |
| HistoGIS | Europe c. 1815–1919 admin units | CC BY 4.0 per collection (reported) | review | Confirm each collection. |
| iDAI.gazetteer | Archaeological sites | CC BY 4.0 (reported) | review | Confirm on gazetteer.dainst.org. |
| historical-basemaps (aourednik) | World border snapshots | GPL-3.0 (verified) | reference-only | GPL is incompatible with ODbL. |
| DARE (Åhlfeldt) | Roman places, forts | CC BY-SA 3.0 or CC BY (reported, conflicting) | reference-only | CC BY-SA is incompatible with ODbL; could ask the author for permission. |
| DARMC / Mapping Past Societies | Roman & medieval layers | Unclear | review | Check per layer; Pleiades-linked records are CC BY 3.0. |
| CShapes 2.0 | Modern state boundaries (1886→present) | CC BY-NC(-SA) 4.0 | reference-only | Non-commercial. |
| Seshat Equinox | Structured polity attributes | CC BY-NC-SA | reference-only | Non-commercial. (Cliopatria geometry is separate and CC BY.) |
| China Historical GIS v6 | China 221 BCE–1911 | Academic only, no redistribution | reference-only | |
| Newberry Atlas of Historical County Boundaries | US counties 1629–2000 | CC BY-NC-SA | reference-only | |
| IPUMS NHGIS | US census units | No redistribution without permission | reference-only | |
| MPIDR / MOSAIC historical GIS | Central Europe c. 1870–1930 | Non-commercial scientific use | reference-only | |
| David Rumsey georeferenced maps | Historical map overlays | CC BY-NC-SA 3.0 | reference-only | |
| UNESCO World Heritage List | Heritage sites | Written permission required | reference-only | Use Wikidata for the same sites. |
| Native Land Digital | Indigenous territories | API terms restrict use | reference-only | Not historical borders; only with permission. |
| Historical Urban Population (Reba et al.) | City populations 3700 BCE–2000 CE | Not stated | review | Ask the authors. |
| ORBIS (Stanford) | Roman travel network | Not stated | review | |
| Euratlas | Historical boundaries (reference) | Commercial | reference-only | Do not ingest or redistribute geometry. |
| Centennia | Historical boundaries (reference) | Commercial | reference-only | Do not ingest or redistribute geometry. |

## Attribution surface

Datasets with `attribution` or `share-alike` status must be credited in a visible
"Data sources" surface in the app (e.g. an About/Sources page and map attribution control),
listed in [`ATTRIBUTION.md`](../ATTRIBUTION.md), and have their obligations recorded on
the relevant `sources` rows via `evidence_links`.
