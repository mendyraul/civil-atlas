# Source of Truth

## Why there is no single source

Historical geography is contested, incomplete, and revision-heavy. Civil Atlas
should not collapse that into one fake definitive dataset.

## Canonical internal model

The Civil Atlas database is the app's canonical operational model. That means
the app reads one normalized set of civilizations, layers, places, edges,
claims, and evidence links.

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
