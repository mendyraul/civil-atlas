from math import isfinite
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


Position = tuple[float, float]


class GeoJSONGeometry(BaseModel):
    """A validated RFC 7946 territorial geometry (longitude, latitude)."""

    type: Literal["Polygon", "MultiPolygon"]
    coordinates: Any

    @model_validator(mode="after")
    def validate_coordinates(self) -> "GeoJSONGeometry":
        polygons = self.coordinates if self.type == "MultiPolygon" else [self.coordinates]
        if not isinstance(polygons, list) or not polygons:
            raise ValueError("geometry must contain at least one polygon")
        for polygon in polygons:
            if not isinstance(polygon, list) or not polygon:
                raise ValueError("each polygon must contain an exterior ring")
            for ring in polygon:
                if not isinstance(ring, list) or len(ring) < 4:
                    raise ValueError("each linear ring must contain at least four positions")
                normalized: list[Position] = []
                for position in ring:
                    if not isinstance(position, (list, tuple)) or len(position) != 2:
                        raise ValueError("positions must be [longitude, latitude] pairs")
                    longitude, latitude = position
                    if isinstance(longitude, bool) or isinstance(latitude, bool):
                        raise ValueError("coordinates must be numbers")
                    try:
                        longitude, latitude = float(longitude), float(latitude)
                    except (TypeError, ValueError) as exc:
                        raise ValueError("coordinates must be numbers") from exc
                    if not isfinite(longitude) or not isfinite(latitude):
                        raise ValueError("coordinates must be finite")
                    if not -180 <= longitude <= 180 or not -90 <= latitude <= 90:
                        raise ValueError(
                            "positions use GeoJSON [longitude, latitude] order; longitude must be "
                            "within [-180, 180] and latitude within [-90, 90]"
                        )
                    normalized.append((longitude, latitude))
                if normalized[0] != normalized[-1]:
                    raise ValueError("linear rings must be closed (first and last positions equal)")
        return self


class EvidenceRecord(BaseModel):
    id: str
    title: str
    citation: str
    link: str | None = None
    confidence: str
    review_status: str
    notes: str


class SourceRecord(BaseModel):
    id: str
    feature_id: str
    feature_kind: str
    feature_label: str
    title: str
    citation: str
    link: str | None = None
    source_namespace: str = "manual_seed"
    confidence: str
    review_status: str
    notes: str
    valid_from_year: int | None = None
    valid_to_year: int | None = None


class StorageBucketContract(BaseModel):
    name: str
    prefix: str
    purpose: str


class StorageContractView(BaseModel):
    provider: str
    endpoint: str
    public_base_url: str | None = None
    region: str
    use_path_style: bool
    signed_url_ttl_seconds: int
    raw: StorageBucketContract
    normalized: StorageBucketContract
    derived: StorageBucketContract
    exports: StorageBucketContract


class SourceArtifact(BaseModel):
    id: str
    artifact_type: str
    storage_provider: str
    bucket: str
    object_key: str
    mime_type: str
    byte_size: int
    sha256: str
    source_record_id: str | None = None
    claim_id: str | None = None
    layer_id: str | None = None
    import_job_id: str | None = None
    derived_from_artifact_id: str | None = None
    metadata_json: dict[str, object] = Field(default_factory=dict)
    created_at: str
    updated_at: str


class ImportJob(BaseModel):
    id: str
    dataset_slug: str
    dataset_label: str
    status: str
    source_type: str
    bucket: str
    object_prefix: str
    initiated_by: str
    manifest_artifact_id: str | None = None
    started_at: str | None = None
    completed_at: str | None = None
    records_discovered: int = 0
    records_imported: int = 0
    artifacts_created: int = 0
    notes: str


class ArtifactIngestRecordInput(BaseModel):
    source_record_id: str
    feature_id: str
    feature_kind: str
    feature_label: str
    title: str
    citation: str
    link: str | None = None
    filename: str
    mime_type: str
    byte_size: int
    sha256: str
    confidence: str = "medium"
    review_status: str = "needs_review"
    notes: str
    source_namespace: str = "operator_upload"
    valid_from_year: int | None = None
    valid_to_year: int | None = None
    claim_id: str | None = None
    layer_id: str | None = None
    create_derived_geometry: bool = False
    geometry_json: GeoJSONGeometry | None = None
    layer_type: str | None = None
    variant_group: str | None = None
    interpretation_label: str | None = None
    interpretation_kind: str | None = None
    is_primary: bool = False
    display_order: int = 0
    is_placeholder: bool = False
    metadata_json: dict[str, object] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_ingest_range_and_layer(self) -> "ArtifactIngestRecordInput":
        if (
            self.valid_from_year is not None
            and self.valid_to_year is not None
            and self.valid_from_year > self.valid_to_year
        ):
            raise ValueError("valid_from_year must be less than or equal to valid_to_year")
        if self.geometry_json is not None and not self.layer_id:
            raise ValueError("territorial geometry must identify its civilization layer")
        if self.create_derived_geometry and (not self.layer_id or self.geometry_json is None):
            raise ValueError("derived territorial geometry requires layer_id and geometry_json")
        return self


