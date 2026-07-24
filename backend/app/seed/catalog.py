from collections import defaultdict

from app.schemas import (
    AtlasNode,
    AtlasRoute,
    Civilization,
    CivilizationEdge,
    CivilizationLayer,
    CivilizationPlace,
    Era,
    EvidenceLink,
    GlobePayload,
    HistoricalClaim,
    HistoricalEvent,
    Place,
    Source,
    SourceRecord,
    WorldPayload,
)
from app.seed.world117 import WORLD_117

SEED_CREATED_AT = "2026-07-21T12:00:00Z"
SEED_UPDATED_AT = "2026-07-21T12:00:00Z"
SEED_RETRIEVED_AT = "2026-07-21T12:00:00Z"
YEAR_MIN = -600
YEAR_MAX = 1800
EVENT_PROXIMITY_WINDOW = 40

LAYER_CONFIG: dict[str, tuple[str, str]] = {
    "roman-empire": ("Trajanic imperial extent", "direct_control"),
    "han-dynasty": ("Later Han administrative extent", "direct_control"),
    "parthian-empire": ("Arsacid imperial extent", "source_reported_extent"),
    "kingdom-of-kush": ("Meroitic Nile core", "direct_control"),
    "aksumite-kingdom": ("Aksumite inland-port sphere", "trade_network"),
    "maya-civilization": ("Maya cultural zone", "cultural_extent"),
    "satavahana-dynasty": ("Satavahana Deccan footprint", "source_reported_extent"),
}

PLACE_IMPORTANCE: dict[str, float] = {
    "capital": 1.0,
    "major_city": 0.82,
    "trade_hub": 0.84,
    "port": 0.8,
    "administrative_center": 0.86,
    "religious_center": 0.7,
    "frontier_post": 0.58,
}

EDGE_TRAVEL_DAYS: dict[str, tuple[int, int]] = {
    "road": (4, 12),
    "sea_route": (6, 18),
    "trade_route": (8, 28),
    "military_route": (5, 15),
    "river_route": (4, 10),
}


def is_active(valid_from_year: int, valid_to_year: int, year: int) -> bool:
    return valid_from_year <= year <= valid_to_year


def is_event_relevant(valid_from_year: int, valid_to_year: int, year: int) -> bool:
    return valid_from_year <= year + EVENT_PROXIMITY_WINDOW and valid_to_year >= year - EVENT_PROXIMITY_WINDOW


def _flatten_source_records() -> list[SourceRecord]:
    records: list[SourceRecord] = []

    for feature in [
        *WORLD_117.civilizations,
        *WORLD_117.nodes,
        *WORLD_117.routes,
        *WORLD_117.eras,
        *WORLD_117.events,
    ]:
        feature_kind = getattr(feature, "kind", None)
        if feature_kind is None:
            feature_kind = "event" if isinstance(feature, HistoricalEvent) else "era"
        for evidence in feature.evidence:
            records.append(
                SourceRecord(
                    id=evidence.id,
                    feature_id=feature.id,
                    feature_kind=feature_kind,
                    feature_label=feature.label,
                    title=evidence.title,
                    citation=evidence.citation,
                    link=evidence.link,
                    source_namespace="manual_seed",
                    confidence=evidence.confidence,
                    review_status=evidence.review_status,
                    notes=evidence.notes,
                    valid_from_year=getattr(feature, "start_year", None),
                    valid_to_year=getattr(feature, "end_year", None),
                )
            )

    return records


SOURCE_RECORDS = _flatten_source_records()

SOURCE_RECORD_IDS_BY_FEATURE: dict[str, list[str]] = defaultdict(list)
for record in SOURCE_RECORDS:
    SOURCE_RECORD_IDS_BY_FEATURE[record.feature_id].append(record.id)


