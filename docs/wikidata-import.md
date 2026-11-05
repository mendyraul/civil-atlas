# Saved Wikidata enrichment

Import saved SPARQL JSON results with `--source wikidata --snapshot results.json
--crosswalk mapping.json` and the usual dataset-version, retrieval-time, actor,
artifact-dir and dry-run arguments. No query is executed by the importer.
Wikidata structured data is CC0; retain statement URIs and retrieval metadata.

Mapping format:

```json
{"civilizations":{"Q12544":"roman-empire"},"places":{"Q220":"rome"}}
```

Bindings must include `kind` (`leader`, `capital` or `event`), `civilization`,
`value`, `valueLabel`, `statement`, `start`, `end`, `startPrecision`, and
`endPrecision`. Entity values must be Wikidata URIs. `property` may identify the
leadership property. Events may include a `place` URI. Statement identities must
be unique: ambiguous joined qualifier rows are rejected rather than silently
collapsed. Retain each independently supported assertion as a separate statement.

Example leader query to run manually and save as SPARQL JSON:

```sparql
SELECT ?kind ?civilization ?value ?valueLabel ?statement ?start ?end ?startPrecision ?endPrecision ?property WHERE {
  VALUES ?civilization { wd:Q12544 }
  VALUES (?predicate ?statementValue ?property) {
    (p:P35 ps:P35 "P35") (p:P6 ps:P6 "P6")
  }
  ?civilization ?predicate ?statement .
  ?statement ?statementValue ?value ; pqv:P580 ?startNode ; pqv:P582 ?endNode .
  ?startNode wikibase:timeValue ?start ; wikibase:timePrecision ?startPrecision .
  ?endNode wikibase:timeValue ?end ; wikibase:timePrecision ?endPrecision .
  BIND("leader" AS ?kind)
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
```

For capitals use `p:P36`, `ps:P36`, and `BIND("capital" AS ?kind)`, with the
same dated qualifier nodes. For events, select the civilization's `p:P793`
statement and `ps:P793 ?value`; use the event's `p:P585/psv:P585` time node as
both start/end (or explicitly supported P580/P582 nodes), with precision from
those nodes. Optional `?value wdt:P276 ?place` adds a mapped event place. Missing
or multiple locations require reconciliation before importing. Do not substitute
query execution dates or broad civilization dates for missing statement dates.

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
