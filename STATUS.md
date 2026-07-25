# Civil Atlas — STATUS

_Last updated: 2026-07-25 (Sage)_

## Current focus
Epic #22 — Make the atlas map awesome (cinematic polish, richer data, geospatial
backbone, storytelling).

## In progress
- **Workstream A — cinematic visual + interaction polish** (child issues #23–#29).
  Implemented together on branch `feat/awesome-atlas-map` (open PR):
  - A1 #23 globe projection + atmosphere/sky
  - A2 #24 camera fly-to / fitBounds on selection
  - A3 #25 hover highlight + cursor + tooltip
  - A4 #26 cross-fade extents on year change
  - A5 #27 on-map legend overlay (`frontend/components/map/MapLegend.tsx`)
  - A6 #28 depth pass (route glow underlayer + node halos)
  - A7 #29 dim non-selected civilizations for focus
  - Also fixed a latent bug: the map init effect listed changing values in its deps,
    tearing down/rebuilding the whole map on each selection/year change. Now inits once
    via a callbacks ref.

## Queued (decompose next)
- **Workstream B — richer data + coverage** → fold into #14. First task: add the
  missing **Kushan Empire** to the 117 CE seed (`frontend/data/world117.ts`).
- **Workstream C — geospatial backbone** (PostGIS + tiles + real GeoJSON) → fold into #16.
- **Workstream D — storytelling / animated playback** → fold into #17.

## Verification
- `npx tsc --noEmit` clean.
- `npm run build` clean; `/atlas` prerenders (8/8 static pages).
- Live WebGL globe not yet smoke-tested in a browser (needs external basemap CDN).

## Notes
- Frontend is API-ready: seed fallback (`HAS_REMOTE_API`) with `WorldPayload` model.
- Workstream A is frontend-only; no backend or schema changes.