def _build_sources() -> list[Source]:
    sources: list[Source] = []
    for record in SOURCE_RECORDS:
        url = record.link
        source_type = "book_or_reference"
        if url:
            source_type = "web_reference"

        sources.append(
            Source(
                id=record.id,
                source_name=record.title,
                source_type=source_type,
                external_id=record.id,
                url=url,
                citation=record.citation,
                license="unknown_seed",
                reliability_tier=record.confidence,
                retrieved_at=SEED_RETRIEVED_AT,
                created_at=SEED_CREATED_AT,
                updated_at=SEED_UPDATED_AT,
            )
        )

    return sources


SOURCES = _build_sources()


HISTORICAL_CLAIMS: list[HistoricalClaim] = [
    HistoricalClaim(
        id="claim-roman-existence",
        claim_type="supports_civilization_existence",
        subject_id="roman-empire",
        subject_kind="civilization",
        confidence="high",
        review_status="reviewed",
        notes="Roman imperial presence in 117 CE is operationally canonical for the MVP and backed by seeded atlas references.",
        valid_from_year=-27,
        valid_to_year=395,
        source_record_ids=["roman-cambridge"],
    ),
    HistoricalClaim(
        id="claim-roman-boundary",
        claim_type="supports_boundary",
        subject_id="layer-roman-empire",
        subject_kind="civilization_layer",
        object_id="roman-empire",
        object_kind="civilization",
        confidence="medium_high",
        review_status="seeded",
        notes="Roman boundary geometry is intentionally approximate and should be read as a source-reported operational layer.",
        valid_from_year=-27,
        valid_to_year=395,
        source_record_ids=["roman-cambridge"],
    ),
    HistoricalClaim(
        id="claim-han-existence",
        claim_type="supports_civilization_existence",
        subject_id="han-dynasty",
        subject_kind="civilization",
        confidence="high",
        review_status="reviewed",
        notes="Han dynasty existence and broad administrative continuity are canonical app facts for the seed period.",
        valid_from_year=-202,
        valid_to_year=220,
        source_record_ids=["han-cambridge"],
    ),
    HistoricalClaim(
        id="claim-han-boundary",
        claim_type="supports_boundary",
        subject_id="layer-han-dynasty",
        subject_kind="civilization_layer",
        object_id="han-dynasty",
        object_kind="civilization",
        confidence="medium_high",
        review_status="seeded",
        notes="The Han layer is a placeholder administrative footprint rather than a fully reviewed frontier reconstruction.",
        valid_from_year=-202,
        valid_to_year=220,
        source_record_ids=["han-cambridge"],
    ),
    HistoricalClaim(
        id="claim-parthian-existence",
        claim_type="supports_civilization_existence",
        subject_id="parthian-empire",
        subject_kind="civilization",
        confidence="medium_high",
        review_status="reviewed",
        notes="Parthian imperial existence is seeded as a distinct polity for west-central Asian comparison.",
        valid_from_year=-247,
        valid_to_year=224,
        source_record_ids=["parthia-curtis"],
    ),
    HistoricalClaim(
        id="claim-kush-existence",
        claim_type="supports_civilization_existence",
        subject_id="kingdom-of-kush",
        subject_kind="civilization",
        confidence="medium",
        review_status="seeded",
        notes="Kush is treated as a Nile-centered kingdom with a provisional extent in the current MVP.",
        valid_from_year=-1070,
        valid_to_year=350,
        source_record_ids=["kush-source"],
    ),
    HistoricalClaim(
        id="claim-aksum-route",
        claim_type="supports_route",
        subject_id="aksum-adulis",
        subject_kind="route",
        object_id="aksumite-kingdom",
        object_kind="civilization",
        confidence="medium",
        review_status="seeded",
        notes="Aksum-Adulis is seeded as a representative inland-to-port trade corridor rather than a precise archaeological path.",
        valid_from_year=-100,
        valid_to_year=700,
        source_record_ids=["route-aksum-adulis", "adulis-source"],
    ),
    HistoricalClaim(
        id="claim-maya-extent",
        claim_type="supports_boundary",
        subject_id="layer-maya-civilization",
        subject_kind="civilization_layer",
        object_id="maya-civilization",
        object_kind="civilization",
        confidence="medium",
        review_status="needs_review",
        notes="The Maya layer is a cultural extent seed and should not be interpreted as a single sovereign border.",
        valid_from_year=-600,
        valid_to_year=1697,
        source_record_ids=["maya-source", "tikal-source"],
    ),
    HistoricalClaim(
        id="claim-satavahana-date-range",
        claim_type="supports_date_range",
        subject_id="satavahana-dynasty",
        subject_kind="civilization",
        confidence="medium",
        review_status="seeded",
        notes="Satavahana date bounds are seeded from broad dynastic overviews and remain open to later refinement.",
        valid_from_year=-100,
        valid_to_year=250,
        source_record_ids=["satavahana-source"],
    ),
    HistoricalClaim(
        id="claim-roma-location",
        claim_type="supports_place_location",
        subject_id="roma",
        subject_kind="place",
        object_id="roman-empire",
        object_kind="civilization",
        confidence="high",
        review_status="reviewed",
        notes="Roma is used as a high-confidence anchor location for the Roman imperial model.",
        valid_from_year=-753,
        valid_to_year=1453,
        source_record_ids=["roma-source"],
    ),
    HistoricalClaim(
        id="claim-changan-capital",
        claim_type="supports_capital_role",
        subject_id="changan",
        subject_kind="place",
        object_id="han-dynasty",
        object_kind="civilization",
        confidence="high",
        review_status="seeded",
        notes="Chang'an is seeded as the primary Han capital-role node for atlas interaction.",
        valid_from_year=-202,
        valid_to_year=220,
        source_record_ids=["changan-source"],
    ),
    HistoricalClaim(
        id="claim-ctesiphon-nisa-route",
        claim_type="supports_route",
        subject_id="ctesiphon-nisa",
        subject_kind="edge",
        object_id="parthian-empire",
        object_kind="civilization",
        confidence="medium",
        review_status="seeded",
        notes="The Ctesiphon-Nisa edge is a schematic overland corridor proving route logic, not a surveyed line.",
        valid_from_year=-129,
        valid_to_year=224,
        source_record_ids=["route-ctesiphon-nisa", "nisa-source", "ctesiphon-source"],
    ),
]

