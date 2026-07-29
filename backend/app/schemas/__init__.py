from pydantic import BaseModel


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
    metadata_json: dict[str, object] = {}
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


class HistoricalClaim(BaseModel):
    id: str
    claim_type: str
    subject_id: str
    subject_kind: str
    object_id: str | None = None
    object_kind: str | None = None
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
    geometry_json: dict[str, object] | None = None
    geometry_placeholder: str | None = None
    confidence: str
    review_status: str
    source_note: str
    created_at: str
    updated_at: str
    source_record_ids: list[str]
    claim_ids: list[str]


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
    polygon: list[tuple[float, float]]
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
