"""Closed vocabularies shared by persistence, validation, and graph APIs."""

from enum import StrEnum


class EntityKind(StrEnum):
    PERSON = "person"
    OFFICE = "office"
    DYNASTY = "dynasty"
    EVENT = "event"
    CONCEPT = "concept"
    ARTIFACT = "artifact"
    PRIMARY_SOURCE_PASSAGE = "primary_source_passage"
    THEMATIC_METRIC = "thematic_metric"


class RelationshipType(StrEnum):
    PREDECESSOR = "predecessor"
    SUCCESSOR = "successor"
    TRIBUTARY = "tributary"
    VASSAL = "vassal"
    RIVAL = "rival"
    TRADE = "trade"
    MIGRATION = "migration"
    CULTURAL_EXCHANGE = "cultural_exchange"
    ADMINISTRATIVE = "administrative"


class ReviewState(StrEnum):
    DRAFT = "draft"
    NEEDS_REVIEW = "needs_review"
    REVIEWED = "reviewed"
    DISPUTED = "disputed"
    REJECTED = "rejected"