CLAIM_IDS_BY_SUBJECT: dict[str, list[str]] = defaultdict(list)
for claim in HISTORICAL_CLAIMS:
    CLAIM_IDS_BY_SUBJECT[claim.subject_id].append(claim.id)
    if claim.object_id:
        CLAIM_IDS_BY_SUBJECT[claim.object_id].append(claim.id)


def _build_evidence_links() -> list[EvidenceLink]:
    links: list[EvidenceLink] = []
    seen: set[tuple[str, str, str]] = set()
    counter = 1

    for claim in HISTORICAL_CLAIMS:
        for source_id in claim.source_record_ids:
            key = (source_id, claim.subject_kind, claim.subject_id)
            if key in seen:
                continue
            seen.add(key)
            links.append(
                EvidenceLink(
                    id=f"evidence-link-{counter}",
                    source_id=source_id,
                    entity_type=claim.subject_kind,
                    entity_id=claim.subject_id,
                    claim_type=claim.claim_type,
                    confidence_level=claim.confidence,
                    quote_or_note=claim.notes,
                    created_at=SEED_CREATED_AT,
                    updated_at=SEED_UPDATED_AT,
                )
            )
            counter += 1

    return links


EVIDENCE_LINKS = _build_evidence_links()


def _polygon_to_geojson(polygon: list[tuple[float, float]]) -> dict[str, object]:
    coordinates = [[[longitude, latitude] for longitude, latitude in polygon]]
    return {"type": "Polygon", "coordinates": coordinates}


