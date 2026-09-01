"""Canonical relational schema for entities and native spatial records.

The JSON registry remains the import-compatible source while typed tables keep
native PostGIS geometry available for future spatial predicates and tiles.
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
    external_ids,
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

__all__ = ["ENTITY_TABLES", "civilization_layers", "entities", "external_ids", "metadata"]
