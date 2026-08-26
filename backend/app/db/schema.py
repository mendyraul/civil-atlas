"""Canonical relational schema.

Territorial geometry deliberately lives only on ``civilization_layers``: a
civilization is an identity and chronology record, while each layer is a
dated, attributable interpretation of its territory.
"""

from app.models.tables import civilization_layers, metadata

__all__ = ["civilization_layers", "metadata"]
