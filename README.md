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
- Database: PostgreSQL with PostGIS-ready GeoJSON placeholders
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
npm install
npm run dev
```

## Seed data

The current seed spans roughly `600 BCE` to `1800 CE`, with `117 CE` as the
main focal year. It includes seven civilizations, a small place set, a small
edge set, and manual source/evidence records.

## Source-of-truth philosophy

Civil Atlas treats the database as the canonical operational model for the app.
That model is still provisional: every canonical object should point back to
sources, claims, confidence levels, review status, and valid time ranges.

## Known limitations

- Boundaries are schematic placeholder or source-reported approximations
- No external source ingestion yet
- No PostGIS geometry columns yet
- No persistence/write workflow yet; seed data still lives in code
- The frontend is still optimized for the MVP atlas flow, not a full research UI
