from datetime import datetime, timezone
from hmac import compare_digest
from uuid import uuid4

from fastapi import APIRouter, Depends, Header, HTTPException, Query

from app.core.config import settings
from app.schemas import (
    ArtifactIngestPlan,
    ArtifactIngestRequest,
    AtlasNode,
    AtlasRoute,
    ClaimView,
    Civilization,
    CivilizationEdge,
    CivilizationLayer,
    CivilizationPlace,
    Era,
    EvidenceLink,
    GlobePayload,
    HistoricalClaim,
    HistoricalEvent,
    HistoricalRelationship,
    ImportJob,
    AttemptFeedback,
    AttemptRequest,
    Lesson,
    Place,
    ReviewAssignment,
    ReviewDecision,
    ReviewActionRequest,
    RevisionRecord,
    Source,
    SourceArtifact,
    StorageBucketContract,
    StorageContractView,
    SourceRecord,
    WorldPayload,
    ComparisonView,
    CoveragePack,
    GraphView,
    KnowledgeEntity,
    SearchResult,
)
from app.services.atlas import (
    YEAR_MAX, YEAR_MIN, get_data_version, get_entity, get_globe, get_places,
    get_world, list_entities, search_entity_payloads,
)
from app.services.ingest import build_ingest_plan
from app.services.learning import LESSONS, grade_attempt
from app.db.session import session_scope
from app.services.repository import AtlasRepository
from app.seed.coverage import COVERAGE_PACKS

router = APIRouter(tags=["world"])
api_router = APIRouter(tags=["api"])


def require_editorial_key(
    editorial_key: str | None = Header(default=None, alias="X-Editorial-Key"),
) -> None:
    """Protect operational import/review metadata from visitor-facing clients."""
    if settings.app_env == "development" and not settings.editorial_api_key:
        return
    if not settings.editorial_api_key or not editorial_key or not compare_digest(
        editorial_key, settings.editorial_api_key
    ):
        raise HTTPException(status_code=401, detail="editorial authorization required")


def _validate_year(year: int) -> int:
    if year < YEAR_MIN or year > YEAR_MAX:
        raise HTTPException(
            status_code=400,
            detail="Year must stay within the current seed range of 600 BCE to 1800 CE.",
        )
    return year


def _validate_zoom(zoom: str) -> str:
    if zoom not in {"world", "regional", "local"}:
        raise HTTPException(
            status_code=400,
            detail="Zoom must be one of: world, regional, local.",
        )
    return zoom


ENTITY_ALIASES = {
    "roman-empire": ["Rome", "Imperium Romanum"],
    "han-dynasty": ["Han", "漢朝", "Hàn cháo"],
    "parthian-empire": ["Parthia", "Arsacid Empire"],
    "aksumite-kingdom": ["Aksum", "Axum"],
    "changan": ["Chang'an", "Changan", "長安"],
    "ctesiphon": ["Tisfun", "al-Mada’in"],
}


@router.get("/search")
def search_catalog(
    q: str = Query(default=""), start_year: int | None = None, end_year: int | None = None,
    region: str | None = None, polity_type: str | None = None, topic: str | None = None,
    confidence: str | None = None, review_status: str | None = None,
    page: int = Query(default=1, ge=1), page_size: int = Query(default=20, ge=1, le=100),
    sort: str = Query(default="relevance"),
) -> dict[str, object]:
    """Server-side catalog search; the seed implementation mirrors a future FTS index contract."""
    records: list[dict[str, object]] = []
    for data in search_entity_payloads(("civilizations", "nodes", "routes", "events", "source_records")):
        entity_id = str(data.get("id", "")); kind = str(data.get("kind") or data.get("feature_kind") or ("event" if "event_type" in data else "source"))
        title = str(data.get("display_name") or data.get("label") or data.get("title"))
        summary = str(data.get("summary") or data.get("notes") or data.get("citation") or "")
        aliases = ENTITY_ALIASES.get(entity_id, [])
        haystack = " ".join([title, summary, str(data), *aliases]).casefold()
        if q and q.casefold() not in haystack: continue
        valid_from = data.get("start_year", data.get("valid_from_year")); valid_to = data.get("end_year", data.get("valid_to_year"))
        if start_year is not None and isinstance(valid_to, int) and valid_to < start_year: continue
        if end_year is not None and isinstance(valid_from, int) and valid_from > end_year: continue
        if polity_type and data.get("civilization_type") != polity_type: continue
        if confidence and data.get("confidence") != confidence: continue
        if review_status and data.get("review_status") != review_status: continue
        if region and region.casefold() not in haystack: continue
        if topic and topic.casefold() not in haystack: continue
        records.append({"id": entity_id, "kind": kind, "slug": data.get("slug", entity_id), "title": title, "summary": summary, "aliases": aliases, "start_year": valid_from, "end_year": valid_to, "confidence": data.get("confidence"), "review_status": data.get("review_status"), "polity_type": data.get("civilization_type")})
    if sort == "title": records.sort(key=lambda record: str(record["title"]))
    elif sort == "date": records.sort(key=lambda record: record["start_year"] if isinstance(record["start_year"], int) else 10**9)
    facets = {name: sorted({str(record[name]) for record in records if record.get(name)}) for name in ("kind", "confidence", "review_status", "polity_type")}
    offset = (page - 1) * page_size
    return {"items": records[offset:offset + page_size], "total": len(records), "page": page, "page_size": page_size, "facets": facets}


