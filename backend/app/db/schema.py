"""Canonical relational schema.

Territorial geometry deliberately lives only on ``civilization_layers``: a
civilization is an identity and chronology record, while each layer is a
dated, attributable interpretation of its territory.
"""

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
    civilization_layers,
    metadata,
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

__all__ = ["ENTITY_TABLES", "civilization_layers", "entities", "metadata"]