class ArtifactIngestRequest(BaseModel):
    dataset_slug: str
    dataset_label: str
    source_type: str
    initiated_by: str
    notes: str = ""
    records: list[ArtifactIngestRecordInput] = Field(default_factory=list)


class ReviewAssignment(BaseModel):
    id: str
    entity_type: str
    entity_id: str
    current_review_status: str
    target_review_status: str
    assigned_reviewer: str
    assigned_by: str
    priority: str
    due_at: str | None = None
    notes: str
    created_at: str


class ReviewDecision(BaseModel):
    id: str
    assignment_id: str
    entity_type: str
    entity_id: str
    decision_type: str
    previous_review_status: str
    new_review_status: str
    reviewer: str
    rationale: str
    created_at: str


class RevisionRecord(BaseModel):
    id: str
    entity_type: str
    entity_id: str
    revision_kind: str
    summary: str
    diff_excerpt: str
    actor: str
    artifact_id: str | None = None
    review_decision_id: str | None = None
    created_at: str


class ArtifactIngestPlan(BaseModel):
    storage: StorageContractView
    import_job: ImportJob
    manifest_artifact: SourceArtifact
    source_records: list[SourceRecord] = Field(default_factory=list)
    artifacts: list[SourceArtifact] = Field(default_factory=list)
    review_assignments: list[ReviewAssignment] = Field(default_factory=list)
    revision_records: list[RevisionRecord] = Field(default_factory=list)


class HistoricalClaim(BaseModel):
    id: str
    claim_type: str
    predicate: str = "unspecified"
    version: int = 1
    subject_id: str
    subject_kind: str
    object_id: str | None = None
    object_kind: str | None = None
    value: str | int | float | bool | dict[str, object] | None = None
    geographic_scope: dict[str, object] | None = None
    source_id: str | None = None
    citation_locator: str | None = None
    confidence_rationale: str = ""
    supersedes_claim_id: str | None = None
    confidence: str
    review_status: str
    notes: str
    valid_from_year: int | None = None
    valid_to_year: int | None = None
    source_record_ids: list[str]


class CivilizationLayer(BaseModel):
    id: str
    civilization_id: str
    name: str
    layer_type: str
    variant_group: str | None = None
    interpretation_label: str | None = None
    interpretation_kind: str | None = None
    is_primary: bool = False
    display_order: int = 0
    valid_from_year: int
    valid_to_year: int
    geometry_json: GeoJSONGeometry
    geometry_placeholder: str | None = None
    is_placeholder: bool = False
    confidence: str
    review_status: str
    source_note: str
    created_at: str
    updated_at: str
    source_record_ids: list[str]
    claim_ids: list[str]

    @model_validator(mode="after")
    def validate_valid_range(self) -> "CivilizationLayer":
        if self.valid_from_year > self.valid_to_year:
            raise ValueError("valid_from_year must be less than or equal to valid_to_year")
        return self


class HistoricalRelationship(BaseModel):
    id: str
    relationship_type: str
    subject_id: str
    subject_kind: str
    target_id: str
    target_kind: str
    label: str
    summary: str
    valid_from_year: int
    valid_to_year: int
    confidence: str
    review_status: str
    source_note: str
    source_record_ids: list[str]
    claim_ids: list[str]


class Civilization(BaseModel):
    id: str
    slug: str
    kind: str
    label: str
    display_name: str
    start_year: int
    end_year: int
    civilization_type: str
    color: str
    color_token: str
    summary: str
    short_description: str
    capital: str
    panel_description: str
    extent_note: str
    confidence: str
    review_status: str
    source_notes: str
    status_badges: list[str]
    # Kept only so legacy seed constructors can be migrated incrementally. It
    # is never serialized; clients must render CivilizationLayer.geometry_json.
    polygon: list[tuple[float, float]] = Field(default_factory=list, exclude=True)
    evidence: list[EvidenceRecord]
    source_record_ids: list[str] = []
    claim_ids: list[str] = []


