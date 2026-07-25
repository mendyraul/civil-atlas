from fastapi import APIRouter, HTTPException, Query

from app.schemas import (
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
    SourceRecord,
    WorldPayload,
)
from app.services.atlas import (
    ATLAS_NODES,
    ATLAS_ROUTES,
    CIVILIZATION_EDGES,
    CIVILIZATION_LAYERS,
    CIVILIZATION_PLACES,
    CIVILIZATIONS,
    CIVILIZATIONS_BY_SLUG,
    ERAS,
    EVIDENCE_LINKS,
    HISTORICAL_CLAIMS,
    HISTORICAL_EVENTS,
    HISTORICAL_RELATIONSHIPS,
    IMPORT_JOBS,
    PLACES,
    PLACES_BY_SLUG,
    REVIEW_ASSIGNMENTS,
    REVIEW_DECISIONS,
    REVISION_RECORDS,
    SOURCES,
    SOURCE_ARTIFACTS,
    SOURCE_RECORDS,
    YEAR_MAX,
    YEAR_MIN,
    get_globe,
    get_places,
    get_world,
)

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
    return CIVILIZATIONS


@router.get("/civilization-layers", response_model=list[CivilizationLayer])
def get_civilization_layers_v1() -> list[CivilizationLayer]:
    return CIVILIZATION_LAYERS


@router.get("/places", response_model=list[AtlasNode])
def get_atlas_places_v1() -> list[AtlasNode]:
    return ATLAS_NODES


@router.get("/routes", response_model=list[AtlasRoute])
def get_routes_v1() -> list[AtlasRoute]:
    return ATLAS_ROUTES


@router.get("/sources", response_model=list[SourceRecord])
def get_sources_v1() -> list[SourceRecord]:
    return SOURCE_RECORDS


@router.get("/eras", response_model=list[Era])
def get_eras_v1() -> list[Era]:
    return ERAS


@router.get("/events", response_model=list[HistoricalEvent])
def get_events_v1() -> list[HistoricalEvent]:
    return HISTORICAL_EVENTS


@router.get("/relationships", response_model=list[HistoricalRelationship])
def get_relationships_v1() -> list[HistoricalRelationship]:
    return HISTORICAL_RELATIONSHIPS


@router.get("/claims", response_model=list[HistoricalClaim])
def get_claims_v1() -> list[HistoricalClaim]:
    return HISTORICAL_CLAIMS


@router.get("/artifacts", response_model=list[SourceArtifact])
def get_artifacts_v1() -> list[SourceArtifact]:
    return SOURCE_ARTIFACTS


@router.get("/import-jobs", response_model=list[ImportJob])
def get_import_jobs_v1() -> list[ImportJob]:
    return IMPORT_JOBS


@router.get("/review-assignments", response_model=list[ReviewAssignment])
def get_review_assignments_v1() -> list[ReviewAssignment]:
    return REVIEW_ASSIGNMENTS


@router.get("/review-decisions", response_model=list[ReviewDecision])
def get_review_decisions_v1() -> list[ReviewDecision]:
    return REVIEW_DECISIONS


@router.get("/revisions", response_model=list[RevisionRecord])
def get_revisions_v1() -> list[RevisionRecord]:
    return REVISION_RECORDS


@api_router.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@api_router.get("/civilizations", response_model=list[Civilization])
def get_civilizations() -> list[Civilization]:
    return CIVILIZATIONS


@api_router.get("/civilizations/{slug}", response_model=Civilization)
def get_civilization(slug: str) -> Civilization:
    civilization = CIVILIZATIONS_BY_SLUG.get(slug)
    if civilization is None:
        raise HTTPException(status_code=404, detail="Civilization not found.")
    return civilization


@api_router.get("/civilization-layers", response_model=list[CivilizationLayer])
def get_civilization_layers() -> list[CivilizationLayer]:
    return CIVILIZATION_LAYERS


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
    place = PLACES_BY_SLUG.get(slug)
    if place is None:
        raise HTTPException(status_code=404, detail="Place not found.")
    return place


@api_router.get("/civilization-places", response_model=list[CivilizationPlace])
def get_civilization_places() -> list[CivilizationPlace]:
    return CIVILIZATION_PLACES


@api_router.get("/civilization-edges", response_model=list[CivilizationEdge])
def get_civilization_edges() -> list[CivilizationEdge]:
    return CIVILIZATION_EDGES


@api_router.get("/globe", response_model=GlobePayload)
def globe(
    year: int = Query(default=117),
    zoom: str = Query(default="world"),
) -> GlobePayload:
    return get_globe(year=_validate_year(year), zoom=_validate_zoom(zoom))


@api_router.get("/sources", response_model=list[Source])
def get_sources() -> list[Source]:
    return SOURCES


@api_router.get("/eras", response_model=list[Era])
def get_eras() -> list[Era]:
    return ERAS


@api_router.get("/events", response_model=list[HistoricalEvent])
def get_events() -> list[HistoricalEvent]:
    return HISTORICAL_EVENTS


@api_router.get("/relationships", response_model=list[HistoricalRelationship])
def get_relationships() -> list[HistoricalRelationship]:
    return HISTORICAL_RELATIONSHIPS


@api_router.get("/artifacts", response_model=list[SourceArtifact])
def get_artifacts() -> list[SourceArtifact]:
    return SOURCE_ARTIFACTS


@api_router.get("/import-jobs", response_model=list[ImportJob])
def get_import_jobs() -> list[ImportJob]:
    return IMPORT_JOBS


@api_router.get("/review-assignments", response_model=list[ReviewAssignment])
def get_review_assignments() -> list[ReviewAssignment]:
    return REVIEW_ASSIGNMENTS


@api_router.get("/review-decisions", response_model=list[ReviewDecision])
def get_review_decisions() -> list[ReviewDecision]:
    return REVIEW_DECISIONS


@api_router.get("/revisions", response_model=list[RevisionRecord])
def get_revisions() -> list[RevisionRecord]:
    return REVISION_RECORDS


@api_router.get("/evidence", response_model=list[EvidenceLink])
def get_evidence(
    entity_type: str = Query(...),
    entity_id: str = Query(...),
) -> list[EvidenceLink]:
    return [
        link
        for link in EVIDENCE_LINKS
        if link.entity_type == entity_type and link.entity_id == entity_id
    ]


@api_router.get("/claims", response_model=list[HistoricalClaim])
def get_claims() -> list[HistoricalClaim]:
    return HISTORICAL_CLAIMS
