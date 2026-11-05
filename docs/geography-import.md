# Roads and physical geography

Use saved GeoJSON FeatureCollections. Itiner-e's static GeoJSON is linked from
https://www.itiner-e.org/about (Zenodo DOI 10.5281/zenodo.17122148). Its project
license is CC BY 4.0. AWMC's current GitHub GeoJSON is ODbL 1.0:
https://github.com/AWMC/geodata. Older non-commercial releases are not eligible.
Record the exact release URL and citation in a mapping sidecar; verify its license
before import. Importers make no network requests.

```sh
python -m app.ingestion.cli --source itinere --snapshot roads.geojson \
  --crosswalk roads-mapping.json --dataset-version itinere-local-v1 \
  --retrieved-at 2026-11-05T15:00:00Z --actor operator:local \
  --artifact-dir .local-artifacts --dry-run
```

Use `--source awmc` for physical geography. Inspect omissions, then remove
`--dry-run`. Feature IDs come from GeoJSON `id`, or the property selected by
`id_field` (default `InLine_FID` for Itiner-e and `OBJECTID` for AWMC).
The default label fields are `Name` and `TITLE`, respectively. A repeatable `--id` selects individual features. Mapping content is
retained in the normalized source and therefore participates in the manifest hash.

Example sidecar (synthetic mappings, not historical evidence):

```json
{
  "license": "CC-BY-4.0",
  "source_url": "https://example.org/exact-release",
  "citation": "Release citation and upstream authors",
  "id_field": "id",
  "features": {
    "123": {
      "source_node_id": "existing-source-node",
      "target_node_id": "existing-target-node",
      "civilization_ids": ["roman-empire"],
      "start_year": 100,
      "end_year": 200,
      "date_citation": "Specific evidence for this interval"
    }
  }
}
```

Routes require existing atlas node endpoints and cited dates. Missing mappings
retain source records with explicit omissions. No dates, travel times or endpoint
positions are inferred from the label “Roman”. Single continuous LineStrings and single-part MultiLineStrings become routes;
disconnected parts are never bridged. Itiner-e `9999` values are unknown-date
sentinels, not years.

For AWMC use `"license": "ODbL-1.0"`; `feature_type` may identify coastlines,
rivers or aqueducts. Dates are optional; absent dates mean **undated**, not a
claim of validity in every historical period. Dated features require a
`date_citation`. Geometry and original properties are preserved in private,
reviewable `physical_features` documents. No schema migration is needed: the
canonical document repository stores them separately from territorial layers.

After editorial approval, world responses include physical features. The map's
“Physical geography” button enables their separate overlay, explicitly labels
undated coverage and displays AWMC/ODbL attribution. Imported roads use the
existing route controls. All imported records initially remain `needs_review`.


## Coordinate systems and real release fixtures

Adapter version 2 recognizes GeoJSON CRS84/EPSG:4326, World Mercator EPSG:3395
and Web Mercator EPSG:3857. The Itiner-e static v1.3 release uses EPSG:3395 and
3D single-part MultiLineStrings. PROJ converts horizontal coordinates to
longitude/latitude without simplifying vertices. The raw archive retains all
original coordinates, including elevation; source records document the display
conversion. Unsupported or conflicting CRS declarations fail rather than being
silently interpreted as longitude/latitude. A legacy snapshot without CRS may
supply `source_crs` in the mapping; otherwise RFC 7946 CRS84 is assumed.

`tests/fixtures/itinere/roads-v1.3.geojson` and
`tests/fixtures/awmc/shoreline.geojson` select unchanged source features with
original CRS/properties. Their READMEs record upstream URLs, full-file hashes,
retrieval times and license evidence. Tests verify coordinate conversion,
identifier/label defaults, retained uncertainty fields and undated AWMC data.
The fixture endpoint mapping tests mechanics and is not historical approval.