@router.get("/coverage/packs", response_model=list[CoveragePack])
def get_coverage_packs_v1() -> list[CoveragePack]:
    return COVERAGE_PACKS


@router.get("/lessons", response_model=list[Lesson], tags=["learning"])
def get_lessons() -> list[Lesson]:
    return LESSONS


@router.get("/lessons/{slug}", response_model=Lesson, tags=["learning"])
def get_lesson(slug: str) -> Lesson:
    lesson = next((item for item in LESSONS if item.slug == slug), None)
    if lesson is None:
        raise HTTPException(status_code=404, detail="Lesson not found.")
    return lesson


@router.post("/attempts", response_model=AttemptFeedback, tags=["learning"])
def submit_attempt(payload: AttemptRequest) -> AttemptFeedback:
    if payload.storage_mode == "account" and not payload.consent:
        raise HTTPException(status_code=422, detail="Clear consent is required before server progress is stored.")
    try:
        return grade_attempt(payload)
    except KeyError as error:
        raise HTTPException(status_code=404, detail="Question not found.") from error


@router.get("/world/{year}", response_model=WorldPayload)
def get_world_by_year(year: int) -> WorldPayload:
    return get_world(_validate_year(year))


def _get_spatial_layers(year: int) -> dict[str, object]:
    with session_scope() as session:
        return AtlasRepository(session).spatial_layers(year)


@router.get("/spatial/layers")
def get_spatial_layers_v1(year: int = Query(default=117)) -> dict[str, object]:
    return _get_spatial_layers(_validate_year(year))


@router.get("/civilizations", response_model=list[Civilization])
def get_civilizations_v1() -> list[Civilization]:
    return list_entities("civilizations", Civilization)


@router.get("/civilization-layers", response_model=list[CivilizationLayer])
def get_civilization_layers_v1() -> list[CivilizationLayer]:
    return list_entities("layers", CivilizationLayer)


@router.get("/places", response_model=list[AtlasNode])
def get_atlas_places_v1() -> list[AtlasNode]:
    return list_entities("nodes", AtlasNode)


@router.get("/routes", response_model=list[AtlasRoute])
def get_routes_v1() -> list[AtlasRoute]:
    return list_entities("routes", AtlasRoute)


@router.get("/sources", response_model=list[SourceRecord])
def get_sources_v1() -> list[SourceRecord]:
    return list_entities("source_records", SourceRecord)


@router.get("/eras", response_model=list[Era])
def get_eras_v1() -> list[Era]:
    return list_entities("eras", Era)


@router.get("/events", response_model=list[HistoricalEvent])
def get_events_v1() -> list[HistoricalEvent]:
    return list_entities("events", HistoricalEvent)


@router.get("/relationships", response_model=list[HistoricalRelationship])
def get_relationships_v1() -> list[HistoricalRelationship]:
    return list_entities("relationships", HistoricalRelationship)


@router.get("/claims", response_model=list[HistoricalClaim])
def get_claims_v1() -> list[HistoricalClaim]:
    return list_entities("claims", HistoricalClaim)


@router.get("/artifacts", response_model=list[SourceArtifact], dependencies=[Depends(require_editorial_key)])
def get_artifacts_v1() -> list[SourceArtifact]:
    return list_entities("artifacts", SourceArtifact, published_only=False)


@router.get("/import-jobs", response_model=list[ImportJob], dependencies=[Depends(require_editorial_key)])
def get_import_jobs_v1() -> list[ImportJob]:
    return list_entities("import_jobs", ImportJob, published_only=False)


