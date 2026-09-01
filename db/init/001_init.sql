CREATE EXTENSION IF NOT EXISTS postgis;

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
  variant_group TEXT,
  interpretation_label TEXT,
  interpretation_kind TEXT,
  is_primary BOOLEAN NOT NULL DEFAULT FALSE,
  display_order INTEGER NOT NULL DEFAULT 0,
  valid_from_year INTEGER NOT NULL,
  valid_to_year INTEGER NOT NULL,
  geometry_json JSONB,
  geom geometry(Geometry, 4326),
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
  geom geometry(Point, 4326),
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
  path_geojson JSONB,
  geom geometry(LineString, 4326)
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
  dataset_version TEXT,
  reliability_tier TEXT NOT NULL,
  retrieved_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS source_artifacts (
  id TEXT PRIMARY KEY,
  artifact_type TEXT NOT NULL,
  storage_provider TEXT NOT NULL,
  bucket TEXT NOT NULL,
  object_key TEXT NOT NULL,
  mime_type TEXT NOT NULL,
  byte_size INTEGER NOT NULL,
  sha256 TEXT NOT NULL,
  source_record_id TEXT,
  claim_id TEXT,
  layer_id TEXT,
  import_job_id TEXT,
  derived_from_artifact_id TEXT,
  metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS import_jobs (
  id TEXT PRIMARY KEY,
  dataset_slug TEXT NOT NULL,
  dataset_label TEXT NOT NULL,
  status TEXT NOT NULL,
  source_type TEXT NOT NULL,
  bucket TEXT NOT NULL,
  object_prefix TEXT NOT NULL,
  initiated_by TEXT NOT NULL,
  manifest_artifact_id TEXT,
  started_at TIMESTAMPTZ,
  completed_at TIMESTAMPTZ,
  records_discovered INTEGER NOT NULL DEFAULT 0,
  records_imported INTEGER NOT NULL DEFAULT 0,
  artifacts_created INTEGER NOT NULL DEFAULT 0,
  notes TEXT NOT NULL
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

CREATE TABLE IF NOT EXISTS historical_relationships (
  id TEXT PRIMARY KEY,
  relationship_type TEXT NOT NULL,
  subject_id TEXT NOT NULL,
  subject_kind TEXT NOT NULL,
  target_id TEXT NOT NULL,
  target_kind TEXT NOT NULL,
  label TEXT NOT NULL,
  summary TEXT NOT NULL,
  valid_from_year INTEGER NOT NULL,
  valid_to_year INTEGER NOT NULL,
  confidence_level TEXT NOT NULL,
  review_status TEXT NOT NULL,
  source_note TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS review_assignments (
  id TEXT PRIMARY KEY,
  entity_type TEXT NOT NULL,
  entity_id TEXT NOT NULL,
  current_review_status TEXT NOT NULL,
  target_review_status TEXT NOT NULL,
  assigned_reviewer TEXT NOT NULL,
  assigned_by TEXT NOT NULL,
  priority TEXT NOT NULL,
  due_at TIMESTAMPTZ,
  notes TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS review_decisions (
  id TEXT PRIMARY KEY,
  assignment_id TEXT NOT NULL,
  entity_type TEXT NOT NULL,
  entity_id TEXT NOT NULL,
  decision_type TEXT NOT NULL,
  previous_review_status TEXT NOT NULL,
  new_review_status TEXT NOT NULL,
  reviewer TEXT NOT NULL,
  rationale TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS revision_records (
  id TEXT PRIMARY KEY,
  entity_type TEXT NOT NULL,
  entity_id TEXT NOT NULL,
  revision_kind TEXT NOT NULL,
  summary TEXT NOT NULL,
  diff_excerpt TEXT NOT NULL,
  actor TEXT NOT NULL,
  artifact_id TEXT,
  review_decision_id TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS historical_claim_sources (
  claim_id TEXT NOT NULL REFERENCES historical_claims(id) ON DELETE CASCADE,
  source_id TEXT NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
  PRIMARY KEY (claim_id, source_id)
);

CREATE TABLE IF NOT EXISTS external_ids (
  id BIGSERIAL PRIMARY KEY,
  entity_kind TEXT NOT NULL,
  entity_id TEXT NOT NULL,
  scheme TEXT NOT NULL,
  external_id TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (entity_kind, entity_id, scheme),
  UNIQUE (scheme, external_id)
);

CREATE INDEX IF NOT EXISTS idx_civilization_layers_civilization_id
  ON civilization_layers (civilization_id);

CREATE INDEX IF NOT EXISTS idx_civilization_layers_geom
  ON civilization_layers USING GIST (geom);

CREATE INDEX IF NOT EXISTS idx_places_geom
  ON places USING GIST (geom);

CREATE INDEX IF NOT EXISTS idx_civilization_edges_geom
  ON civilization_edges USING GIST (geom);

CREATE INDEX IF NOT EXISTS idx_external_ids_entity
  ON external_ids (entity_kind, entity_id);

CREATE INDEX IF NOT EXISTS idx_places_slug
  ON places (slug);

CREATE INDEX IF NOT EXISTS idx_civilization_places_lookup
  ON civilization_places (civilization_id, place_id);

CREATE INDEX IF NOT EXISTS idx_civilization_edges_lookup
  ON civilization_edges (civilization_id, source_place_id, target_place_id);

CREATE INDEX IF NOT EXISTS idx_evidence_links_entity
  ON evidence_links (entity_type, entity_id);

CREATE INDEX IF NOT EXISTS idx_source_artifacts_source_record
  ON source_artifacts (source_record_id, artifact_type);

CREATE INDEX IF NOT EXISTS idx_import_jobs_dataset_status
  ON import_jobs (dataset_slug, status);

CREATE INDEX IF NOT EXISTS idx_historical_claims_subject_ref
  ON historical_claims (subject_kind, subject_id);

CREATE INDEX IF NOT EXISTS idx_historical_relationships_subject_target
  ON historical_relationships (subject_kind, subject_id, target_kind, target_id);

CREATE INDEX IF NOT EXISTS idx_review_assignments_entity
  ON review_assignments (entity_type, entity_id, priority);

CREATE INDEX IF NOT EXISTS idx_revision_records_entity
  ON revision_records (entity_type, entity_id, revision_kind);