def _build_layers() -> list[CivilizationLayer]:
    layers: list[CivilizationLayer] = []

    for civilization in WORLD_117.civilizations:
        layer_name, layer_type = LAYER_CONFIG.get(
            civilization.id,
            ("Operational seed layer", "source_reported_extent"),
        )
        layer_id = f"layer-{civilization.id}"
        layers.append(
            CivilizationLayer(
                id=layer_id,
                civilization_id=civilization.id,
                name=layer_name,
                layer_type=layer_type,
                valid_from_year=civilization.start_year,
                valid_to_year=civilization.end_year,
                geometry_json=_polygon_to_geojson(civilization.polygon),
                geometry_placeholder=civilization.extent_note,
                confidence=civilization.confidence,
                review_status=civilization.review_status,
                source_note=civilization.source_notes,
                created_at=SEED_CREATED_AT,
                updated_at=SEED_UPDATED_AT,
                source_record_ids=SOURCE_RECORD_IDS_BY_FEATURE[civilization.id],
                claim_ids=CLAIM_IDS_BY_SUBJECT[layer_id],
            )
        )

    return layers


CIVILIZATION_LAYERS = _build_layers()


def _build_places() -> list[Place]:
    places: list[Place] = []
    for node in WORLD_117.nodes:
        longitude, latitude = node.coordinates
        places.append(
            Place(
                id=node.id,
                slug=node.slug,
                canonical_name=node.name,
                modern_name=node.modern_name,
                latitude=latitude,
                longitude=longitude,
                start_year=node.start_year,
                end_year=node.end_year,
                place_type=node.place_type,
                confidence_level=node.confidence,
                review_status=node.review_status,
                created_at=SEED_CREATED_AT,
                updated_at=SEED_UPDATED_AT,
            )
        )

    return places


PLACES = _build_places()
PLACES_BY_ID = {place.id: place for place in PLACES}
PLACES_BY_SLUG = {place.slug: place for place in PLACES}


def _build_civilization_places() -> list[CivilizationPlace]:
    items: list[CivilizationPlace] = []
    for node in WORLD_117.nodes:
        if not node.civilization_id:
            continue
        items.append(
            CivilizationPlace(
                id=f"civilization-place-{node.id}",
                civilization_id=node.civilization_id,
                place_id=node.id,
                valid_from_year=node.start_year,
                valid_to_year=node.end_year,
                role=node.role,
                importance_score=PLACE_IMPORTANCE.get(node.role, 0.65),
                confidence_level=node.confidence,
                review_status=node.review_status,
            )
        )
    return items


CIVILIZATION_PLACES = _build_civilization_places()


def _build_edges() -> list[CivilizationEdge]:
    edges: list[CivilizationEdge] = []
    for route in WORLD_117.routes:
        travel_min, travel_max = EDGE_TRAVEL_DAYS.get(route.edge_type, (7, 21))
        for civilization_id in route.civilization_ids:
            edges.append(
                CivilizationEdge(
                    id=route.id,
                    civilization_id=civilization_id,
                    source_place_id=route.source_node_id,
                    target_place_id=route.target_node_id,
                    valid_from_year=route.start_year,
                    valid_to_year=route.end_year,
                    edge_type=route.edge_type,
                    estimated_travel_days_min=travel_min,
                    estimated_travel_days_max=travel_max,
                    confidence_level=route.confidence,
                    review_status=route.review_status,
                    source_note=route.source_notes,
                )
            )
    return edges


CIVILIZATION_EDGES = _build_edges()


def _attach_links() -> tuple[list[Civilization], list[AtlasNode], list[AtlasRoute]]:
    civilizations = [
        civilization.model_copy(
            update={
                "source_record_ids": SOURCE_RECORD_IDS_BY_FEATURE[civilization.id],
                "claim_ids": CLAIM_IDS_BY_SUBJECT[civilization.id],
            }
        )
        for civilization in WORLD_117.civilizations
    ]
    nodes = [
        node.model_copy(
            update={
                "source_record_ids": SOURCE_RECORD_IDS_BY_FEATURE[node.id],
                "claim_ids": CLAIM_IDS_BY_SUBJECT[node.id],
            }
        )
        for node in WORLD_117.nodes
    ]
    routes = [
        route.model_copy(
            update={
                "source_record_ids": SOURCE_RECORD_IDS_BY_FEATURE[route.id],
                "claim_ids": CLAIM_IDS_BY_SUBJECT[route.id],
            }
        )
        for route in WORLD_117.routes
    ]
    return civilizations, nodes, routes


