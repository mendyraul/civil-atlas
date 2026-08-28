# Source of Truth

## Why there is no single source

Historical geography is contested, incomplete, and revision-heavy. Civil Atlas
should not collapse that into one fake definitive dataset.

## Canonical internal model

The Civil Atlas database is the app's canonical operational model. That means
the app reads one normalized set of civilizations, layers, places, edges,
claims, and evidence links.

The public API reads only records explicitly marked `published` in the
database. Importing a manifest does not publish it; a release operator must
validate the manifest and pass the importer's `--publish` flag. The controlled
baseline may publish `seeded` and `reviewed` records with their status visible;
`needs_review` and `placeholder` records remain private. This keeps provisional
or failed imports out of the visitor experience while preserving them for
editorial review and audit.

Import plans, review queues, artifact metadata, and revision history are
operator endpoints protected by the backend-only `EDITORIAL_API_KEY`. Public
clients never receive that credential; a later editorial interface can replace
the interim shared key with organization SSO without changing the data model.

## Evidence links

Canonical objects are not meant to stand alone. They should point back to:

- source metadata
- claim types
- confidence levels
- review status
- valid time ranges

## Confidence scoring

Confidence is an operational signal, not a claim of certainty. It helps the UI
show where data is strong, provisional, or waiting on review.

## Future source importers

Likely future import candidates include:

- Pleiades
- World Historical Gazetteer
- OpenHistoricalMap
- Wikidata
- Library of Congress
- Europeana

The MVP intentionally does not ingest any of them yet.
