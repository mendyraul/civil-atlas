# Historical research toolkit

Civil Atlas keeps MapLibre/Next.js and FastAPI/PostGIS. The toolkit adapts the
portable design patterns from God's Eye View: linked views, world-anchored
annotations, attributed episode packs, and one read-only query service exposed
through HTTP and MCP. No Cesium application or upstream datasets are bundled.

## Geography and review

Curated territory uses a reviewed, published `CivilizationLayer`, referenced by
ID. Its original Polygon/MultiPolygon geometry, holes and islands are preserved.
A personal sketch never becomes an authoritative polity boundary. Reviewed,
non-placeholder source variants take priority over schematic primary seed layers;
visitors can still explicitly compare available interpretations.

Run `python -m app.ingestion.audit_geometry` against the configured database to
report topology, vertex counts, source references, import hashes and regional
extents. These checks do not establish historical accuracy. Do not snap ancient
borders to modern country lines or silently clip historical coastlines. Any
correction must retain the raw source, describe the change, and receive review.

The local implementation exercise downloaded original Cliopatria v021 bytes
(SHA-256 `e10a4e429fca708788ff9e7572a95fce801fae55852d217cffabc1c59cd4eed4`).
The 117 CE selection produces seven mapped layers and 29 omissions. All seven
pass PostGIS topology checks; Rome has 1,534 vertices. No simplification was
needed. Source review retains **low confidence**: it checks the release,
identity/date mapping, citation, license, topology and regional extent, and does
not claim independent expert historical verification.

## Visitors

- **Compare:** `/compare` offers linked maps with independent years and source
  interpretations. The polity table remains available. URLs preserve both
  selections, camera orientation and the linked/unlinked preference.
- **Map notes:** point, path and region notes are personal/unreviewed and stored
  in IndexedDB. Drawing can also use keyboard-entered coordinates. JSON import
  previews changes; export keeps a portable copy. Storage failures keep the
  current session available and request an export.
- **Area query:** search the visible bounds, a two-corner rectangle, a point and
  radius, or a reviewed historical boundary. Spatial queries intersect routes
  and territories and include places in the selected geography. Events use
  recorded polygon scope or linked, public places. Unlocated records are counted
  separately. Empty results indicate database coverage, not historical absence.
- **Episodes:** browse published packs or preview local JSON/bundles. Steps carry
  dates, camera positions, explicit layers/entities, annotations and citations.
  Playback waits for referenced geography and assets. Manual timeline/entity
  navigation stops episode playback. Reduced motion disables automatic playback.
- **Layer status:** delivery errors are separate from source interpretation,
  validity interval, review state and confidence. Source links identify the
  release and its attribution.

## Authoring and importing episodes

Canonical manifests are in `backend/data/imports/episodes/v1/`:

- `connected-world-117.json`: a three-step, source-linked geographic reading at
  117, 123 and 130 CE. Territorial annotations use Cliopatria layer IDs.
- `rome-frontier-114-118.json`: unpublished draft requiring additional snapshots
  and campaign evidence.
- `mediterranean-india-connections.json`: unpublished draft requiring reviewed
  ports, routes and exchange evidence.

From `backend`, validate a pack without a database:

```sh
python -m app.ingestion.cli --source episodes \
  --snapshot data/imports/episodes/v1/connected-world-117.json \
  --dataset-version connected-world-v1 --retrieved-at 2026-10-23T18:12:00Z \
  --actor operator:local --artifact-dir .local-artifacts --dry-run
```

Omit `--dry-run` to archive exact bytes and create private review assignments.
This command does not publish. First review the referenced sources, records,
claims and boundaries using the [existing review workflow](pleiades-pilot.md),
then approve the episode's annotations, and finally the episode. Episode
publication rejects missing, private, unreviewed, out-of-date or placeholder
boundary dependencies. Public reads revalidate dependencies, so withdrawing a
required record withdraws the public episode. Changed annotation content requires
its own new review before a changed episode can be published.

## Assets and local bundles

Assets declare an ID, kind, trusted relative path, attribution, cleared license,
SHA-256, exact byte length and geographic placement. Publish licensed assets
under `frontend/public/episode-assets/<path>`. PNG overlays require ordered
west/south/east/north bounds and dimensions no larger than 4096×4096; dateline-
crossing images must be split into separate assets. Audio/video require a
longitude/latitude anchor and use native, user-operated playback controls.
Georeferencing scans is an authoring step outside this toolkit.

The browser verifies MIME type, size and hash before creating an asset URL.
Missing assets fail explicitly; changing steps, stopping, or leaving the atlas
cancels requests and releases object URLs. Each asset is limited to 8 MiB, each
step to eight assets/32 MiB, and an imported JSON file/bundle to 32 MiB.

A local bundle has `{ "schemaVersion": 1, "pack": <episode>, "files": { ... } }`.
Each `files` key is a declared asset path with `{ "mimeType": "...", "base64":
"..." }` bytes. Undeclared files and traversal paths are rejected. Import preview
makes no asset requests. Local content is never uploaded or published, and must
be reimported after a reload; export preserves supplied bundle bytes.

## Public API

- `GET /api/v1/episodes` and `GET /api/v1/episodes/{id}` expose reviewed packs with
  valid public dependencies.
- `POST /api/v1/research/query` accepts the shared `ResearchQuery` contract.
  Operations: `entities_in_area`, `events_in_area`, `compare_boundaries`,
  `sources_for_feature`, `episodes`, `atlas_link`.
- Geographic queries require `year` and exactly one area: `bbox` in W/S/E/N
  order (west > east means crossing the dateline), `center` plus `radiusKm`, or
  `layerId`. Pagination defaults to 20 and is capped at 100 records per page.
- Results include structured records, source citations, atlas links, public data
  version, coverage limitations and an unlocated-record count.

Backend models accept camelCase and snake_case request keys; existing backend
JSON is normalized at the frontend boundary. New records use the existing
publication-gated document store and review audit, so no database schema
migration is required beyond the current PostGIS migrations.

## MCP (local stdio)

Use Python 3.12 and install the optional server dependencies:

```sh
pip install -r backend/requirements-mcp.txt
cd backend
python -m app.mcp_server
```

Configure the MCP client to launch that command with its working directory set
to `backend` and `DATABASE_URL` supplied through the client environment. Exposed
tools are `historical_research`, `discover_episodes` and `build_atlas_link`.
The first tool accepts the same query contract as HTTP. All tools are read-only,
return the same publication-filtered results, and require no editorial key or AI
provider. Clients supply geography and years explicitly; there is no browser
control bridge or public network MCP endpoint.

## Verification and operations

Run `pytest -q` against PostgreSQL/PostGIS and install `requirements-mcp.txt` for
MCP integration coverage. Frontend checks are typecheck, lint, Vitest, production
build, and Playwright. Toolkit browser tests cover persistence, linked cameras,
independent dates, episode resume/stop, research request/results, and accessibility.

Keep the archive directory with database backups. Follow the existing staging
restore drill before a public release. Check readiness, query errors, asset-load
errors and missing coverage in the deployed preview. The implementation's local
preview database is isolated from existing databases; no public deployment or
new contributor-account system is part of this rollout.
