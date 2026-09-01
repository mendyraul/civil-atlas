# Spatial tiles

Civil Atlas keeps canonical GeoJSON in the database projection and exposes
public, time-filtered layer geometry at
`GET /api/v1/spatial/layers?year=117`. The response is a GeoJSON
`FeatureCollection` whose properties retain the layer identifier, interpretation
variant, valid-time bounds, confidence, review state, and source note.

The endpoint is the source for a deterministic PMTiles build. PMTiles are
immutable, range-readable artifacts and belong in the `derived-tiles` bucket;
they are not a replacement for the canonical PostGIS geometry or its audit
metadata.

## Build a tile artifact

Install [tippecanoe](https://github.com/felt/tippecanoe) and the
[PMTiles CLI](https://github.com/protomaps/go-pmtiles), then run:

```bash
API_BASE_URL=https://api.example.com YEAR=117 \
  OUTPUT_DIR=./build/tiles ./ops/build-pmtiles.sh
```

The script writes `layers-117.geojson`, `layers-117.mbtiles`, and the final
`layers-117.pmtiles`. Review the generated artifact before copying it to
`derived-tiles/geometries/`; retain the source API revision and year in the
release record.

## Serving and caching

- Serve PMTiles through an HTTPS object store or NAS reverse proxy with byte
  range requests enabled.
- Set immutable cache headers on versioned objects, for example
  `Cache-Control: public, max-age=31536000, immutable`.
- Publish a new object key for each dataset version and focal-year build; do
  not overwrite an object referenced by a released frontend.
- Keep the PostGIS endpoint available for review, spatial predicates, and
  provenance; tiles are a presentation cache only.

The current frontend continues to use the API GeoJSON path while the tile
artifact pipeline is introduced. This makes the rollout reversible and keeps
the schematic geometry's confidence and review labels visible during review.