class AtlasNode(BaseModel):
    id: str
    slug: str
    kind: str
    label: str
    name: str
    modern_name: str | None = None
    node_kind: str
    place_type: str
    role: str
    civilization_id: str | None = None
    civilization_slug: str | None = None
    start_year: int
    end_year: int
    summary: str
    coordinates: tuple[float, float]
    confidence: str
    review_status: str
    source_notes: str
    status_badges: list[str]
    evidence: list[EvidenceRecord]
    source_record_ids: list[str] = []
    claim_ids: list[str] = []


class AtlasRoute(BaseModel):
    id: str
    slug: str
    kind: str
    label: str
    route_kind: str
    edge_type: str
    source_node_id: str
    target_node_id: str
    civilization_ids: list[str]
    start_year: int
    end_year: int
    summary: str
    path: list[tuple[float, float]]
    confidence: str
    review_status: str
    source_notes: str
    status_badges: list[str]
    evidence: list[EvidenceRecord]
    source_record_ids: list[str] = []
    claim_ids: list[str] = []


class Era(BaseModel):
    id: str
    slug: str
    label: str
    start_year: int
    end_year: int
    summary: str
    focus_region: str
    featured_civilization_ids: list[str]
    confidence: str
    review_status: str
    evidence: list[EvidenceRecord]


class HistoricalEvent(BaseModel):
    id: str
    slug: str
    label: str
    event_type: str
    start_year: int
    end_year: int
    display_date: str
    summary: str
    impact: str
    civilization_ids: list[str]
    place_ids: list[str]
    confidence: str
    review_status: str
    evidence: list[EvidenceRecord]


class WorldPayload(BaseModel):
    year: int
    civilizations: list[Civilization]
    nodes: list[AtlasNode]
    routes: list[AtlasRoute]
    layers: list[CivilizationLayer]
    relationships: list[HistoricalRelationship]
    eras: list[Era]
    events: list[HistoricalEvent]


class Place(BaseModel):
    id: str
    slug: str
    canonical_name: str
    modern_name: str | None = None
    latitude: float
    longitude: float
    start_year: int
    end_year: int
    place_type: str
    confidence_level: str
    review_status: str
    created_at: str
    updated_at: str


class CivilizationPlace(BaseModel):
    id: str
    civilization_id: str
    place_id: str
    valid_from_year: int
    valid_to_year: int
    role: str
    importance_score: float
    confidence_level: str
    review_status: str


class CivilizationEdge(BaseModel):
    id: str
    civilization_id: str
    source_place_id: str
    target_place_id: str
    valid_from_year: int
    valid_to_year: int
    edge_type: str
    estimated_travel_days_min: int | None = None
    estimated_travel_days_max: int | None = None
    confidence_level: str
    review_status: str
    source_note: str


class Source(BaseModel):
    id: str
    source_name: str
    source_type: str
    external_id: str | None = None
    url: str | None = None
    citation: str
    license: str
    reliability_tier: str
    retrieved_at: str | None = None
    created_at: str
    updated_at: str


class EvidenceLink(BaseModel):
    id: str
    source_id: str
    entity_type: str
    entity_id: str
    claim_type: str
    confidence_level: str
    quote_or_note: str
    created_at: str
    updated_at: str


class GlobePayload(BaseModel):
    year: int
    zoom: str
    civilizations: list[Civilization]
    layers: list[CivilizationLayer]
    places: list[Place]
    edges: list[CivilizationEdge]
    evidence_links: list[EvidenceLink]


class KnowledgeEntity(BaseModel):
    id: str
    slug: str
    kind: str
    canonical_name: str
    valid_from_year: int | None = None
    valid_to_year: int | None = None
    review_state: str
    overview_claim_ids: list[str] = Field(default_factory=list)
    chronology_event_ids: list[str] = Field(default_factory=list)
    map_layers: list[dict[str, object]] = Field(default_factory=list)
    related_entity_ids: list[str] = Field(default_factory=list)
    passage_ids: list[str] = Field(default_factory=list)


class ClaimView(BaseModel):
    id: str
    version: int
    subject_id: str
    predicate: str
    object_id: str | None = None
    value: str | int | float | bool | dict[str, object] | None = None
    valid_from_year: int | None = None
    valid_to_year: int | None = None
    geographic_scope: dict[str, object] | None = None
    source_id: str
    citation_locator: str
    confidence: str
    confidence_rationale: str
    review_state: str
    supersedes_claim_id: str | None = None


class ComparisonView(BaseModel):
    entities: list[KnowledgeEntity]
    shared_predicates: list[str]
    claims_by_entity: dict[str, list[ClaimView]]


class SearchResult(BaseModel):
    id: str
    kind: str
    label: str
    matched_claim_ids: list[str] = Field(default_factory=list)


class GraphView(BaseModel):
    nodes: list[KnowledgeEntity]
    edges: list[dict[str, object]]
