-- Backfill PostGIS and concordance support for databases initialized before
-- the native geometry migration. This file is idempotent by design.
CREATE EXTENSION IF NOT EXISTS postgis;

ALTER TABLE civilization_layers
  ADD COLUMN IF NOT EXISTS geom geometry(Geometry, 4326);
ALTER TABLE civilization_layers
  ADD COLUMN IF NOT EXISTS is_placeholder BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE places
  ADD COLUMN IF NOT EXISTS geom geometry(Point, 4326);
ALTER TABLE civilization_edges
  ADD COLUMN IF NOT EXISTS geom geometry(LineString, 4326);
ALTER TABLE sources
  ADD COLUMN IF NOT EXISTS dataset_version TEXT;

CREATE INDEX IF NOT EXISTS idx_civilization_layers_geom
  ON civilization_layers USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_places_geom
  ON places USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_civilization_edges_geom
  ON civilization_edges USING GIST (geom);

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

CREATE INDEX IF NOT EXISTS idx_external_ids_entity
  ON external_ids (entity_kind, entity_id);