@router.get("/review-assignments", response_model=list[ReviewAssignment], dependencies=[Depends(require_editorial_key)])
def get_review_assignments_v1() -> list[ReviewAssignment]:
    return list_entities("review_assignments", ReviewAssignment, published_only=False)


@router.get("/review-decisions", response_model=list[ReviewDecision], dependencies=[Depends(require_editorial_key)])
def get_review_decisions_v1() -> list[ReviewDecision]:
    return list_entities("review_decisions", ReviewDecision, published_only=False)


@router.get("/revisions", response_model=list[RevisionRecord], dependencies=[Depends(require_editorial_key)])
def get_revisions_v1() -> list[RevisionRecord]:
    return list_entities("revisions", RevisionRecord, published_only=False)


@router.get("/storage-contract", response_model=StorageContractView, dependencies=[Depends(require_editorial_key)])
def get_storage_contract_v1() -> StorageContractView:
    return _storage_contract_view()


@router.post("/ingest-plans", response_model=ArtifactIngestPlan, dependencies=[Depends(require_editorial_key)])
def create_ingest_plan_v1(payload: ArtifactIngestRequest) -> ArtifactIngestPlan:
    return build_ingest_plan(payload)


def _review_entity_type(entity_type: str) -> str:
    return {
        "civilization": "civilizations",
        "civilization_layer": "layers",
        "historical_claim": "claims",
        "historical_event": "events",
        "historical_relationship": "relationships",
        "source_record": "source_records",
        "node": "nodes",
        "route": "routes",
    }.get(entity_type, entity_type)


def _apply_review_action(payload: ReviewActionRequest) -> ReviewDecision:
    target_status = {
        "approve": "reviewed",
        "request_changes": "needs_review",
        "reject": "rejected",
        "publish": "reviewed",
    }[payload.decision_type]
    now = datetime.now(timezone.utc).isoformat()
    with session_scope() as session:
        repository = AtlasRepository(session)
        assignment = repository.get("review_assignments", payload.assignment_id, published_only=False)
        if not assignment:
            raise HTTPException(status_code=404, detail="Review assignment not found.")
        previous_status = str(assignment.get("current_review_status", ""))
        entity_type = _review_entity_type(str(assignment.get("entity_type", "")))
        entity_id = str(assignment.get("entity_id", ""))
        try:
            repository.update_review_status(entity_type, entity_id, target_status, payload.reviewer)
        except KeyError as error:
            raise HTTPException(status_code=404, detail="Review target not found.") from error
        except ValueError as error:
            raise HTTPException(status_code=409, detail=str(error)) from error

        assignment["current_review_status"] = target_status
        assignment["target_review_status"] = target_status
        assignment["assigned_reviewer"] = payload.reviewer
        assignment["notes"] = payload.rationale
        repository.upsert(
            "review_assignments", payload.assignment_id, assignment, payload.reviewer,
            published=False,
        )
        decision = ReviewDecision(
            id=f"review-decision:{uuid4()}",
            assignment_id=payload.assignment_id,
            entity_type=str(assignment.get("entity_type", entity_type)),
            entity_id=entity_id,
            decision_type=payload.decision_type,
            previous_review_status=previous_status,
            new_review_status=target_status,
            reviewer=payload.reviewer,
            rationale=payload.rationale,
            created_at=now,
        )
        repository.upsert(
            "review_decisions", decision.id, decision.model_dump(mode="json"), payload.reviewer,
            published=False,
        )
        return decision


@router.post("/review-actions", response_model=ReviewDecision, dependencies=[Depends(require_editorial_key)])
def apply_review_action_v1(payload: ReviewActionRequest) -> ReviewDecision:
    return _apply_review_action(payload)


@api_router.get("/health")
def healthcheck() -> dict[str, object]:
    try:
        return {
            "status": "ok",
            "database": "available",
            "data": get_data_version(),
            "api_version": settings.app_version,
        }
    except Exception as exc:
        raise HTTPException(status_code=503, detail="database is unavailable") from exc


@api_router.get("/health/live")
def api_liveness() -> dict[str, str]:
    return {"status": "ok"}


@api_router.get("/health/ready")
def api_readiness() -> dict[str, object]:
    return healthcheck()


@api_router.get("/data-version")
def data_version() -> dict[str, object]:
    return get_data_version()


@api_router.get("/civilizations", response_model=list[Civilization])
def get_civilizations() -> list[Civilization]:
    return list_entities("civilizations", Civilization)


@api_router.get("/coverage/packs", response_model=list[CoveragePack])
def get_coverage_packs() -> list[CoveragePack]:
    return COVERAGE_PACKS


