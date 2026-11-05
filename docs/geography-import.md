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
`id_field`. A repeatable `--id` selects individual features. Mapping content is
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
positions are inferred from the label “Roman”. Only continuous LineStrings become
routes, preserving every coordinate.

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
