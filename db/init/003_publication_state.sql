-- Publication migration for databases initialized before the explicit public
-- release gate was introduced.
ALTER TABLE atlas_entities
  ADD COLUMN IF NOT EXISTS published BOOLEAN NOT NULL DEFAULT FALSE;

CREATE INDEX IF NOT EXISTS idx_atlas_entities_public
  ON atlas_entities(entity_type, published, external_id);
