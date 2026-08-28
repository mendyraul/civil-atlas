"""Load the versioned atlas import manifest.

The manifest is the editable seed artifact. This module only validates and
indexes it for the API; historical facts and geometry do not live in Python
application code.
"""

from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from app.schemas import (
    AtlasNode, AtlasRoute, Civilization, CivilizationEdge, CivilizationLayer,
    CivilizationPlace, Era, EvidenceLink, GlobePayload, HistoricalClaim,
    HistoricalEvent, HistoricalRelationship, ImportJob, Place, ReviewAssignment,
    ReviewDecision, RevisionRecord, Source, SourceArtifact, SourceRecord,
    WorldPayload,
)

MANIFEST_PATH = Path(__file__).resolve().parents[2] / "data/imports/world117/v1/manifest.json"

DATASET_MODELS: dict[str, type[BaseModel]] = {
    "civilizations": Civilization, "layers": CivilizationLayer, "nodes": AtlasNode,
    "routes": AtlasRoute, "places": Place, "civilization_places": CivilizationPlace,
    "edges": CivilizationEdge, "sources": Source, "source_records": SourceRecord,
    "eras": Era, "events": HistoricalEvent, "relationships": HistoricalRelationship,
    "claims": HistoricalClaim, "evidence": EvidenceLink, "artifacts": SourceArtifact,
    "import_jobs": ImportJob, "review_assignments": ReviewAssignment,
    "review_decisions": ReviewDecision, "revisions": RevisionRecord,
}


def _read_manifest() -> dict[str, Any]:
    try:
        return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise RuntimeError(f"versioned import manifest is missing: {MANIFEST_PATH}") from exc


MANIFEST = _read_manifest()
if MANIFEST.get("schema_version") != 1:
    raise RuntimeError("unsupported import manifest schema version")
DATASET_VERSION = str(MANIFEST["dataset_version"])
MANIFEST_SHA256 = sha256(MANIFEST_PATH.read_bytes()).hexdigest()


def _load_dataset(kind: str, model: type[BaseModel]) -> list[BaseModel]:
    values = MANIFEST.get("datasets", {}).get(kind)
    if not isinstance(values, list):
        raise RuntimeError(f"manifest dataset {kind!r} must be a list")
    records = [model.model_validate(value) for value in values]
    identifiers: set[str] = set()
    for record in records:
        value = record.model_dump(mode="json")
        external_id = str(value.get("slug") or value["id"])
        if external_id in identifiers:
            raise RuntimeError(f"duplicate external identifier in {kind}: {external_id}")
        identifiers.add(external_id)
    return records


DATASETS: dict[str, list[BaseModel]] = {
    kind: _load_dataset(kind, model) for kind, model in DATASET_MODELS.items()
}

CIVILIZATIONS = DATASETS["civilizations"]
CIVILIZATION_LAYERS = DATASETS["layers"]
ATLAS_NODES = DATASETS["nodes"]
ATLAS_ROUTES = DATASETS["routes"]
PLACES = DATASETS["places"]
CIVILIZATION_PLACES = DATASETS["civilization_places"]
CIVILIZATION_EDGES = DATASETS["edges"]
SOURCES = DATASETS["sources"]
SOURCE_RECORDS = DATASETS["source_records"]
ERAS = DATASETS["eras"]
HISTORICAL_EVENTS = DATASETS["events"]
HISTORICAL_RELATIONSHIPS = DATASETS["relationships"]
HISTORICAL_CLAIMS = DATASETS["claims"]
EVIDENCE_LINKS = DATASETS["evidence"]
SOURCE_ARTIFACTS = DATASETS["artifacts"]
IMPORT_JOBS = DATASETS["import_jobs"]
REVIEW_ASSIGNMENTS = DATASETS["review_assignments"]
REVIEW_DECISIONS = DATASETS["review_decisions"]
REVISION_RECORDS = DATASETS["revisions"]

WORLD_117 = WorldPayload(
    year=int(MANIFEST["focal_year"]), civilizations=CIVILIZATIONS, nodes=ATLAS_NODES,
    routes=ATLAS_ROUTES, layers=CIVILIZATION_LAYERS,
    relationships=HISTORICAL_RELATIONSHIPS, eras=ERAS, events=HISTORICAL_EVENTS,
)
CIVILIZATIONS_BY_SLUG = {item.slug: item for item in CIVILIZATIONS}
PLACES_BY_ID = {item.id: item for item in PLACES}
PLACES_BY_SLUG = {item.slug: item for item in PLACES}