@api_router.get("/spatial/layers")
def get_spatial_layers(year: int = Query(default=117)) -> dict[str, object]:
    return _get_spatial_layers(_validate_year(year))


@api_router.get("/civilizations/{slug}", response_model=Civilization)
def get_civilization(slug: str) -> Civilization:
    civilization = get_entity("civilizations", slug, Civilization)
    if civilization is None:
        raise HTTPException(status_code=404, detail="Civilization not found.")
    return civilization


@api_router.get("/civilization-layers", response_model=list[CivilizationLayer])
def get_civilization_layers() -> list[CivilizationLayer]:
    return list_entities("layers", CivilizationLayer)


@api_router.get("/places", response_model=list[Place])
def list_places(
    year: int | None = Query(default=None),
    civilization: str | None = Query(default=None),
) -> list[Place]:
    if year is not None:
        _validate_year(year)
    return get_places(year=year, civilization_slug=civilization)


@api_router.get("/places/{slug}", response_model=Place)
def get_place(slug: str) -> Place:
    place = get_entity("places", slug, Place)
    if place is None:
        raise HTTPException(status_code=404, detail="Place not found.")
    return place


@api_router.get("/civilization-places", response_model=list[CivilizationPlace])
def get_civilization_places() -> list[CivilizationPlace]:
    return list_entities("civilization_places", CivilizationPlace)


@api_router.get("/civilization-edges", response_model=list[CivilizationEdge])
def get_civilization_edges() -> list[CivilizationEdge]:
    return list_entities("edges", CivilizationEdge)


@api_router.get("/globe", response_model=GlobePayload)
def globe(
    year: int = Query(default=117),
    zoom: str = Query(default="world"),
) -> GlobePayload:
    return get_globe(year=_validate_year(year), zoom=_validate_zoom(zoom))


@api_router.get("/sources", response_model=list[Source])
def get_sources() -> list[Source]:
    return list_entities("sources", Source)


@api_router.get("/eras", response_model=list[Era])
def get_eras() -> list[Era]:
    return list_entities("eras", Era)


@api_router.get("/events", response_model=list[HistoricalEvent])
def get_events() -> list[HistoricalEvent]:
    return list_entities("events", HistoricalEvent)


@api_router.get("/relationships", response_model=list[HistoricalRelationship])
def get_relationships() -> list[HistoricalRelationship]:
    return list_entities("relationships", HistoricalRelationship)


@api_router.get("/artifacts", response_model=list[SourceArtifact], dependencies=[Depends(require_editorial_key)])
def get_artifacts() -> list[SourceArtifact]:
    return list_entities("artifacts", SourceArtifact, published_only=False)


@api_router.get("/import-jobs", response_model=list[ImportJob], dependencies=[Depends(require_editorial_key)])
def get_import_jobs() -> list[ImportJob]:
    return list_entities("import_jobs", ImportJob, published_only=False)


@api_router.get("/review-assignments", response_model=list[ReviewAssignment], dependencies=[Depends(require_editorial_key)])
def get_review_assignments() -> list[ReviewAssignment]:
    return list_entities("review_assignments", ReviewAssignment, published_only=False)


@api_router.get("/review-decisions", response_model=list[ReviewDecision], dependencies=[Depends(require_editorial_key)])
def get_review_decisions() -> list[ReviewDecision]:
    return list_entities("review_decisions", ReviewDecision, published_only=False)


@api_router.get("/revisions", response_model=list[RevisionRecord], dependencies=[Depends(require_editorial_key)])
def get_revisions() -> list[RevisionRecord]:
    return list_entities("revisions", RevisionRecord, published_only=False)


@api_router.get("/storage-contract", response_model=StorageContractView, dependencies=[Depends(require_editorial_key)])
def get_storage_contract() -> StorageContractView:
    return _storage_contract_view()


@api_router.post("/ingest-plans", response_model=ArtifactIngestPlan, dependencies=[Depends(require_editorial_key)])
def create_ingest_plan(payload: ArtifactIngestRequest) -> ArtifactIngestPlan:
    return build_ingest_plan(payload)


@api_router.post("/review-actions", response_model=ReviewDecision, dependencies=[Depends(require_editorial_key)])
def apply_review_action(payload: ReviewActionRequest) -> ReviewDecision:
    return _apply_review_action(payload)


@api_router.get("/evidence", response_model=list[EvidenceLink])
def get_evidence(
    entity_type: str = Query(...),
    entity_id: str = Query(...),
) -> list[EvidenceLink]:
    return [
        link
        for link in list_entities("evidence", EvidenceLink)
        if link.entity_type == entity_type and link.entity_id == entity_id
    ]


