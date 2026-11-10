# OpenHistoricalMap boundary import

Use a saved Overpass JSON export (optionally gzip-compressed) with relation tags and full member-way geometry
(`out geom`). The importer never fetches data. Save exact bytes and record the
retrieval time and a unique dataset version. CC0 is the default license; features
with an individual `license` tag are omitted pending separate clearance.

From `backend`:

```sh
python -m app.ingestion.cli --source ohm --snapshot /path/to/overpass.json \
  --id 2849539 --year 117 --dataset-version ohm-117-v1 \
  --retrieved-at 2026-11-05T15:00:00Z --actor operator:local \
  --artifact-dir .local-artifacts --dry-run
```

Remove `--dry-run` after inspecting omissions. Import the civilization seed first.
IDs select relations, not Wikidata entities. Without IDs all saved relations are
considered. Only explicit start/end dates containing the selected year qualify;
year-level API intervals cover years that overlap the source interval. An exact
January 1 end date excludes that year; partial-year end dates retain their
uncertainty in the source tags. Full date tags remain in review notes. OHM year
0000 becomes atlas year -1 (1 BCE). Invalid or approximate dates are omitted.
See [OHM date semantics](https://wiki.openstreetmap.org/wiki/OpenHistoricalMap/Tags/Key/end_date).

The default `ohm-world117.json` crosswalk matches OHM Wikidata tags and expected
source names independently of Cliopatria. Roman Empire is
[Q2277](https://www.wikidata.org/wiki/Q2277); Cliopatria
uses a different source ID for its 117 CE row, which must not be reused as a
canonical cross-source identifier. An explicit JSON crosswalk passed with `--crosswalk` may use `relation/ID`
keys for reviewed relation-specific mappings. No name-based automatic match occurs.

Member ways must form complete, unambiguous closed outer and inner rings.
Admin-centre/label nodes are metadata rather than boundary geometry. Nested
relations and unsupported boundary roles are omitted. Holes require a unique
outer and topology must be valid; invalid polygons are never automatically repaired.
Coordinates and source tags are preserved; `fixme` tags remain visible to reviewers.
Imported layers use the civilization's variant group and are never primary.

Every record is private and `needs_review`; the existing editor can inspect and
approve the boundary as a second reading. Raw bytes and the normalized manifest
are archived locally through the common ingestion pipeline. Repeating the same
version/bytes preserves later reviews; changed inputs require a new version.


## Upstream acceptance fixture

`tests/fixtures/ohm/roman-117.overpass.json.gz` is the complete, unchanged saved
response for relation 2849539, compressed losslessly. The default adapter imports
it without custom mappings, retaining its boundary-line source warning and
leaving all records private. Its README records the source hash and CC0 notice.
