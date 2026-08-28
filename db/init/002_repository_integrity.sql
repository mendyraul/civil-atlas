-- Repository migration: stable identifiers, versioned JSON documents, and provenance FKs.
CREATE TABLE IF NOT EXISTS atlas_entities (
  id TEXT PRIMARY KEY,
  entity_type TEXT NOT NULL,
  external_id TEXT NOT NULL,
  payload JSONB NOT NULL,
  content_hash TEXT NOT NULL,
  published BOOLEAN NOT NULL DEFAULT FALSE,
  revision_number INTEGER NOT NULL DEFAULT 1 CHECK (revision_number > 0),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (entity_type, external_id),
  UNIQUE (id, entity_type)
);

ALTER TABLE sources ADD COLUMN IF NOT EXISTS atlas_entity_id TEXT REFERENCES atlas_entities(id);
CREATE UNIQUE INDEX IF NOT EXISTS uq_sources_external_id ON sources(external_id) WHERE external_id IS NOT NULL;
ALTER TABLE source_artifacts ADD COLUMN IF NOT EXISTS external_id TEXT;
ALTER TABLE import_jobs ADD COLUMN IF NOT EXISTS external_id TEXT;
ALTER TABLE historical_claims ADD COLUMN IF NOT EXISTS external_id TEXT;
ALTER TABLE review_assignments ADD COLUMN IF NOT EXISTS external_id TEXT;
ALTER TABLE review_decisions ADD COLUMN IF NOT EXISTS external_id TEXT;
ALTER TABLE revision_records ADD COLUMN IF NOT EXISTS external_id TEXT;

CREATE UNIQUE INDEX IF NOT EXISTS uq_artifacts_external_id ON source_artifacts(external_id) WHERE external_id IS NOT NULL;
CREATE UNIQUE INDEX IF NOT EXISTS uq_import_jobs_external_id ON import_jobs(external_id) WHERE external_id IS NOT NULL;
CREATE UNIQUE INDEX IF NOT EXISTS uq_claims_external_id ON historical_claims(external_id) WHERE external_id IS NOT NULL;
CREATE UNIQUE INDEX IF NOT EXISTS uq_assignments_external_id ON review_assignments(external_id) WHERE external_id IS NOT NULL;
CREATE UNIQUE INDEX IF NOT EXISTS uq_decisions_external_id ON review_decisions(external_id) WHERE external_id IS NOT NULL;
CREATE UNIQUE INDEX IF NOT EXISTS uq_revisions_external_id ON revision_records(external_id) WHERE external_id IS NOT NULL;

-- Provenance records are no longer independent strings: every resolvable link is enforced.
ALTER TABLE source_artifacts
  ADD CONSTRAINT fk_artifact_source FOREIGN KEY (source_record_id) REFERENCES sources(id),
  ADD CONSTRAINT fk_artifact_claim FOREIGN KEY (claim_id) REFERENCES historical_claims(id),
  ADD CONSTRAINT fk_artifact_layer FOREIGN KEY (layer_id) REFERENCES civilization_layers(id),
  ADD CONSTRAINT fk_artifact_import FOREIGN KEY (import_job_id) REFERENCES import_jobs(id),
  ADD CONSTRAINT fk_artifact_parent FOREIGN KEY (derived_from_artifact_id) REFERENCES source_artifacts(id);
ALTER TABLE import_jobs
  ADD CONSTRAINT fk_import_manifest FOREIGN KEY (manifest_artifact_id) REFERENCES source_artifacts(id) DEFERRABLE INITIALLY DEFERRED;
ALTER TABLE review_decisions
  ADD CONSTRAINT fk_decision_assignment FOREIGN KEY (assignment_id) REFERENCES review_assignments(id);
ALTER TABLE revision_records
  ADD CONSTRAINT fk_revision_entity FOREIGN KEY (entity_id) REFERENCES atlas_entities(id),
  ADD CONSTRAINT fk_revision_artifact FOREIGN KEY (artifact_id) REFERENCES source_artifacts(id),
  ADD CONSTRAINT fk_revision_decision FOREIGN KEY (review_decision_id) REFERENCES review_decisions(id);

CREATE INDEX IF NOT EXISTS idx_atlas_entities_version ON atlas_entities(updated_at, revision_number);
CREATE INDEX IF NOT EXISTS idx_atlas_entities_public ON atlas_entities(entity_type, published, external_id);
