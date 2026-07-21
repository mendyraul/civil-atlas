CREATE TABLE IF NOT EXISTS civilizations (
  id TEXT PRIMARY KEY,
  slug TEXT NOT NULL UNIQUE,
  name TEXT NOT NULL,
  type TEXT NOT NULL,
  start_year INTEGER NOT NULL,
  end_year INTEGER NOT NULL,
  description TEXT NOT NULL,
  display_color TEXT NOT NULL,
  confidence_level TEXT NOT NULL,
  review_status TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS civilization_layers (
  id TEXT PRIMARY KEY,
  civilization_id TEXT NOT NULL REFERENCES civilizations(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  layer_type TEXT NOT NULL,
  valid_from_year INTEGER NOT NULL,
  valid_to_year INTEGER NOT NULL,
  geometry_json JSONB,
  geometry_placeholder TEXT,
  confidence_level TEXT NOT NULL,
  review_status TEXT NOT NULL,
  source_note TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON COLUMN civilization_layers.geometry_json IS
  'GeoJSON placeholder storage for MVP seed layers. Planned future migration path: geometry(MultiPolygon, 4326) or vector-tile source tables.';

CREATE TABLE IF NOT EXISTS places (
  id TEXT PRIMARY KEY,
  slug TEXT NOT NULL UNIQUE,
  canonical_name TEXT NOT NULL,
  modern_name TEXT,
  latitude DOUBLE PRECISION NOT NULL,
  longitude DOUBLE PRECISION NOT NULL,
  start_year INTEGER NOT NULL,
  end_year INTEGER NOT NULL,
  place_type TEXT NOT NULL,
  confidence_level TEXT NOT NULL,
  review_status TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS civilization_places (
  id TEXT PRIMARY KEY,
  civilization_id TEXT NOT NULL REFERENCES civilizations(id) ON DELETE CASCADE,
  place_id TEXT NOT NULL REFERENCES places(id) ON DELETE CASCADE,
  valid_from_year INTEGER NOT NULL,
  valid_to_year INTEGER NOT NULL,
  role TEXT NOT NULL,
  importance_score NUMERIC(4, 2) NOT NULL,
  confidence_level TEXT NOT NULL,
  review_status TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS civilization_edges (
  id TEXT PRIMARY KEY,
  civilization_id TEXT NOT NULL REFERENCES civilizations(id) ON DELETE CASCADE,
  source_place_id TEXT NOT NULL REFERENCES places(id) ON DELETE CASCADE,
  target_place_id TEXT NOT NULL REFERENCES places(id) ON DELETE CASCADE,
  valid_from_year INTEGER NOT NULL,
  valid_to_year INTEGER NOT NULL,
  edge_type TEXT NOT NULL,
  estimated_travel_days_min INTEGER,
  estimated_travel_days_max INTEGER,
  confidence_level TEXT NOT NULL,
  review_status TEXT NOT NULL,
  source_note TEXT NOT NULL,
  path_geojson JSONB
);

COMMENT ON COLUMN civilization_edges.path_geojson IS
  'Optional MVP route polyline as GeoJSON until PostGIS line geometry is enabled.';

CREATE TABLE IF NOT EXISTS sources (
  id TEXT PRIMARY KEY,
  source_name TEXT NOT NULL,
  source_type TEXT NOT NULL,
  external_id TEXT,
  url TEXT,
  citation TEXT NOT NULL,
  license TEXT NOT NULL,
  reliability_tier TEXT NOT NULL,
  retrieved_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS evidence_links (
  id TEXT PRIMARY KEY,
  source_id TEXT NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
  entity_type TEXT NOT NULL,
  entity_id TEXT NOT NULL,
  claim_type TEXT NOT NULL,
  confidence_level TEXT NOT NULL,
  quote_or_note TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS historical_claims (
  id TEXT PRIMARY KEY,
  claim_type TEXT NOT NULL,
  subject_id TEXT NOT NULL,
  subject_kind TEXT NOT NULL,
  object_id TEXT,
  object_kind TEXT,
  valid_from_year INTEGER,
  valid_to_year INTEGER,
  confidence_level TEXT NOT NULL,
  review_status TEXT NOT NULL,
  notes TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS historical_claim_sources (
  claim_id TEXT NOT NULL REFERENCES historical_claims(id) ON DELETE CASCADE,
  source_id TEXT NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
  PRIMARY KEY (claim_id, source_id)
);

CREATE INDEX IF NOT EXISTS idx_civilization_layers_civilization_id
  ON civilization_layers (civilization_id);

CREATE INDEX IF NOT EXISTS idx_places_slug
  ON places (slug);

CREATE INDEX IF NOT EXISTS idx_civilization_places_lookup
  ON civilization_places (civilization_id, place_id);

CREATE INDEX IF NOT EXISTS idx_civilization_edges_lookup
  ON civilization_edges (civilization_id, source_place_id, target_place_id);

CREATE INDEX IF NOT EXISTS idx_evidence_links_entity
  ON evidence_links (entity_type, entity_id);

CREATE INDEX IF NOT EXISTS idx_historical_claims_subject_ref
  ON historical_claims (subject_kind, subject_id);
