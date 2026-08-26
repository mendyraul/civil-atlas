from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    MetaData,
    Numeric,
    String,
    Table,
    Text,
    CheckConstraint,
    UniqueConstraint,
)

metadata = MetaData()

civilizations = Table(
    "civilizations",
    metadata,
    Column("id", String(64), primary_key=True),
    Column("slug", String(255), nullable=False, unique=True),
    Column("name", String(255), nullable=False),
    Column("type", String(64), nullable=False),
    Column("start_year", Integer, nullable=False),
    Column("end_year", Integer, nullable=False),
    Column("description", Text, nullable=False),
    Column("display_color", String(64), nullable=False),
    Column("confidence_level", String(64), nullable=False),
    Column("review_status", String(64), nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
)

civilization_layers = Table(
    "civilization_layers",
    metadata,
    Column("id", String(64), primary_key=True),
    Column("civilization_id", ForeignKey("civilizations.id"), nullable=False),
    Column("name", String(255), nullable=False),
    Column("layer_type", String(64), nullable=False),
    Column("variant_group", String(128), nullable=True),
    Column("interpretation_label", String(255), nullable=True),
    Column("interpretation_kind", String(64), nullable=True),
    Column("is_primary", Integer, nullable=False, default=0),
    Column("display_order", Integer, nullable=False, default=0),
    Column("valid_from_year", Integer, nullable=False),
    Column("valid_to_year", Integer, nullable=False),
    Column("geometry_json", JSON, nullable=True),
    Column("geometry_placeholder", Text, nullable=True),
    Column("confidence_level", String(64), nullable=False),
    Column("review_status", String(64), nullable=False),
    Column("source_note", Text, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
)

places = Table(
    "places",
    metadata,
    Column("id", String(64), primary_key=True),
    Column("slug", String(255), nullable=False, unique=True),
    Column("canonical_name", String(255), nullable=False),
    Column("modern_name", String(255), nullable=True),
    Column("latitude", String(32), nullable=False),
    Column("longitude", String(32), nullable=False),
    Column("start_year", Integer, nullable=False),
    Column("end_year", Integer, nullable=False),
    Column("place_type", String(64), nullable=False),
    Column("confidence_level", String(64), nullable=False),
    Column("review_status", String(64), nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
)

civilization_places = Table(
    "civilization_places",
    metadata,
    Column("id", String(64), primary_key=True),
    Column("civilization_id", ForeignKey("civilizations.id"), nullable=False),
    Column("place_id", ForeignKey("places.id"), nullable=False),
    Column("valid_from_year", Integer, nullable=False),
    Column("valid_to_year", Integer, nullable=False),
    Column("role", String(64), nullable=False),
    Column("importance_score", Numeric(4, 2), nullable=False),
    Column("confidence_level", String(64), nullable=False),
    Column("review_status", String(64), nullable=False),
)

civilization_edges = Table(
    "civilization_edges",
    metadata,
    Column("id", String(64), primary_key=True),
    Column("civilization_id", ForeignKey("civilizations.id"), nullable=False),
    Column("source_place_id", ForeignKey("places.id"), nullable=False),
    Column("target_place_id", ForeignKey("places.id"), nullable=False),
    Column("valid_from_year", Integer, nullable=False),
    Column("valid_to_year", Integer, nullable=False),
    Column("edge_type", String(64), nullable=False),
    Column("estimated_travel_days_min", Integer, nullable=True),
    Column("estimated_travel_days_max", Integer, nullable=True),
    Column("confidence_level", String(64), nullable=False),
    Column("review_status", String(64), nullable=False),
    Column("source_note", Text, nullable=False),
    Column(
        "path_geojson",
        JSON,
        nullable=True,
        comment="Optional MVP route polyline as GeoJSON until PostGIS line geometry is enabled.",
    ),
)

sources = Table(
    "sources",
    metadata,
    Column("id", String(64), primary_key=True),
    Column("source_name", String(255), nullable=False),
    Column("source_type", String(64), nullable=False),
    Column("external_id", String(255), nullable=True),
    Column("url", Text, nullable=True),
    Column("citation", Text, nullable=False),
    Column("license", String(64), nullable=False),
    Column("reliability_tier", String(64), nullable=False),
    Column("retrieved_at", DateTime(timezone=True), nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
)

source_artifacts = Table(
    "source_artifacts",
    metadata,
    Column("id", String(64), primary_key=True),
    Column("artifact_type", String(64), nullable=False),
    Column("storage_provider", String(64), nullable=False),
    Column("bucket", String(255), nullable=False),
    Column("object_key", Text, nullable=False),
    Column("mime_type", String(128), nullable=False),
    Column("byte_size", Integer, nullable=False),
    Column("sha256", String(128), nullable=False),
    Column("source_record_id", String(64), nullable=True),
    Column("claim_id", String(64), nullable=True),
    Column("layer_id", String(64), nullable=True),
    Column("import_job_id", String(64), nullable=True),
    Column("derived_from_artifact_id", String(64), nullable=True),
    Column("metadata_json", JSON, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
)

import_jobs = Table(
    "import_jobs",
    metadata,
    Column("id", String(64), primary_key=True),
    Column("dataset_slug", String(128), nullable=False),
    Column("dataset_label", String(255), nullable=False),
    Column("status", String(64), nullable=False),
    Column("source_type", String(64), nullable=False),
    Column("bucket", String(255), nullable=False),
    Column("object_prefix", Text, nullable=False),
    Column("initiated_by", String(255), nullable=False),
    Column("manifest_artifact_id", String(64), nullable=True),
    Column("started_at", DateTime(timezone=True), nullable=True),
    Column("completed_at", DateTime(timezone=True), nullable=True),
    Column("records_discovered", Integer, nullable=False),
    Column("records_imported", Integer, nullable=False),
    Column("artifacts_created", Integer, nullable=False),
    Column("notes", Text, nullable=False),
)

evidence_links = Table(
    "evidence_links",
    metadata,
    Column("id", String(64), primary_key=True),
    Column("source_id", ForeignKey("sources.id"), nullable=False),
    Column("entity_type", String(64), nullable=False),
    Column("entity_id", String(64), nullable=False),
    Column("claim_type", String(64), nullable=False),
    Column("confidence_level", String(64), nullable=False),
    Column("quote_or_note", Text, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
)

historical_claims = Table(
    "historical_claims",
    metadata,
    Column("id", String(64), primary_key=True),
    Column("claim_type", String(64), nullable=False),
    Column("predicate", String(128), nullable=False, server_default="unspecified"),
    Column("version", Integer, nullable=False, server_default="1"),
    Column("subject_id", String(64), nullable=False),
    Column("subject_kind", String(64), nullable=False),
    Column("object_id", String(64), nullable=True),
    Column("object_kind", String(64), nullable=True),
    Column("value_json", JSON, nullable=True),
    Column("geographic_scope_json", JSON, nullable=True),
    Column("source_id", ForeignKey("sources.id"), nullable=True),
    Column("citation_locator", String(255), nullable=True),
    Column("confidence_rationale", Text, nullable=False, server_default=""),
    Column("supersedes_claim_id", ForeignKey("historical_claims.id"), nullable=True),
    Column("valid_from_year", Integer, nullable=True),
    Column("valid_to_year", Integer, nullable=True),
    Column("confidence_level", String(64), nullable=False),
    Column("review_status", String(64), nullable=False),
    Column("notes", Text, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    CheckConstraint("object_id IS NOT NULL OR value_json IS NOT NULL", name="ck_claim_object_or_value"),
    UniqueConstraint("id", "version", name="uq_claim_version"),
)

historical_relationships = Table(
    "historical_relationships",
    metadata,
    Column("id", String(64), primary_key=True),
    Column("relationship_type", String(64), nullable=False),
    Column("subject_id", String(64), nullable=False),
    Column("subject_kind", String(64), nullable=False),
    Column("target_id", String(64), nullable=False),
    Column("target_kind", String(64), nullable=False),
    Column("label", String(255), nullable=False),
    Column("summary", Text, nullable=False),
    Column("valid_from_year", Integer, nullable=False),
    Column("valid_to_year", Integer, nullable=False),
    Column("confidence_level", String(64), nullable=False),
    Column("review_status", String(64), nullable=False),
    Column("source_note", Text, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
)

relationship_claims = Table(
    "relationship_claims",
    metadata,
    Column("relationship_id", ForeignKey("historical_relationships.id"), primary_key=True),
    Column("claim_id", ForeignKey("historical_claims.id"), primary_key=True),
)

# Every knowledge-domain record is addressable through this registry.  Type-specific
# tables keep fields typed without turning factual assertions into biography prose.
entities = Table(
    "entities", metadata,
    Column("id", String(64), primary_key=True),
    Column("slug", String(255), nullable=False, unique=True),
    Column("entity_kind", String(64), nullable=False),
    Column("canonical_name", String(255), nullable=False),
    Column("valid_from_year", Integer, nullable=True),
    Column("valid_to_year", Integer, nullable=True),
    Column("review_status", String(64), nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
)

people = Table(
    "people", metadata,
    Column("entity_id", ForeignKey("entities.id"), primary_key=True),
    Column("birth_year", Integer, nullable=True),
    Column("death_year", Integer, nullable=True),
)

offices = Table(
    "offices", metadata,
    Column("entity_id", ForeignKey("entities.id"), primary_key=True),
    Column("jurisdiction_entity_id", ForeignKey("entities.id"), nullable=True),
    Column("office_category", String(64), nullable=False),
)

dynasties = Table(
    "dynasties", metadata,
    Column("entity_id", ForeignKey("entities.id"), primary_key=True),
    Column("founder_entity_id", ForeignKey("entities.id"), nullable=True),
)

events = Table(
    "events", metadata,
    Column("entity_id", ForeignKey("entities.id"), primary_key=True),
    Column("event_type", String(64), nullable=False),
    Column("place_entity_id", ForeignKey("entities.id"), nullable=True),
)

concepts = Table(
    "concepts", metadata,
    Column("entity_id", ForeignKey("entities.id"), primary_key=True),
    Column("concept_category", String(64), nullable=False),
)

artifacts = Table(
    "artifacts", metadata,
    Column("entity_id", ForeignKey("entities.id"), primary_key=True),
    Column("artifact_category", String(64), nullable=False),
    Column("holding_institution", String(255), nullable=True),
    Column("catalog_identifier", String(255), nullable=True),
)

primary_source_passages = Table(
    "primary_source_passages", metadata,
    Column("entity_id", ForeignKey("entities.id"), primary_key=True),
    Column("source_id", ForeignKey("sources.id"), nullable=False),
    Column("citation_locator", String(255), nullable=False),
    Column("language", String(32), nullable=True),
    Column("passage_text", Text, nullable=False),
    Column("translation_text", Text, nullable=True),
)

thematic_metrics = Table(
    "thematic_metrics", metadata,
    Column("entity_id", ForeignKey("entities.id"), primary_key=True),
    Column("subject_entity_id", ForeignKey("entities.id"), nullable=False),
    Column("metric_key", String(128), nullable=False),
    Column("numeric_value", Numeric(18, 6), nullable=False),
    Column("unit", String(64), nullable=False),
    Column("methodology_claim_id", ForeignKey("historical_claims.id"), nullable=False),
)

review_assignments = Table(
    "review_assignments",
    metadata,
    Column("id", String(64), primary_key=True),
    Column("entity_type", String(64), nullable=False),
    Column("entity_id", String(64), nullable=False),
    Column("current_review_status", String(64), nullable=False),
    Column("target_review_status", String(64), nullable=False),
    Column("assigned_reviewer", String(255), nullable=False),
    Column("assigned_by", String(255), nullable=False),
    Column("priority", String(64), nullable=False),
    Column("due_at", DateTime(timezone=True), nullable=True),
    Column("notes", Text, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
)

review_decisions = Table(
    "review_decisions",
    metadata,
    Column("id", String(64), primary_key=True),
    Column("assignment_id", String(64), nullable=False),
    Column("entity_type", String(64), nullable=False),
    Column("entity_id", String(64), nullable=False),
    Column("decision_type", String(64), nullable=False),
    Column("previous_review_status", String(64), nullable=False),
    Column("new_review_status", String(64), nullable=False),
    Column("reviewer", String(255), nullable=False),
    Column("rationale", Text, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
)

revision_records = Table(
    "revision_records",
    metadata,
    Column("id", String(64), primary_key=True),
    Column("entity_type", String(64), nullable=False),
    Column("entity_id", String(64), nullable=False),
    Column("revision_kind", String(64), nullable=False),
    Column("summary", Text, nullable=False),
    Column("diff_excerpt", Text, nullable=False),
    Column("actor", String(255), nullable=False),
    Column("artifact_id", String(64), nullable=True),
    Column("review_decision_id", String(64), nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
)
