# Historical data sources audit

Audit date: 2026-10-22. This covers free sources that could supply **borders**
(polygons), **points of interest** (cities, sites, battles) and **routes**
for Civil Atlas. It extends the importer list in
[source-of-truth.md](source-of-truth.md).

License column legend:

- **verified**: read from the project's own LICENSE file or its live API output during this audit.
- **reported**: taken from catalogs or the project's site through search, not from a license file. Confirm before importing.

## Summary

1. **Cliopatria (Seshat)** is the best single source for borders. It is one
   GeoJSON file of about 13,800 polygon rows covering 3400 BCE to 2024 CE,
   licensed CC BY 4.0. Each row has year ranges and Wikidata IDs. It has
   polygons for **all 7 civilizations in our `world117` seed** at year 117
   (36 polities in total for that year).
2. **OpenHistoricalMap** is the best source we could edit and
   contribute back to. It is CC0, offers Overpass and vector tiles, and has
   year-by-year Roman Empire relations, including one for exactly 117–118 CE.
   Most ancient borders there are flagged `needs source for boundary lines`.
3. **For points of interest:** Pleiades (already piloted), Wikidata (CC0)
   and the World Historical Gazetteer (licensed per dataset). DARE and
   iDAI.gazetteer cover the Roman and archaeological world.
4. **For routes:** Itiner-e (Roman roads, CC BY 4.0, high resolution) and
   AWMC (roads, aqueducts and ancient coastlines, ODbL).
5. **Watch licenses.** Many academic datasets are non-commercial (NC) or
   share-alike (SA). Those terms are fine only if Civil Atlas stays
   non-commercial and/or keeps derived data under the same license. That is
   a product decision we have not made yet.

## Borders and polygons