YEAR_MIN = -600
YEAR_MAX = 1800
EVENT_PROXIMITY_WINDOW = 40


def is_active(valid_from_year: int, valid_to_year: int, year: int) -> bool:
    return valid_from_year <= year <= valid_to_year


def is_event_relevant(valid_from_year: int, valid_to_year: int, year: int) -> bool:
    return valid_from_year <= year + EVENT_PROXIMITY_WINDOW and valid_to_year >= year - EVENT_PROXIMITY_WINDOW


def get_world(year: int) -> WorldPayload:
    return WorldPayload(
        year=year,
        civilizations=[item for item in CIVILIZATIONS if is_active(item.start_year, item.end_year, year)],
        nodes=[item for item in ATLAS_NODES if is_active(item.start_year, item.end_year, year)],
        routes=[item for item in ATLAS_ROUTES if is_active(item.start_year, item.end_year, year)],
        layers=[item for item in CIVILIZATION_LAYERS if is_active(item.valid_from_year, item.valid_to_year, year)],
        relationships=[item for item in HISTORICAL_RELATIONSHIPS if is_active(item.valid_from_year, item.valid_to_year, year)],
        eras=[item for item in ERAS if is_active(item.start_year, item.end_year, year)],
        events=[item for item in HISTORICAL_EVENTS if is_event_relevant(item.start_year, item.end_year, year)],
    )


def get_places(year: int | None = None, civilization_slug: str | None = None) -> list[Place]:
    places = list(PLACES)
    if year is not None:
        places = [item for item in places if is_active(item.start_year, item.end_year, year)]
    if civilization_slug is not None:
        civilization = CIVILIZATIONS_BY_SLUG.get(civilization_slug)
        if civilization is None:
            return []
        linked_ids = {item.place_id for item in CIVILIZATION_PLACES if item.civilization_id == civilization.id}
        places = [item for item in places if item.id in linked_ids]
    return places


def get_globe(year: int, zoom: str) -> GlobePayload:
    civilizations = [item for item in CIVILIZATIONS if is_active(item.start_year, item.end_year, year)]
    civilization_ids = {item.id for item in civilizations}
    layers = [item for item in CIVILIZATION_LAYERS if item.civilization_id in civilization_ids and is_active(item.valid_from_year, item.valid_to_year, year)]
    active_places = [item for item in PLACES if is_active(item.start_year, item.end_year, year)]
    active_by_id = {item.id: item for item in active_places}
    active_edges = [item for item in CIVILIZATION_EDGES if item.civilization_id in civilization_ids and is_active(item.valid_from_year, item.valid_to_year, year)]

    if zoom == "world":
        visible_places: list[Place] = []
        visible_edges: list[CivilizationEdge] = []
    elif zoom == "regional":
        important_ids = {item.place_id for item in CIVILIZATION_PLACES if item.civilization_id in civilization_ids and is_active(item.valid_from_year, item.valid_to_year, year) and item.importance_score >= 0.8}
        visible_places = [item for item in active_places if item.id in important_ids]
        visible_edges = []
    else:
        visible_places = active_places
        visible_edges = [item for item in active_edges if item.source_place_id in active_by_id and item.target_place_id in active_by_id]
    visible_ids = civilization_ids | {item.id for item in layers} | {item.id for item in visible_places} | {item.id for item in visible_edges}
    return GlobePayload(year=year, zoom=zoom, civilizations=civilizations, layers=layers, places=visible_places, edges=visible_edges, evidence_links=[item for item in EVIDENCE_LINKS if item.entity_id in visible_ids])


__all__ = [
    "ATLAS_NODES", "ATLAS_ROUTES", "CIVILIZATIONS", "CIVILIZATION_EDGES",
    "CIVILIZATION_LAYERS", "DATASETS", "DATASET_MODELS", "DATASET_VERSION",
    "EVIDENCE_LINKS", "ERAS", "HISTORICAL_CLAIMS", "HISTORICAL_EVENTS",
    "HISTORICAL_RELATIONSHIPS", "IMPORT_JOBS", "MANIFEST_PATH", "MANIFEST_SHA256",
    "PLACES", "REVIEW_ASSIGNMENTS", "REVIEW_DECISIONS", "REVISION_RECORDS",
    "SOURCE_ARTIFACTS", "SOURCE_RECORDS", "SOURCES", "get_globe", "get_places", "get_world",
]
