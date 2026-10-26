# Historical timeline preview

The static Vercel preview covers **600 BCE–1800 CE** with **38 selected polities**
and **1,002 dated boundary records** from Cliopatria v0.2.1. This is curated
coverage, not a complete world map. Absence of a polity does not mean the land
was uninhabited or ungoverned.

Original Polygon/MultiPolygon coordinates, holes and inclusive source intervals
are preserved. Each year selects records active in that year; there is no
interpolation, nearest-year substitution or schematic fallback. Later Chinese
dynasties, the Mongol and Ottoman empires, caliphates, Indian empires, West African
states, American polities and early colonial empires extend the initial ancient
sample. The exact name/QID selection is in `ops/build_history_preview.py`.

Some upstream Wikidata IDs are reused for unrelated names. Selection requires
both the expected source name and QID; QID matching alone is insufficient.
Overlapping intervals within a selected polity are rejected by the builder.

The source check covered identity pairs, dates, unchanged coordinates and
geometry validation. All 1,002 geometries passed PostGIS topology validation and
the application's coordinate schema. This is not independent expert historical
verification; confidence remains low. Source dating and naming remain upstream
interpretations. The importer and editorial database remain separate: generating
this static preview never publishes anything to the database.

## Build from the archived release

From the repository root:

```sh
python ops/build_history_preview.py --snapshot /path/to/cliopatria.geojson.zip
```

The default output is `needs_review`. After completing source checks, an operator
can regenerate with `--reviewed-source-checks` to record that review for the static
preview. The catalog records the unchanged upstream archive SHA256, review scope,
selected intervals, and each century chunk's hash and size. Chunks are loaded on
demand and cached by the module loader, so the initial page does not download the
whole historical collection.

The archived release used here has SHA256
`e10a4e429fca708788ff9e7572a95fce801fae55852d217cffabc1c59cd4eed4`.
Its upstream license is CC BY 4.0; the compiled Civil Atlas database is ODbL 1.0.
Keep the [Cliopatria attribution](../ATTRIBUTION.md) with produced maps and data.

## Present-day reference borders

The optional modern overlay draws country-level boundaries from the existing
OpenFreeMap/OpenMapTiles basemap. It is placed above historical territory fills,
with a thin dark stroke and low opacity. Maritime boundaries are excluded and
disputed boundaries are dashed. Country and province labels remain hidden.
These lines provide present-day orientation and are never historical claims.

The atlas and comparison views expose independent modern-border controls and
preserve them in `modernBorders=true|false` share URLs. Historical layers,
episodes and research filters do not change that choice.

The historical source records retain citations and date intervals. Seeded place,
route and narrative examples remain illustrative; examples owned by a polity
without boundary coverage at the chosen date are omitted from the map. Wider
place/event coverage and a live backend remain separate roadmap work.
