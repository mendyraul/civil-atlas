from __future__ import annotations

from typing import TypeVar

from pydantic import BaseModel

from app.db.session import session_scope
from app.schemas import (
    AtlasNode, AtlasRoute, Civilization, CivilizationEdge, CivilizationLayer,
    CivilizationPlace, Era, EvidenceLink, GlobePayload, HistoricalClaim,
    HistoricalEvent, HistoricalRelationship, ImportJob, Place, ReviewAssignment,
    ReviewDecision, RevisionRecord, Source, SourceArtifact, SourceRecord, WorldPayload,
)
from app.services.repository import AtlasRepository

YEAR_MIN = -600
YEAR_MAX = 1800
EVENT_PROXIMITY_WINDOW = 40
T = TypeVar("T", bound=BaseModel)

MODEL_TYPES: dict[str, type[BaseModel]] = {
    "civilizations": Civilization, "layers": CivilizationLayer, "nodes": AtlasNode,
    "routes": AtlasRoute, "places": Place, "civilization_places": CivilizationPlace,
    "edges": CivilizationEdge, "sources": Source, "source_records": SourceRecord,
    "eras": Era, "events": HistoricalEvent, "relationships": HistoricalRelationship,
    "claims": HistoricalClaim, "evidence": EvidenceLink, "artifacts": SourceArtifact,
    "import_jobs": ImportJob, "review_assignments": ReviewAssignment,
    "review_decisions": ReviewDecision, "revisions": RevisionRecord,
}


def list_entities(kind: str, model: type[T]) -> list[T]:
    with session_scope() as session:
        return [model.model_validate(item) for item in AtlasRepository(session).list(kind)]


def get_entity(kind: str, external_id: str, model: type[T]) -> T | None:
    with session_scope() as session:
        value = AtlasRepository(session).get(kind, external_id)
        return model.model_validate(value) if value else None


def get_data_version() -> dict[str, object]:
    with session_scope() as session:
        return AtlasRepository(session).data_version()


def active(start: int, end: int, year: int) -> bool:
    return start <= year <= end


def get_world(year: int) -> WorldPayload:
    civilizations = [x for x in list_entities("civilizations", Civilization) if active(x.start_year, x.end_year, year)]
    return WorldPayload(
        year=year, civilizations=civilizations,
        nodes=[x for x in list_entities("nodes", AtlasNode) if active(x.start_year, x.end_year, year)],
        routes=[x for x in list_entities("routes", AtlasRoute) if active(x.start_year, x.end_year, year)],
        layers=[x for x in list_entities("layers", CivilizationLayer) if active(x.valid_from_year, x.valid_to_year, year)],
        relationships=[x for x in list_entities("relationships", HistoricalRelationship) if active(x.valid_from_year, x.valid_to_year, year)],
        eras=[x for x in list_entities("eras", Era) if active(x.start_year, x.end_year, year)],
        events=[x for x in list_entities("events", HistoricalEvent) if x.start_year <= year + EVENT_PROXIMITY_WINDOW and x.end_year >= year - EVENT_PROXIMITY_WINDOW],
    )


def get_places(year: int | None = None, civilization_slug: str | None = None) -> list[Place]:
    places = list_entities("places", Place)
    if year is not None:
        places = [x for x in places if active(x.start_year, x.end_year, year)]
    if civilization_slug:
        civilization = get_entity("civilizations", civilization_slug, Civilization)
        if not civilization:
            return []
        ids = {x.place_id for x in list_entities("civilization_places", CivilizationPlace) if x.civilization_id == civilization.id}
        places = [x for x in places if x.id in ids]
    return places


def get_globe(year: int, zoom: str) -> GlobePayload:
    civilizations = [x for x in list_entities("civilizations", Civilization) if active(x.start_year, x.end_year, year)]
    civilization_ids = {x.id for x in civilizations}
    layers = [x for x in list_entities("layers", CivilizationLayer) if x.civilization_id in civilization_ids and active(x.valid_from_year, x.valid_to_year, year)]
    places = get_places(year) if zoom != "world" else []
    edges = [x for x in list_entities("edges", CivilizationEdge) if x.civilization_id in civilization_ids and active(x.valid_from_year, x.valid_to_year, year)] if zoom == "local" else []
    visible = civilization_ids | {x.id for x in layers} | {x.id for x in places} | {x.id for x in edges}
    evidence = [x for x in list_entities("evidence", EvidenceLink) if x.entity_id in visible]
    return GlobePayload(year=year, zoom=zoom, civilizations=civilizations, layers=layers, places=places, edges=edges, evidence_links=evidence)
