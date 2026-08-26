"""Transactional, repeatable importer for the World 117 fixture.

Run with ``python -m app.seed.import_world117``. The fixture is validated through
the API schemas before a transaction can change repository data.
"""
from pydantic import BaseModel

from app.db.session import session_scope
from app.schemas import *  # noqa: F403 - the explicit mapping below is the fixture contract
from app.seed import catalog
from app.services.repository import AtlasRepository

DATASETS: list[tuple[str, list[BaseModel], type[BaseModel]]] = [
    ("civilizations", catalog.CIVILIZATIONS, Civilization),
    ("layers", catalog.CIVILIZATION_LAYERS, CivilizationLayer),
    ("nodes", catalog.ATLAS_NODES, AtlasNode),
    ("routes", catalog.ATLAS_ROUTES, AtlasRoute),
    ("places", catalog.PLACES, Place),
    ("civilization_places", catalog.CIVILIZATION_PLACES, CivilizationPlace),
    ("edges", catalog.CIVILIZATION_EDGES, CivilizationEdge),
    ("sources", catalog.SOURCES, Source),
    ("source_records", catalog.SOURCE_RECORDS, SourceRecord),
    ("eras", catalog.ERAS, Era),
    ("events", catalog.HISTORICAL_EVENTS, HistoricalEvent),
    ("relationships", catalog.HISTORICAL_RELATIONSHIPS, HistoricalRelationship),
    ("claims", catalog.HISTORICAL_CLAIMS, HistoricalClaim),
    ("evidence", catalog.EVIDENCE_LINKS, EvidenceLink),
    ("artifacts", catalog.SOURCE_ARTIFACTS, SourceArtifact),
    ("import_jobs", catalog.IMPORT_JOBS, ImportJob),
    ("review_assignments", catalog.REVIEW_ASSIGNMENTS, ReviewAssignment),
    ("review_decisions", catalog.REVIEW_DECISIONS, ReviewDecision),
    ("revisions", catalog.REVISION_RECORDS, RevisionRecord),
]


def import_fixture(actor: str = "fixture:world117") -> dict[str, int]:
    counts = {"created": 0, "updated": 0, "duplicate": 0}
    with session_scope() as session:
        repository = AtlasRepository(session)
        for kind, records, schema in DATASETS:
            seen: set[str] = set()
            for raw in records:
                record = schema.model_validate(raw).model_dump(mode="json")
                external_id = str(record.get("slug") or record["id"])
                if external_id in seen:
                    raise ValueError(f"duplicate external identifier in {kind}: {external_id}")
                seen.add(external_id)
                result = repository.upsert(kind, external_id, record, actor)
                counts[result] += 1
    return counts


if __name__ == "__main__":
    print(import_fixture())
