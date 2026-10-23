# Civil Atlas

Civil Atlas is a time-enabled historical civilization atlas. The first MVP,
`Civil Atlas: World at 117 CE`, is a monorepo prototype for testing a timeline,
map, evidence model, and canonical operational data layer without pretending the
history is settled.

## MVP scope

- Timeline-driven atlas view
- Active civilizations by selected year
- Approximate civilization layers with stable colors
- Zoom-aware places and route visibility
- Clickable civilization, place, and route detail panels
- Seeded sources, claims, and evidence links
- Canonical backend model plus frontend atlas UI

## Stack

- Frontend: Next.js, TypeScript, Tailwind CSS, MapLibre GL JS
- Backend: FastAPI, Python
- Database: PostgreSQL/PostGIS with GeoJSON fallback and spatial indexes
- Infrastructure: Docker Compose

## Services

- `frontend`: Next.js app on `http://localhost:3000`
- `backend`: FastAPI app on `http://localhost:8000`
- `db`: PostgreSQL 16 on `localhost:5432`

## Storage contract readiness

The backend exposes a read-only storage contract at `/api/storage-contract` and
`/api/v1/storage-contract` so the app and operators can agree on the expected
S3-compatible bucket and prefix layout before live object storage is wired in.

Relevant environment variables:

- `S3_ENDPOINT`
- `S3_ACCESS_KEY_ID`
- `S3_SECRET_ACCESS_KEY`
- `S3_PUBLIC_BASE_URL`
- `S3_REGION`
- `S3_USE_PATH_STYLE`
- `S3_SIGNED_URL_TTL_SECONDS`
- `S3_BUCKET_RAW`
- `S3_BUCKET_NORMALIZED`
- `S3_BUCKET_DERIVED`
- `S3_BUCKET_EXPORTS`
- `S3_PREFIX_RAW`
- `S3_PREFIX_NORMALIZED`
- `S3_PREFIX_DERIVED`
- `S3_PREFIX_EXPORTS`

## Run locally

```bash
cp .env.example .env
docker compose up --build
```

Manual backend run:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Manual frontend run:

```bash
cd frontend
npm ci
npm run dev
```

## Basemap configuration and licensing

Set `NEXT_PUBLIC_MAP_STYLE_URL` to a public MapLibre Style Specification URL. It
is a browser-visible, build-time Next.js setting; the style, tile, sprite, and
glyph URLs it references must allow browser CORS requests. Docker Compose and
Vercel default it to the checked-in `/map-styles/minimal.json`. Rebuild the
frontend after changing it.

The fallback style uses the public [OpenFreeMap](https://openfreemap.org/)
vector-tile and glyph service and OpenStreetMap data. OpenFreeMap publishes its
service under its terms and the map must continue to show **© OpenStreetMap
contributors** with a link to the OSM copyright page. The style embeds this
attribution and the UI deliberately retains MapLibre's attribution control.
OpenFreeMap currently describes the public service as free with no API keys or
request limits, but availability is not an SLA: review the provider's current
terms and fair-use guidance before production traffic. Do not remove or obscure
attribution, and do not configure a commercial or restricted style, tile,
sprite, or glyph endpoint without confirming that its license covers the
intended deployment and traffic volume.

The fallback JSON is local, but its basemap tiles and glyphs are not. During
offline development the globe receives the fallback land/background colors and
Civil Atlas's local GeoJSON layers can still initialize, while water,
boundaries, and labels require network access. Failed requests are reported in
the accessible map status overlay and can be retried. For fully offline use,
host licensed OpenMapTiles-compatible vector tiles and glyphs locally, update a
copy of the style to those endpoints, preserve the source-data attribution, and
point `NEXT_PUBLIC_MAP_STYLE_URL` at that style.

## Seed data

The current versioned import manifest spans roughly `600 BCE` to `1800 CE`,
with `117 CE` as the main focal year. It includes seven civilizations, a small
place set, a small edge set, and manual source/evidence records. Import it with:

```bash
cd backend
python -m app.seed.import_world117 --dry-run
python -m app.seed.import_world117 --publish --actor operator:staging
```

The manifest lives at
`backend/data/imports/world117/v1/manifest.json`. Increment its dataset version
when changing records; the importer validates provenance, records its manifest
hash, and is safe to rerun. Imports are private by default; `--publish` is an
explicit release of eligible public atlas entity types. `needs_review` and
`placeholder` records stay private. Review assignments, decisions, revisions,
import jobs, and source artifacts remain operational records.

## Vercel

Vercel serves the frontend only. Configure the project root as `frontend` (or
use the checked-in root `vercel.json`), set
`NEXT_PUBLIC_API_BASE_URL` to the public HTTPS FastAPI origin, and keep
`NEXT_PUBLIC_DEMO_MODE=false`. See [the Vercel deployment runbook](docs/vercel.md)
for the GitHub author identity and release checks.

## Source-of-truth philosophy

Civil Atlas treats the database as the canonical operational model for the app.
That model is still provisional: every canonical object should point back to
sources, claims, confidence levels, review status, and valid time ranges.

## Known limitations

- Boundaries are schematic placeholder or source-reported approximations
- A local Pleiades JSON adapter supports selected-record imports with archived
  source bytes, provenance, and review assignments; live fetching remains future work.
  See [the Pleiades pilot runbook](docs/pleiades-pilot.md).
- PostGIS geometry storage is in place, but production geometry population and
  vector-tile generation remain future scale work
- Source ingestion and editorial review are currently operator/API foundations;
  the end-to-end editor UI is not yet available
- The frontend is still optimized for the MVP atlas flow, not a full research UI
# Data modes

The API serves only validated repository data. Import the bundled, idempotent
fixture with `python -m app.seed.import_world117` after applying the SQL
migrations in `db/init`. The frontend never falls back to bundled knowledge in
production. Set `NEXT_PUBLIC_DEMO_MODE=true` explicitly to use the clearly
labeled World 117 demo snapshot without an API.

## License

Civil Atlas is open source and non-commercial.

- **Code** is licensed under [AGPL-3.0-or-later](LICENSE). If you run a modified
  version as a public web service, you must offer its source code to that service's users.
- **Historical data** (`backend/data/`, database exports, public API data) is
  licensed under the [Open Database License 1.0](DATA_LICENSE.md).
- **Documentation** is licensed under [CC BY 4.0](LICENSES/CC-BY-4.0.txt).

[`REUSE.toml`](REUSE.toml) maps every path to its license. Upstream data credits
are in [ATTRIBUTION.md](ATTRIBUTION.md). Which sources may be imported is tracked in
[docs/licensing-register.md](docs/licensing-register.md). See
[CONTRIBUTING.md](CONTRIBUTING.md) before adding a source.