@api_router.get("/claims", response_model=list[HistoricalClaim])
def get_claims() -> list[HistoricalClaim]:
    return list_entities("claims", HistoricalClaim)


@api_router.get("/entities", response_model=list[KnowledgeEntity])
def list_knowledge_entities(kind: str | None = Query(default=None)) -> list[KnowledgeEntity]:
    entities = list_entities("knowledge_entities", KnowledgeEntity)
    return [entity for entity in entities if kind is None or entity.kind == kind]


@api_router.get("/entities/{slug}", response_model=KnowledgeEntity)
def get_knowledge_entity(slug: str) -> KnowledgeEntity:
    entity = get_entity("knowledge_entities", slug, KnowledgeEntity)
    if entity is None:
        raise HTTPException(status_code=404, detail="Entity not found.")
    return entity


@api_router.get("/claims/{claim_id}", response_model=ClaimView)
def get_claim(claim_id: str) -> ClaimView:
    claim = get_entity("knowledge_claims", claim_id, ClaimView)
    if claim is None:
        raise HTTPException(status_code=404, detail="Claim not found.")
    return claim


@api_router.get("/comparisons", response_model=ComparisonView)
def compare_entities(ids: list[str] = Query(...)) -> ComparisonView:
    selected = [
        entity
        for entity in list_entities("knowledge_entities", KnowledgeEntity)
        if entity.id in ids
    ]
    if len(selected) != len(set(ids)):
        raise HTTPException(status_code=404, detail="One or more entities were not found.")
    claims_by_entity = {
        entity.id: [
            claim
            for claim in list_entities("knowledge_claims", ClaimView)
            if claim.subject_id == entity.id
        ]
        for entity in selected
    }
    predicate_sets = [{claim.predicate for claim in claims} for claims in claims_by_entity.values()]
    shared = sorted(set.intersection(*predicate_sets)) if predicate_sets else []
    return ComparisonView(entities=selected, shared_predicates=shared, claims_by_entity=claims_by_entity)


@api_router.get("/search", response_model=list[SearchResult])
def search_entities(
    q: str = Query(..., min_length=2),
    kind: str | None = Query(default=None),
) -> list[SearchResult]:
    needle = q.casefold()
    return [
        SearchResult(
            id=entity.id,
            kind=entity.kind,
            label=entity.canonical_name,
            matched_claim_ids=entity.overview_claim_ids,
        )
        for entity in list_entities("knowledge_entities", KnowledgeEntity)
        if (kind is None or entity.kind == kind)
        and needle in entity.canonical_name.casefold()
    ]


@api_router.get("/graph", response_model=GraphView)
def get_graph(entity_id: str | None = Query(default=None)) -> GraphView:
    edges = [
        edge
        for edge in search_entity_payloads(("knowledge_relationships",))
        if entity_id is None
        or entity_id in {edge["subject_id"], edge["target_id"]}
    ]
    node_ids = {value for edge in edges for value in (edge["subject_id"], edge["target_id"])}
    nodes = (
        list_entities("knowledge_entities", KnowledgeEntity)
        if entity_id is None
        else [
            entity
            for entity in list_entities("knowledge_entities", KnowledgeEntity)
            if entity.id in node_ids or entity.id == entity_id
        ]
    )
    return GraphView(nodes=nodes, edges=edges)


def _storage_contract_view() -> StorageContractView:
    storage = settings.storage
    return StorageContractView(
        provider=storage.provider,
        endpoint=storage.endpoint,
        public_base_url=storage.public_base_url,
        region=storage.region,
        use_path_style=storage.use_path_style,
        signed_url_ttl_seconds=storage.signed_url_ttl_seconds,
        raw=StorageBucketContract(
            name=storage.raw_bucket,
            prefix=storage.raw_prefix,
            purpose="Immutable raw captures, scans, notes, manifests, and dataset payloads.",
        ),
        normalized=StorageBucketContract(
            name=storage.normalized_bucket,
            prefix=storage.normalized_prefix,
            purpose="Normalized records and import manifests for atlas-native entities.",
        ),
        derived=StorageBucketContract(
            name=storage.derived_bucket,
            prefix=storage.derived_prefix,
            purpose="Derived geometry, presentation artifacts, and future vector tiles.",
        ),
        exports=StorageBucketContract(
            name=storage.exports_bucket,
            prefix=storage.exports_prefix,
            purpose="Researcher exports, classroom bundles, and shareable artifacts.",
        ),
    )
