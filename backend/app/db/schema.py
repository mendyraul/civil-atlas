from app.models.tables import (
    artifacts,
    concepts,
    dynasties,
    entities,
    events,
    metadata,
    offices,
    people,
    primary_source_passages,
    thematic_metrics,
)

ENTITY_TABLES = {
    "person": people,
    "office": offices,
    "dynasty": dynasties,
    "event": events,
    "concept": concepts,
    "artifact": artifacts,
    "primary_source_passage": primary_source_passages,
    "thematic_metric": thematic_metrics,
}

__all__ = ["ENTITY_TABLES", "entities", "metadata"]