| Source | Coverage | Format / access | License | Fit for Civil Atlas |
|---|---|---|---|---|
| [Cliopatria](https://github.com/Seshat-Global-History-Databank/cliopatria) (Seshat) | World, 3400 BCE–2024 CE, ~1,600–1,800 polities, ~13.8K rows | One GeoJSON file (zipped, 46 MB; 173 MB unzipped), EPSG:4326, `FromYear`/`ToYear`, `Wikidata`, `SeshatID`, `Area` | **CC BY 4.0** (verified, `LICENSE.md`) | **Top pick.** Year ranges map directly onto `valid_time`. Wikidata IDs link to other sources. Paper: [Sci Data 2025](https://doi.org/10.1038/s41597-025-04516-9). The project says it shows "one version" of each territory, so treat it as one claim among several. |
| [OpenHistoricalMap](https://www.openhistoricalmap.org) | World, any date, crowd-sourced | Overpass (`overpass-api.openhistoricalmap.org`), vector tiles (`vtiles.openhistoricalmap.org/maps/osm/{z}/{x}/{y}.pbf`), planet dumps. Features carry `start_date`/`end_date`. | **CC0** (verified in Overpass output; [license page](https://wiki.openstreetmap.org/wiki/OpenHistoricalMap/License)) | **Strong.** Has Roman Empire relations every few years (e.g. relation 2849539, 0117→0118) plus Parthian, Byzantine and Holy Roman Empire. Quality varies: many ancient borders carry `fixme:s=needs source`. We could contribute reviewed borders back. |
| [historical-basemaps](https://github.com/aourednik/historical-basemaps) | World, 54 snapshots from 123000 BCE to 2010 (100 and 200 CE, but no 117) | One GeoJSON per year with `NAME`, `SUBJECTO`, `PARTOF`, `BORDERPRECISION` (1–3) | **GPL-3.0** (verified via GitHub API) | Useful fallback, but it only has fixed snapshots and GPL is an odd license for data. The author calls it a work in progress. |
| [AWMC geodata](https://github.com/AWMC/geodata) | Greco-Roman Mediterranean | GeoJSON and shapefiles: `political_shading`, `roads`, `aqueducts`, `walls`, `urban_areas`, plus physical layers (ancient coastlines, rivers) | **ODbL 1.0** (verified, README). Derived from the Barrington Atlas. Some older AWMC releases were CC BY-NC. | Good for Roman provinces and **ancient coastlines and rivers** for the basemap. ODbL is share-alike for the derived database. |
| [CShapes 2.0](https://icr.ethz.ch/data/cshapes/) | World states and colonies, 1886–2019 | Shapefile/GeoJSON, R/Python packages | CC BY-NC(-SA) 4.0 (reported; sources disagree on SA) | Excellent for modern eras, but non-commercial. |
| [HistoGIS](https://histogis.acdh.oeaw.ac.at) | Europe c. 1815–1919, admin units | GeoJSON (Linked Places format), API | CC BY 4.0 per collection (reported) | Good for 19th-century Europe. |
| [China Historical GIS v6](https://chgis.fas.harvard.edu/data/chgis/v6/) | China, 221 BCE–1911 | Shapefiles via Harvard Dataverse | Academic only. No commercial use or redistribution (reported). | Best China data, but **we cannot redistribute it**. Reference only. |
| [HGIS de las Indias](https://whgazetteer.org/datasets/8) | Spanish America 1701–1808, 12 territorial levels, yearly | Shapefile, Linked Places format via WHG, Yale Dataverse | CC BY 4.0 on WHG; CC BY-SA on the project wiki (reported) | Strong for colonial Americas. |
| [Newberry Atlas of Historical County Boundaries](https://publications.newberry.org/ahcb/) | US counties and states, 1629–2000 | Shapefile | CC BY-NC-SA (reported) | US only, non-commercial. |
| [IPUMS NHGIS](https://www.nhgis.org) | US census units 1790–present | Shapefile (registration required) | No redistribution without permission ([terms](https://www.nhgis.org/ipums-nhgis-terms-use)) | Avoid for a public app. |
| [MPIDR / MOSAIC historical GIS](https://mosaic.ipums.org/historical-gis-datafiles) | Germany, Austria-Hungary, Europe c. 1870–1930 | Shapefile (registration required) | Non-commercial scientific use only (reported) | Avoid. |
| [Thenmap](https://www.thenmap.net) | Countries 1945–present | API, GeoJSON/TopoJSON/SVG | Not found | Modern only. CShapes covers the same period. |
| [Native Land Digital](https://native-land.ca) | Indigenous territories, present-day framing | API (key required) | 2025 API terms forbid revenue-generating use ([docs](https://api-docs.native-land.ca/llms-full.txt)) | Not historical borders. Sensitive. Only with permission. |
| Euratlas, GeaCron | Europe / world | Commercial | Paid | Out of scope (not free). |

## Points of interest (places, sites, events)

| Source | Coverage | Format / access | License | Fit |
|---|---|---|---|---|
| [Pleiades](https://pleiades.stoa.org/downloads) | Ancient world, ~40K places | JSON/CSV/RDF dumps, per-place `/json` | CC BY 3.0 | **Already piloted** (`backend/app/ingestion/pleiades.py`). Extend it to time periods and place types. |
| [Wikidata](https://query.wikidata.org) | Everything | SPARQL, dumps | **CC0** | Coordinates (`P625`), inception and dissolution (`P571`/`P576`), battles (`Q178561`), archaeological sites (`Q839954`), capitals (`P36`). Cliopatria rows already carry Wikidata IDs, so we can join polygons to capitals and events. Quality is uneven; use it to fill gaps, not as the main source. |
| [World Historical Gazetteer](https://whgazetteer.org) | World, aggregates many gazetteers | API, Linked Places format and TSV downloads | Per dataset (CC0 / CC BY / CC BY-SA / some NC). Site-wide default reads CC BY-NC. | Very useful aggregator. Check the license of each dataset. |
| [DARE (Digital Atlas of the Roman Empire)](https://imperium.ahlfeldt.se) | Roman Empire, forts, towns, oppida | GeoJSON API (`/api/geojson.php`), tiles | CC BY or CC BY-SA 3.0 (reported, conflicting) | Good Roman detail. Many places already link to Pleiades. |
| [iDAI.gazetteer](https://gazetteer.dainst.org) | Archaeological sites worldwide (German Archaeological Institute) | JSON, GeoJSON, SHP, API | CC BY 4.0 (reported) | Good archaeological coverage. |
| [Getty TGN](https://www.getty.edu/research-conservation/tools-databases/vocabularies/data-services) | ~2M current and historical place names | SPARQL, linked-data dumps | ODC-By 1.0 (reported) | Mostly names and hierarchy; coordinates are coarse. Useful for matching names. |
| [Historical Urban Population 3700 BC–AD 2000](https://doi.org/10.7927/H4ZG6QBX) (Reba et al., SEDAC) | ~1,700 cities with population by year | CSV (city, lat, lon, year, population, reliability) | No license stated (reported) | Good for city size over time. Ask the authors before redistributing. |
| [Seshat Equinox](https://seshat-db.com/downloads_page) | Polity attributes (not geometry) | CSV | CC BY-NC-SA | Rich attributes, but non-commercial. |
| [DARMC / Mapping Past Societies](https://darmc.harvard.edu) | Roman and medieval: shipwrecks, mints, roads, battles | Shapefiles | Unclear; Pleiades-linked records are CC BY 3.0 | Promising, but check terms. The site is being rebuilt. |
| OpenStreetMap `historic=*` | Surviving sites today (castles, ruins, archaeological sites) | Overpass, planet dumps | ODbL | Modern locations of remains, not historical extent. Good "visit today" layer. |
| GeoNames | Mostly modern; some historical features (`HSTS`) | API, dumps | CC BY 4.0 | Minor use. |
| UNESCO World Heritage List | ~1,200 sites | XML/KML feeds | Republication needs written permission ([FAQ](https://whc.unesco.org/en/faq/126)) | Get the same sites through Wikidata instead. |

## Routes and networks

| Source | Coverage | License | Fit |
|---|---|---|---|
| [Itiner-e](https://www.itiner-e.org) | Roman roads, ~300K km, high resolution | **CC BY 4.0** ([about](https://www.itiner-e.org/about); [Zenodo 2024 static](https://zenodo.org/records/17122148)) | **Top pick** for Roman routes. Nightly NDJSON export; use the Zenodo static copy for reproducible imports. |
| AWMC `roads`, `aqueducts`, `canals` | Greco-Roman | ODbL (verified) | Good complement. |
| [ORBIS](https://orbis.stanford.edu) | Roman travel-cost network, ~600–750 nodes, c. 200 CE | Not found; the project has ended | Great concept for travel time, but licensing is unclear. |
| Old World Trade Routes (OWTRAD) | Afro-Eurasian trade routes | Not found | Unverified. Low priority. |

## Georeferenced historical maps (raster)

- [Allmaps](https://allmaps.org): open-source tools that lay scanned historical maps (in the IIIF image format) over a web map. Good for a "show the original map" overlay rather than for vector data.
- David Rumsey collection: CC BY-NC-SA. Commercial use needs permission.
- Library of Congress map scans: mostly public domain.

## What this means for Civil Atlas

**Fit with the current pipeline.** `pleiades.py` already defines a
`SourceAdapter` and puts imports into the `needs_review` workflow. Each source
below can be one adapter that turns records into claims with source records
and evidence. Nothing gets published automatically.

**Suggested order:**

1. **Cliopatria adapter (borders).** Import rows where `FromYear ≤ year ≤ ToYear`
   as boundary claims with CC BY attribution. It covers all 7 seeded
   civilizations at 117 CE (Roman Empire, Han, Parthian, Kush, Axum,
   "Mayan City-States", Satavahana), so it can replace the hand-drawn
   placeholder polygons. It would also add 29 more polities at 117, such as
   Kushan, Xianbei, Funan and Goguryeo.
2. **OpenHistoricalMap adapter (borders, second opinion).** Import OHM
   relations for the same year as alternative boundary claims. That makes
   "contested borders" a real feature: show Cliopatria and OHM side by side
   with their confidence.
3. **Itiner-e + AWMC (routes, coastlines).** Replace the 7 schematic routes and
   use AWMC's ancient coastlines and rivers in the basemap.
4. **Wikidata enrichment (POIs).** Join on the Wikidata IDs in Cliopatria to
   pull capitals, battles and founding dates. Use it to fill gaps only.
5. **Broaden Pleiades, then World Historical Gazetteer, DARE and iDAI** for
   denser place coverage, checking the license of each dataset.

**Decisions (2026-10-23):**

- Civil Atlas is **non-commercial and fully open source**. Code is
  AGPL-3.0-or-later, the historical database is ODbL 1.0, and docs are
  CC BY 4.0. See [`DATA_LICENSE.md`](../DATA_LICENSE.md) and
  [`REUSE.toml`](../REUSE.toml).
- Because the database is ODbL, AWMC (also ODbL) can be included.
  CC0 and CC BY sources fit with attribution.
- **NC sources stay out anyway** (CShapes, Newberry, Seshat Equinox, CHGIS,
  Rumsey, MPIDR). NC is not an open license and would block reuse of our
  dataset. GPL (historical-basemaps) and CC BY-SA (DARE) are
  incompatible with ODbL and are reference-only too. The full status list
  is in [`licensing-register.md`](licensing-register.md).
- **Attribution UI.** CC BY sources require visible credit. The credit
  lines are collected in [`ATTRIBUTION.md`](../ATTRIBUTION.md); the
  map needs an attribution panel for each layer.

## Open checks

- AWMC: older releases were CC BY-NC; confirm the ODbL terms cover `political_shading`.
- DARE: the license is reported as both CC BY and CC BY-SA 3.0.
- Historical Urban Population: no license is published.
- CShapes 2.0: whether the license is BY-NC or BY-NC-SA.
- Every World Historical Gazetteer dataset has its own license.
