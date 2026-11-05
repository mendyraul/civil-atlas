# Saved Wikidata enrichment

Import saved SPARQL JSON results with `--source wikidata --snapshot results.json
--crosswalk mapping.json` and the usual dataset-version, retrieval-time, actor,
artifact-dir and dry-run arguments. No query is executed by the importer.
Wikidata structured data is CC0; retain statement URIs and retrieval metadata.

Mapping format:

```json
{"civilizations":{"Q2277":"roman-empire"},"places":{"Q220":"roma"}}
```

Bindings must include `kind` (`leader`, `capital` or `event`), `civilization`,
`value`, `valueLabel`, `statement`, `start`, `end`, `startPrecision`, and
`endPrecision`. Entity values must be Wikidata URIs. `property` may identify the
leadership property. Events may include a `place` URI. Statement identities must
be unique: ambiguous joined qualifier rows are rejected rather than silently
collapsed. Retain each independently supported assertion as a separate statement.

## Saved query templates

The three executable templates in `backend/queries` cover Roman emperor tenures
(`wikidata-roman-leaders.rq`), dated capitals (`wikidata-capitals.rq`) and notable
events with dated statements (`wikidata-events.rq`). Run them manually in the
Wikidata Query Service and save the response as SPARQL JSON. The first query is
bounded to Trajan; remove its person VALUES clause only when intentionally
preparing a broader batch. The importer itself never calls the endpoint.

Trajan's dated tenure is on his P39 (position held) statement, not necessarily
on the civilization's P35/P6 properties. The leader template retains the office
entity and label. For polities with dated P35/P6 assertions, select those
properties with the same start/end qualifier bindings. Do not reuse Cliopatria's
source IDs for cross-source lookup: its Roman row's ID differs from canonical
[Roman Empire Q2277](https://www.wikidata.org/wiki/Q2277).

The capitals template requires actual P36 start/end qualifiers. The event
template preserves both the P793 association statement and the event's P585 date
statement; it uses that point date for both bounds. Empty results indicate absent
qualifiers or associations, not permission to invent dates. Multiple locations
or joined qualifier rows require reconciliation before import.

`tests/fixtures/wikidata/trajan-tenure.sparql.json` saves the real leader query
response byte-for-byte. Its README records the hash, retrieval time and CC0
source. Use `data/imports/crosswalks/wikidata-world117.json` for that fixture.

SPARQL RDF `timeValue` uses Gregorian astronomical year numbering, so source
year 0000 becomes atlas year -1 (1 BCE). This differs from Wikibase entity JSON,
which the adapter does not accept. Calendar/precision bindings remain attached;
see [the Wikibase RDF date contract](https://www.mediawiki.org/wiki/Wikibase/Indexing/RDF_Dump_Format).

Only year precision or finer is accepted. Original precision and qualifier
bindings remain in source records. Unsupported/missing dates or crosswalks become
explicit omissions. All records remain private until editorial review.

The public `/api/v1/civilizations/{id}/enrichment?year=117` lookup and world
responses include reviewed leaders and capitals for the selected year, provided
the civilization, supporting source records/source, and referenced person/place
are public. The dossier links to each statement. Absence means no reviewed
record for that year; it does not assert that a polity had no leader or capital.

Apply migration 006 before importing: it materializes the existing entity/person/office
registry and dated office-tenure projection. Publication checks always use canonical
repository records, so private projections are never sufficient for public visibility.
