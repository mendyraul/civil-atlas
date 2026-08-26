from fastapi import APIRouter, HTTPException, Query

from app.core.config import settings
from app.schemas import (
    ArtifactIngestPlan,
    ArtifactIngestRequest,
    AtlasNode,
    AtlasRoute,
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
    Place,
    ReviewAssignment,
    ReviewDecision,
    RevisionRecord,
    Source,
    SourceArtifact,
    StorageBucketContract,
    StorageContractView,
    SourceRecord,
    WorldPayload,
)
from app.services.atlas import (
    YEAR_MAX, YEAR_MIN, get_data_version, get_entity, get_globe, get_places,
    get_world, list_entities,
)
from app.services.ingest import build_ingest_plan

router = APIRouter(tags=["world"])
api_router = APIRouter(tags=["api"])


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


@router.get("/world/{year}", response_model=WorldPayload)
def get_world_by_year(year: int) -> WorldPayload:
    return get_world(_validate_year(year))


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


@router.get("/artifacts", response_model=list[SourceArtifact])
def get_artifacts_v1() -> list[SourceArtifact]:
    return list_entities("artifacts", SourceArtifact)


@router.get("/import-jobs", response_model=list[ImportJob])
def get_import_jobs_v1() -> list[ImportJob]:
    return list_entities("import_jobs", ImportJob)


@router.get("/review-assignments", response_model=list[ReviewAssignment])
def get_review_assignments_v1() -> list[ReviewAssignment]:
    return list_entities("review_assignments", ReviewAssignment)


@router.get("/review-decisions", response_model=list[ReviewDecision])
def get_review_decisions_v1() -> list[ReviewDecision]:
    return list_entities("review_decisions", ReviewDecision)


@router.get("/revisions", response_model=list[RevisionRecord])
def get_revisions_v1() -> list[RevisionRecord]:
    return list_entities("revisions", RevisionRecord)


@router.get("/storage-contract", response_model=StorageContractView)
def get_storage_contract_v1() -> StorageContractView:
    return _storage_contract_view()


@router.post("/ingest-plans", response_model=ArtifactIngestPlan)
def create_ingest_plan_v1(payload: ArtifactIngestRequest) -> ArtifactIngestPlan:
    return build_ingest_plan(payload)


@api_router.get("/health")
def healthcheck() -> dict[str, object]:
    return {
        "status": "ok",
        "database": "available",
        "data": get_data_version(),
        "api_version": settings.app_version,
    }


@api_router.get("/data-version")
def data_version() -> dict[str, object]:
    return get_data_version()


@api_router.get("/civilizations", response_model=list[Civilization])
def get_civilizations() -> list[Civilization]:
    return list_entities("civilizations", Civilization)


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


@api_router.get("/artifacts", response_model=list[SourceArtifact])
def get_artifacts() -> list[SourceArtifact]:
    return list_entities("artifacts", SourceArtifact)


@api_router.get("/import-jobs", response_model=list[ImportJob])
def get_import_jobs() -> list[ImportJob]:
    return list_entities("import_jobs", ImportJob)


@api_router.get("/review-assignments", response_model=list[ReviewAssignment])
def get_review_assignments() -> list[ReviewAssignment]:
    return list_entities("review_assignments", ReviewAssignment)


@api_router.get("/review-decisions", response_model=list[ReviewDecision])
def get_review_decisions() -> list[ReviewDecision]:
    return list_entities("review_decisions", ReviewDecision)


@api_router.get("/revisions", response_model=list[RevisionRecord])
def get_revisions() -> list[RevisionRecord]:
    return list_entities("revisions", RevisionRecord)


@api_router.get("/storage-contract", response_model=StorageContractView)
def get_storage_contract() -> StorageContractView:
    return _storage_contract_view()


@api_router.post("/ingest-plans", response_model=ArtifactIngestPlan)
def create_ingest_plan(payload: ArtifactIngestRequest) -> ArtifactIngestPlan:
    return build_ingest_plan(payload)


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
