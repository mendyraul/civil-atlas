"""Synthetic, dependency-closed data for export/load and public API acceptance."""

from copy import deepcopy
from app.seed import catalog
from app.schemas import (
    Source,
    SourceRecord,
    PersonRecord,
    OfficeTenure,
    CapitalRole,
    PhysicalFeature,
    KnowledgeEntity,
    ClaimView,
    HistoricalEvent,
)
from app.schemas.toolkit import Annotation, EpisodePack


def dataset():
    records = []

    def add(kind, payload):
        records.append(
            {
                "entity_type": kind,
                "external_id": payload.get("slug") or payload["id"],
                "payload": payload,
            }
        )

    citation = "Synthetic release acceptance fixture; not historical evidence."
    source = Source(
        id="release-origin",
        source_name="Synthetic source release",
        source_type="test",
        citation=citation,
        license="CC0-1.0",
        dataset_version="test-v1",
        reliability_tier="test",
        created_at="2026-11-05T00:00:00Z",
        updated_at="2026-11-05T00:00:00Z",
    ).model_dump(mode="json")
    source["review_status"] = "reviewed"
    add("sources", source)
    source_record = SourceRecord(
        id="release-citation",
        feature_id="release-layer",
        feature_kind="civilization_layer",
        feature_label="Synthetic boundary",
        title="Synthetic release citation",
        citation=citation,
        confidence="low",
        review_status="reviewed",
        notes=citation,
        valid_from_year=50,
        valid_to_year=200,
    ).model_dump(mode="json")
    source_record["source_id"] = "release-origin"
    add("source_records", source_record)
    civ = deepcopy(catalog.CIVILIZATIONS[0].model_dump(mode="json"))
    civ.update(
        start_year=50,
        end_year=200,
        source_record_ids=["release-citation"],
        claim_ids=[],
        evidence=[],
        review_status="reviewed",
    )
    add("civilizations", civ)
    civ_id = civ["id"]
    layer = deepcopy(catalog.CIVILIZATION_LAYERS[0].model_dump(mode="json"))
    layer.update(
        id="release-layer",
        civilization_id=civ_id,
        valid_from_year=50,
        valid_to_year=200,
        geometry_json={
            "type": "Polygon",
            "coordinates": [[[0, 0], [3, 0], [3, 3], [0, 3], [0, 0]]],
        },
        is_placeholder=False,
        geometry_placeholder=None,
        review_status="reviewed",
        source_record_ids=["release-citation"],
        claim_ids=[],
    )
    add("layers", layer)
    for identifier, coordinates in [("release-a", [1, 1]), ("release-b", [2, 2])]:
        node = deepcopy(catalog.ATLAS_NODES[0].model_dump(mode="json"))
        node.update(
            id=identifier,
            slug=identifier,
            label=identifier,
            civilization_id=civ_id,
            civilization_slug=civ["slug"],
            coordinates=coordinates,
            start_year=50,
            end_year=200,
            review_status="reviewed",
            source_record_ids=["release-citation"],
            claim_ids=[],
            evidence=[],
        )
        add("nodes", node)
    place = deepcopy(catalog.PLACES[0].model_dump(mode="json"))
    place.update(
        id="release-a",
        slug="release-a",
        canonical_name="Synthetic capital",
        longitude=1,
        latitude=1,
        start_year=50,
        end_year=200,
        review_status="reviewed",
    )
    add("places", place)
    route = deepcopy(catalog.ATLAS_ROUTES[0].model_dump(mode="json"))
    route.update(
        id="release-road",
        slug="release-road",
        source_node_id="release-a",
        target_node_id="release-b",
        civilization_ids=[civ_id],
        start_year=50,
        end_year=200,
        path=[[1, 1], [2, 2]],
        review_status="reviewed",
        source_record_ids=["release-citation"],
        claim_ids=[],
        evidence=[],
    )
    add("routes", route)
    person = PersonRecord(
        id="release-person",
        name="Synthetic leader",
        wikidata_id="Q1",
        review_status="reviewed",
        source_record_ids=["release-citation"],
    ).model_dump(mode="json")
    add("people", person)
    common = dict(
        civilization_id=civ_id,
        start_year=98,
        end_year=117,
        review_status="reviewed",
        source_record_ids=["release-citation"],
        source_id="release-origin",
        statement="https://www.wikidata.org/entity/statement/Q1-test",
        qualifiers={},
    )
    tenure = OfficeTenure(
        id="release-tenure",
        person_id="release-person",
        office="Synthetic office",
        **common,
    ).model_dump(mode="json")
    add("offices", tenure)
    capital = CapitalRole(
        id="release-capital", place_id="release-a", **common
    ).model_dump(mode="json")
    add("capital_roles", capital)
    event = HistoricalEvent(
        id="release-event",
        slug="release-event",
        label="Synthetic event",
        event_type="test",
        start_year=117,
        end_year=117,
        display_date="117",
        summary=citation,
        impact="test",
        civilization_ids=[civ_id],
        place_ids=["release-a"],
        confidence="low",
        review_status="reviewed",
        evidence=[],
    ).model_dump(mode="json")
    event.update(source_record_ids=["release-citation"], source_id="release-origin")
    add("events", event)
    annotation = Annotation(
        id="release-annotation",
        title="Synthetic note",
        valid_from_year=117,
        valid_to_year=117,
        boundary_layer_id="release-layer",
        kind="territory",
        source_record_ids=["release-citation"],
        review_status="reviewed",
    ).model_dump(mode="json")
    add("annotations", annotation)
    pack = EpisodePack(
        id="release-episode",
        title="Synthetic episode",
        summary=citation,
        dataset_version="test-v1",
        attribution=citation,
        review_status="reviewed",
        annotations=[annotation],
        steps=[
            dict(
                id="one",
                title="Synthetic step",
                narrative=citation,
                year=117,
                camera=dict(center=[1, 1]),
                entity_ids=["release-a"],
                layer_ids=["release-layer"],
                annotation_ids=["release-annotation"],
                source_record_ids=["release-citation"],
            )
        ],
    ).model_dump(mode="json")
    add("episodes", pack)
    physical = PhysicalFeature(
        id="release-physical",
        label="Synthetic river",
        feature_type="river",
        geometry={"type": "LineString", "coordinates": [[1, 1], [2, 1]]},
        confidence="low",
        review_status="reviewed",
        source_record_ids=["release-citation"],
        source_notes=citation,
        source_id="release-origin",
    ).model_dump(mode="json")
    add("physical_features", physical)
    person = KnowledgeEntity(
        id="release-kperson",
        slug="release-person-knowledge",
        kind="person",
        canonical_name="Synthetic knowledge person",
        review_state="reviewed",
        overview_claim_ids=["release-kclaim"],
        chronology_event_ids=["release-kevent"],
        related_entity_ids=["release-kevent"],
        map_layers=[{"id": "release-layer", "label": "Synthetic map"}],
    ).model_dump(mode="json")
    event = KnowledgeEntity(
        id="release-kevent",
        slug="release-event-knowledge",
        kind="event",
        canonical_name="Synthetic knowledge event",
        review_state="reviewed",
    ).model_dump(mode="json")
    add("knowledge_entities", person)
    add("knowledge_entities", event)
    claim = ClaimView(
        id="release-kclaim",
        version=1,
        subject_id="release-kperson",
        predicate="synthetic_relation",
        object_id="release-kevent",
        source_id="release-origin",
        citation_locator="Synthetic fixture",
        confidence="low",
        confidence_rationale=citation,
        review_state="reviewed",
    ).model_dump(mode="json")
    add("knowledge_claims", claim)
    add(
        "knowledge_relationships",
        dict(
            id="release-krelationship",
            relationship_type="context",
            subject_id="release-kperson",
            target_id="release-kevent",
            valid_from_year=117,
            valid_to_year=117,
            review_status="reviewed",
            supporting_claim_ids=["release-kclaim"],
        ),
    )
    return records
