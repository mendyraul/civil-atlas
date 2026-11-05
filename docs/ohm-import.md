# OpenHistoricalMap boundary import

Use a saved Overpass JSON export with relation tags and full member-way geometry
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
year-level API intervals preserve the source years and full date tags remain in
review notes. Approximate or absent dates are omitted rather than inferred.

The default checked civilization crosswalk is shared with Cliopatria, matching
OHM Wikidata tags. An explicit JSON crosswalk passed with `--crosswalk` may use `relation/ID`
keys for reviewed relation-specific mappings. No name-based automatic match occurs.

Member ways must form complete, unambiguous closed outer and inner rings.
Nested relations and unsupported roles are omitted. Holes require a unique outer.
Coordinates and source tags are preserved; `fixme` tags remain visible to reviewers.
Imported layers use the civilization's variant group and are never primary.

Every record is private and `needs_review`; the existing editor can inspect and
approve the boundary as a second reading. Raw bytes and the normalized manifest
are archived locally through the common ingestion pipeline. Repeating the same
version/bytes preserves later reviews; changed inputs require a new version.
