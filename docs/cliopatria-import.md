# Cliopatria border import

The operator CLI imports polity borders from a local copy of
[Cliopatria](https://github.com/Seshat-Global-History-Databank/cliopatria)
(Seshat Global History Databank, CC BY 4.0) as **alternative boundary layers** on
existing world117 civilizations. Like the [Pleiades pilot](pleiades-pilot.md), it
never fetches or publishes data. Everything lands as `needs_review`.

## How rows map to Civil Atlas

- Crosswalks with `cliopatria_name` require an exact source-name/QID pair.
  A reused QID attached to an unrelated active polity is rejected before
  normalization or import. Explicit legacy crosswalks containing only the
  civilization ID and variant group still work. Adapter version 2 records this
  stricter identity policy in import provenance.

- Cliopatria stores one row per polity per year range (`FromYear`/`ToYear`,
  negative for BCE). `--year` selects the rows active in that year.
- Rows are matched to civilizations by Wikidata ID through
  `backend/data/imports/crosswalks/cliopatria-world117.json`. Each entry also
  names the civilization's existing `variant_group`, so the import sits beside
  the seeded geometry as another reading (`interpretation_kind=boundary_variant`,
  `is_primary=false`).
- Each row becomes a layer, a `supports_boundary` claim, a source record and an
  evidence link. All of them cite the release and the paper
  ([doi:10.1038/s41597-025-04516-9](https://doi.org/10.1038/s41597-025-04516-9)).
- Geometry is stored exactly as published, with no simplification. At 117 CE the
  largest row (Roman Empire) has about 1,500 vertices.
- Active polities without a crosswalk entry are listed as omissions. At 117 CE
  there are 29 of them, such as the Kushan Empire, Xianbei, Funan and Goguryeo.
  Adding them means adding civilizations first.

World117 seed version 1.1.0 adds Kushan (Q25979), its source-reading group,
cited existence claim and the preserved 117–126 CE Cliopatria border. These
records remain `needs_review` and unpublished even with the seed's `--publish`
flag. The 30–375 broad dynasty bounds and Purushapura capital label retain the
demo convention pending chronology/capital-role review. The museum reference
is citation-only; no copyrighted text or image is imported. See
`tests/fixtures/cliopatria/kushan-117.geojson` for the geometry-preservation check.
The older count of 29 unmapped polities predates this addition.

## Run

Download a release (the `cliopatria.geojson.zip` file in the repository, or a
[Zenodo](https://zenodo.org/records/13363121) version), keep its bytes unchanged,
and note when you retrieved it. The zip and the unzipped GeoJSON are both
accepted. The collection `name` (for example `cliopatria_polities_only_v021`) is
recorded as the release label.

From `backend`, validate against the bundled sample:

```bash
python -m app.ingestion.cli --source cliopatria \
  --snapshot tests/fixtures/cliopatria/sample-117.geojson \
  --year 117 \
  --dataset-version cliopatria-fixture-v1 \
  --retrieved-at 2026-10-22T20:46:00Z \
  --actor operator:local \
  --artifact-dir .local-artifacts \
  --dry-run
```

Pass `--id Q12544` (repeatable) to import specific polities only. Without `--id`,
every mapped polity active in that year is imported. For a real import, drop
`--dry-run`, use your own snapshot path and retrieval time, and pick a new
`--dataset-version`.

The world117 seed must already be imported, because layers reference its
civilizations. Otherwise the import fails and nothing is written. Imported layers are
also written to the PostGIS `civilization_layers` table, but they appear in public
API responses only after an editor approves them through the review queue.

## Licensing

Cliopatria is CC BY 4.0, which the importer's license gate
(`backend/app/ingestion/licenses.py`) allows. Keep the credit line in
[`ATTRIBUTION.md`](../ATTRIBUTION.md) and show it wherever these borders are
displayed. See [`licensing-register.md`](licensing-register.md).
