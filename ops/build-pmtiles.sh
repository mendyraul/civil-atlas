#!/usr/bin/env sh
set -eu

: "${API_BASE_URL:?API_BASE_URL must be the reachable Civil Atlas API origin}"

year="${YEAR:-117}"
output_dir="${OUTPUT_DIR:-./build/tiles}"
layer_name="${LAYER_NAME:-civil-atlas-layers}"
min_zoom="${MIN_ZOOM:-0}"
max_zoom="${MAX_ZOOM:-8}"
mkdir -p "$output_dir"

command -v curl >/dev/null 2>&1 || { echo "curl is required" >&2; exit 1; }
command -v tippecanoe >/dev/null 2>&1 || {
  echo "tippecanoe is required; see docs/tiles.md" >&2
  exit 1
}
command -v pmtiles >/dev/null 2>&1 || {
  echo "pmtiles is required; see docs/tiles.md" >&2
  exit 1
}

geojson="$output_dir/layers-$year.geojson"
mbtiles="$output_dir/layers-$year.mbtiles"
pmtiles_file="$output_dir/layers-$year.pmtiles"

curl --fail --retry 3 --silent --show-error \
  "$API_BASE_URL/api/v1/spatial/layers?year=$year" > "$geojson"
tippecanoe --force --no-tile-compression --minimum-zoom "$min_zoom" \
  --maximum-zoom "$max_zoom" --name "$layer_name" --output "$mbtiles" "$geojson"
pmtiles convert "$mbtiles" "$pmtiles_file"

printf '%s\n' "$pmtiles_file"
