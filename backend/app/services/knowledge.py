"""Small reviewed fixture behind the knowledge APIs; persistence uses tables.py."""

from app.schemas import ClaimView, KnowledgeEntity

ENTITIES = [
    KnowledgeEntity(id="person-trajan", slug="trajan", kind="person", canonical_name="Trajan", valid_from_year=53, valid_to_year=117, review_state="reviewed", overview_claim_ids=["claim-trajan-office"], chronology_event_ids=["event-trajan-accession"], map_layers=[{"id": "layer-roman-117", "label": "Roman administration, 117 CE"}], related_entity_ids=["office-roman-emperor", "dynasty-nerva-antonine"], passage_ids=["passage-cassius-dio-trajan"]),
    KnowledgeEntity(id="office-roman-emperor", slug="roman-emperor", kind="office", canonical_name="Roman emperor", review_state="reviewed", overview_claim_ids=["claim-trajan-office"], related_entity_ids=["person-trajan"]),
    KnowledgeEntity(id="dynasty-nerva-antonine", slug="nerva-antonine", kind="dynasty", canonical_name="Nerva–Antonine dynasty", valid_from_year=96, valid_to_year=192, review_state="needs_review", related_entity_ids=["person-trajan"]),
    KnowledgeEntity(id="event-trajan-accession", slug="trajan-accession", kind="event", canonical_name="Accession of Trajan", valid_from_year=98, valid_to_year=98, review_state="reviewed", overview_claim_ids=["claim-trajan-office"]),
    KnowledgeEntity(id="concept-principate", slug="principate", kind="concept", canonical_name="Principate", review_state="needs_review", related_entity_ids=["office-roman-emperor"]),
    KnowledgeEntity(id="artifact-trajans-column", slug="trajans-column", kind="artifact", canonical_name="Trajan's Column", valid_from_year=113, valid_to_year=113, review_state="reviewed", overview_claim_ids=["claim-column-date"]),
    KnowledgeEntity(id="passage-cassius-dio-trajan", slug="cassius-dio-trajan-68", kind="primary_source_passage", canonical_name="Cassius Dio, Roman History 68", review_state="reviewed", related_entity_ids=["person-trajan"]),
    KnowledgeEntity(id="metric-reign-years", slug="trajan-reign-years", kind="thematic_metric", canonical_name="Trajan reign duration", review_state="reviewed", overview_claim_ids=["claim-reign-duration"]),
]

CLAIMS = [
    ClaimView(id="claim-trajan-office", version=2, subject_id="person-trajan", predicate="held_office", object_id="office-roman-emperor", valid_from_year=98, valid_to_year=117, geographic_scope={"entity_ids": ["civilization-roman-empire"]}, source_id="source-livius-trajan", citation_locator="sections 4–5", confidence="high", confidence_rationale="Accession and death dates agree across the cited chronology and independent narrative tradition.", review_state="reviewed", supersedes_claim_id="claim-trajan-office-v1"),
    ClaimView(id="claim-column-date", version=1, subject_id="artifact-trajans-column", predicate="dedicated_in_year", value=113, valid_from_year=113, valid_to_year=113, geographic_scope={"entity_ids": ["place-rome"]}, source_id="source-column-inscription", citation_locator="CIL VI 960", confidence="high", confidence_rationale="The dedicatory inscription supplies a consular date.", review_state="reviewed"),
    ClaimView(id="claim-reign-duration", version=1, subject_id="metric-reign-years", predicate="numeric_value", value={"amount": 19, "unit": "years"}, valid_from_year=98, valid_to_year=117, source_id="source-livius-trajan", citation_locator="chronology", confidence="medium", confidence_rationale="Rounded inclusive dates; exact day-count methodology remains to be reviewed.", review_state="needs_review"),
]

RELATIONSHIPS = [
    {"id": "rel-dynasty-successor", "relationship_type": "successor", "subject_id": "dynasty-nerva-antonine", "target_id": "person-trajan", "valid_from_year": 98, "valid_to_year": 117, "supporting_claim_ids": ["claim-trajan-office"]},
    {"id": "rel-office-administrative", "relationship_type": "administrative", "subject_id": "person-trajan", "target_id": "office-roman-emperor", "valid_from_year": 98, "valid_to_year": 117, "supporting_claim_ids": ["claim-trajan-office"]},
]

ENTITIES_BY_SLUG = {entity.slug: entity for entity in ENTITIES}
CLAIMS_BY_ID = {claim.id: claim for claim in CLAIMS}