CIVILIZATIONS, ATLAS_NODES, ATLAS_ROUTES = _attach_links()
ERAS: list[Era] = WORLD_117.eras
HISTORICAL_EVENTS: list[HistoricalEvent] = WORLD_117.events
CIVILIZATIONS_BY_SLUG = {civilization.slug: civilization for civilization in CIVILIZATIONS}


def get_world(year: int) -> WorldPayload:
    return WorldPayload(
        year=year,
        civilizations=[
            civilization
            for civilization in CIVILIZATIONS
            if is_active(civilization.start_year, civilization.end_year, year)
        ],
        nodes=[
            node for node in ATLAS_NODES if is_active(node.start_year, node.end_year, year)
        ],
        routes=[
            route
            for route in ATLAS_ROUTES
            if is_active(route.start_year, route.end_year, year)
        ],
        eras=[era for era in ERAS if is_active(era.start_year, era.end_year, year)],
        events=[
            event
            for event in HISTORICAL_EVENTS
            if is_event_relevant(event.start_year, event.end_year, year)
        ],
    )


def get_places(year: int | None = None, civilization_slug: str | None = None) -> list[Place]:
    places = PLACES
    if year is not None:
        places = [place for place in places if is_active(place.start_year, place.end_year, year)]

    if civilization_slug is not None:
        civilization = CIVILIZATIONS_BY_SLUG.get(civilization_slug)
        if not civilization:
            return []
        linked_place_ids = {
            item.place_id for item in CIVILIZATION_PLACES if item.civilization_id == civilization.id
        }
        places = [place for place in places if place.id in linked_place_ids]

    return places


def get_globe(year: int, zoom: str) -> GlobePayload:
    visible_civilizations = [
        civilization
        for civilization in CIVILIZATIONS
        if is_active(civilization.start_year, civilization.end_year, year)
    ]
    visible_civilization_ids = {civilization.id for civilization in visible_civilizations}
    visible_layers = [
        layer
        for layer in CIVILIZATION_LAYERS
        if layer.civilization_id in visible_civilization_ids
        and is_active(layer.valid_from_year, layer.valid_to_year, year)
    ]
    active_places = [place for place in PLACES if is_active(place.start_year, place.end_year, year)]
    active_places_by_id = {place.id: place for place in active_places}
    active_edges = [
        edge
        for edge in CIVILIZATION_EDGES
        if edge.civilization_id in visible_civilization_ids
        and is_active(edge.valid_from_year, edge.valid_to_year, year)
    ]

    if zoom == "world":
        visible_places: list[Place] = []
        visible_edges: list[CivilizationEdge] = []
        visible_entity_ids = {civilization.id for civilization in visible_civilizations} | {
            layer.id for layer in visible_layers
        }
    elif zoom == "regional":
        regional_place_ids = {
            item.place_id
            for item in CIVILIZATION_PLACES
            if item.civilization_id in visible_civilization_ids
            and is_active(item.valid_from_year, item.valid_to_year, year)
            and item.importance_score >= 0.8
        }
        visible_places = [
            place for place in active_places if place.id in regional_place_ids
        ]
        visible_edges = []
        visible_entity_ids = {place.id for place in visible_places} | {
            civilization.id for civilization in visible_civilizations
        } | {layer.id for layer in visible_layers}
    else:
        visible_places = active_places
        visible_edges = [
            edge
            for edge in active_edges
            if edge.source_place_id in active_places_by_id
            and edge.target_place_id in active_places_by_id
        ]
        visible_entity_ids = {place.id for place in visible_places} | {
            edge.id for edge in visible_edges
        } | {civilization.id for civilization in visible_civilizations} | {
            layer.id for layer in visible_layers
        }

    evidence_links = [
        link for link in EVIDENCE_LINKS if link.entity_id in visible_entity_ids
    ]

    return GlobePayload(
        year=year,
        zoom=zoom,
        civilizations=visible_civilizations,
        layers=visible_layers,
        places=visible_places,
        edges=visible_edges,
        evidence_links=evidence_links,
    )
