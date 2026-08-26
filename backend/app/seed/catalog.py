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
    HistoricalRelationship,
    ImportJob,
    Place,
    ReviewAssignment,
    ReviewDecision,
    RevisionRecord,
    Source,
    SourceArtifact,
    SourceRecord,
    WorldPayload,
)
from app.seed.world117 import WORLD_117

SEED_CREATED_AT = "2026-07-21T12:00:00Z"
SEED_UPDATED_AT = "2026-07-21T12:00:00Z"
SEED_RETRIEVED_AT = "2026-07-21T12:00:00Z"
SEED_REVIEW_DUE_AT = "2026-08-07T17:00:00Z"
YEAR_MIN = -600
YEAR_MAX = 1800
EVENT_PROXIMITY_WINDOW = 40
RAW_BUCKET = "civil-atlas-raw"
NORMALIZED_BUCKET = "civil-atlas-normalized"
DERIVED_BUCKET = "civil-atlas-derived"
EXPORTS_BUCKET = "civil-atlas-exports"

DEFAULT_LAYER_CONFIG: dict[str, tuple[str, str]] = {
    "roman-empire": ("Roman imperial footprint", "direct_control"),
    "han-dynasty": ("Later Han footprint", "direct_control"),
    "parthian-empire": ("Arsacid imperial extent", "source_reported_extent"),
    "kingdom-of-kush": ("Meroitic Nile core", "direct_control"),
    "aksumite-kingdom": ("Aksumite inland-port sphere", "trade_network"),
    "maya-civilization": ("Maya cultural zone", "cultural_extent"),
    "satavahana-dynasty": ("Satavahana Deccan footprint", "source_reported_extent"),
}

LAYER_VARIANTS: dict[str, list[dict[str, object]]] = {
    "roman-empire": [
        {
            "id": "layer-roman-empire-core",
            "name": "Roman direct provincial core",
            "layer_type": "direct_control",
            "variant_group": "roman-117-frontier-readings",
            "interpretation_label": "Conservative provincial core",
            "interpretation_kind": "boundary_variant",
            "display_order": 0,
            "is_primary": True,
            "geometry": [
                (-8, 36),
                (-5, 43),
                (3, 49),
                (13, 52),
                (24, 52),
                (31, 45),
                (36, 40),
                (37, 35),
                (31, 31),
                (24, 32),
                (18, 39),
                (7, 44),
                (-1, 43),
                (-8, 36),
            ],
            "confidence": "medium_high",
            "review_status": "seeded",
            "source_note": "Conservative reading emphasizing long-held provincial control without treating Trajan's Mesopotamian campaign as settled empire.",
        },
        {
            "id": "layer-roman-empire-trajanic-east",
            "name": "Roman eastern campaign reach",
            "layer_type": "contested_zone",
            "variant_group": "roman-117-frontier-readings",
            "interpretation_label": "Maximal Trajanic campaign reading",
            "interpretation_kind": "boundary_variant",
            "display_order": 1,
            "is_primary": False,
            "valid_from_year": 114,
            "valid_to_year": 117,
            "geometry": [
                (-8, 36),
                (-5, 43),
                (3, 50),
                (14, 54),
                (28, 56),
                (39, 49),
                (49, 36),
                (45, 31),
                (38, 30),
                (31, 30),
                (27, 32),
                (23, 38),
                (14, 46),
                (2, 44),
                (-8, 36),
            ],
            "confidence": "medium",
            "review_status": "needs_review",
            "source_note": "Maximal 114-117 CE campaign reading that treats Roman reach into Mesopotamia as a temporary frontier interpretation, not a settled consensus boundary.",
        },
    ],
    "han-dynasty": [
        {
            "id": "layer-han-dynasty-core",
            "name": "Later Han administrative core",
            "layer_type": "administrative_layer",
            "variant_group": "han-117-frontier-readings",
            "interpretation_label": "Administrative core provinces",
            "interpretation_kind": "administrative_layer",
            "display_order": 0,
            "is_primary": True,
            "geometry": [
                (98, 23),
                (100, 31),
                (106, 37),
                (114, 39),
                (120, 36),
                (119, 28),
                (112, 23),
                (104, 21),
                (98, 23),
            ],
            "confidence": "medium_high",
            "review_status": "seeded",
            "source_note": "Conservative administrative reading centered on the durable agrarian and metropolitan core of the Later Han state.",
        },
        {
            "id": "layer-han-dynasty-western-regions",
            "name": "Han western-regions influence corridor",
            "layer_type": "influence_zone",
            "variant_group": "han-117-frontier-readings",
            "interpretation_label": "Western Regions influence corridor",
            "interpretation_kind": "influence_zone",
            "display_order": 1,
            "is_primary": False,
            "valid_from_year": 91,
            "valid_to_year": 123,
            "geometry": [
                (84, 36),
                (90, 42),
                (99, 43),
                (107, 39),
                (104, 34),
                (95, 31),
                (87, 31),
                (84, 36),
            ],
            "confidence": "medium",
            "review_status": "needs_review",
            "source_note": "Influence-zone reading for corridor oversight and military activity in the Western Regions, deliberately separated from direct administrative control.",
        },
    ],
}

RELATIONSHIP_SEEDS: list[dict[str, object]] = [
    {
        "id": "relationship-roman-parthian-frontier",
        "relationship_type": "contested_frontier",
        "subject_id": "roman-empire",
        "subject_kind": "civilization",
        "target_id": "parthian-empire",
        "target_kind": "civilization",
        "label": "Roman-Parthian eastern frontier rivalry",
        "summary": "The Euphrates-to-Mesopotamia zone should be interpreted as contested and time-sensitive, not as a single settled imperial edge.",
        "valid_from_year": -53,
        "valid_to_year": 217,
        "confidence": "high",
        "review_status": "seeded",
        "source_note": "Seed relationship used to make rivalry and contested control first-class atlas facts.",
        "source_record_ids": ["roman-cambridge", "parthia-curtis", "event-trajan-east"],
        "claim_ids": ["claim-roman-boundary-core", "claim-roman-boundary-maximal", "claim-parthian-existence"],
    },
    {
        "id": "relationship-han-western-regions-overlap",
        "relationship_type": "influence_overlap",
        "subject_id": "han-dynasty",
        "subject_kind": "civilization",
        "target_id": "parthian-empire",
        "target_kind": "civilization",
        "label": "Han and Arsacid corridor overlap",
        "summary": "The atlas should distinguish direct rule from long-distance corridor influence when comparing Han and Arsacid west-east systems.",
        "valid_from_year": -100,
        "valid_to_year": 220,
        "confidence": "medium",
        "review_status": "seeded",
        "source_note": "Seed relationship capturing overlapping influence logic across the Silk Road corridor world.",
        "source_record_ids": ["han-cambridge", "parthia-curtis", "event-han-western-regions"],
        "claim_ids": ["claim-han-boundary-core", "claim-han-western-regions-influence", "claim-parthian-existence"],
    },
    {
        "id": "relationship-roman-aksum-trade",
        "relationship_type": "trade_exchange",
        "subject_id": "roman-empire",
        "subject_kind": "civilization",
        "target_id": "aksumite-kingdom",
        "target_kind": "civilization",
        "label": "Roman-Aksum Red Sea trade exchange",
        "summary": "Trade reach should be modeled separately from formal political control, especially across the Red Sea and Nile-to-port systems.",
        "valid_from_year": -30,
        "valid_to_year": 300,
        "confidence": "medium",
        "review_status": "seeded",
        "source_note": "Seed relationship proving that thematic exchange systems deserve first-class representation alongside territory.",
        "source_record_ids": ["aksum-source", "route-aksum-adulis", "event-aksum-trade"],
        "claim_ids": ["claim-aksum-route"],
    },
]

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


IMPORT_JOBS: list[ImportJob] = [
    ImportJob(
        id="import-job-manual-seed-117",
        dataset_slug="manual-seed-117",
        dataset_label="Manual Seed 117 CE",
        status="completed",
        source_type="manual_seed",
        bucket=NORMALIZED_BUCKET,
        object_prefix="imports/manual-seed-117/2026-07-21/",
        initiated_by="rico",
        manifest_artifact_id="artifact-import-manifest-manual-seed-117",
        started_at=SEED_CREATED_AT,
        completed_at=SEED_UPDATED_AT,
        records_discovered=len(SOURCE_RECORDS),
        records_imported=len(SOURCE_RECORDS),
        artifacts_created=len(SOURCE_RECORDS) + 4,
        notes="Bootstrap seed import that materializes the first atlas payload, source records, and interpretation layers.",
    ),
    ImportJob(
        id="import-job-pleiades-prototype",
        dataset_slug="pleiades-prototype",
        dataset_label="Pleiades Prototype Import",
        status="planned",
        source_type="gazetteer",
        bucket=RAW_BUCKET,
        object_prefix="imports/pleiades-prototype/queued/",
        initiated_by="rico",
        manifest_artifact_id=None,
        started_at=None,
        completed_at=None,
        records_discovered=0,
        records_imported=0,
        artifacts_created=0,
        notes="Planned prototype import for ancient place gazetteer records and URI preservation.",
    ),
    ImportJob(
        id="import-job-whg-normalization",
        dataset_slug="whg-normalization",
        dataset_label="World Historical Gazetteer Normalization",
        status="planned",
        source_type="gazetteer",
        bucket=RAW_BUCKET,
        object_prefix="imports/whg-normalization/queued/",
        initiated_by="rico",
        manifest_artifact_id=None,
        started_at=None,
        completed_at=None,
        records_discovered=0,
        records_imported=0,
        artifacts_created=0,
        notes="Planned normalization flow for WHG records and concordance metadata.",
    ),
]


def _mock_sha(seed: str) -> str:
    normalized = seed.replace("/", "-").replace(" ", "-")
    return f"sha256:{normalized}"[:71]


def _build_source_artifacts() -> list[SourceArtifact]:
    artifacts: list[SourceArtifact] = [
        SourceArtifact(
            id="artifact-import-manifest-manual-seed-117",
            artifact_type="import_manifest",
            storage_provider="s3_compatible",
            bucket=NORMALIZED_BUCKET,
            object_key="imports/manual-seed-117/2026-07-21/manifest.json",
            mime_type="application/json",
            byte_size=4096,
            sha256=_mock_sha("imports/manual-seed-117/manifest"),
            import_job_id="import-job-manual-seed-117",
            metadata_json={
                "dataset_slug": "manual-seed-117",
                "contains": ["source_records", "claims", "layers", "events"],
            },
            created_at=SEED_CREATED_AT,
            updated_at=SEED_UPDATED_AT,
        )
    ]

    for record in SOURCE_RECORDS:
        artifacts.append(
            SourceArtifact(
                id=f"artifact-source-{record.id}",
                artifact_type="raw_source_record",
                storage_provider="s3_compatible",
                bucket=RAW_BUCKET,
                object_key=f"sources/manual-seed/{record.feature_kind}/{record.id}.json",
                mime_type="application/json",
                byte_size=2048,
                sha256=_mock_sha(record.id),
                source_record_id=record.id,
                import_job_id="import-job-manual-seed-117",
                derived_from_artifact_id="artifact-import-manifest-manual-seed-117",
                metadata_json={
                    "feature_id": record.feature_id,
                    "feature_kind": record.feature_kind,
                    "feature_label": record.feature_label,
                },
                created_at=SEED_CREATED_AT,
                updated_at=SEED_UPDATED_AT,
            )
        )

    for layer in CIVILIZATION_LAYERS:
        source_record_id = layer.source_record_ids[0] if layer.source_record_ids else None
        artifacts.append(
            SourceArtifact(
                id=f"artifact-layer-{layer.id}",
                artifact_type="derived_geometry",
                storage_provider="s3_compatible",
                bucket=DERIVED_BUCKET,
                object_key=f"geometries/{layer.civilization_id}/{layer.id}.geojson",
                mime_type="application/geo+json",
                byte_size=3072,
                sha256=_mock_sha(layer.id),
                source_record_id=source_record_id,
                layer_id=layer.id,
                import_job_id="import-job-manual-seed-117",
                derived_from_artifact_id=(
                    f"artifact-source-{source_record_id}" if source_record_id else None
                ),
                metadata_json={
                    "variant_group": layer.variant_group,
                    "interpretation_label": layer.interpretation_label,
                    "interpretation_kind": layer.interpretation_kind,
                },
                created_at=SEED_CREATED_AT,
                updated_at=SEED_UPDATED_AT,
            )
        )

    return artifacts



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
        id="claim-roman-boundary-core",
        claim_type="supports_boundary",
        subject_id="layer-roman-empire-core",
        subject_kind="civilization_layer",
        object_id="roman-empire",
        object_kind="civilization",
        confidence="medium_high",
        review_status="seeded",
        notes="Conservative Roman boundary geometry emphasizes long-held provincial control and intentionally excludes the most maximal campaign reading in Mesopotamia.",
        valid_from_year=-27,
        valid_to_year=395,
        source_record_ids=["roman-cambridge"],
    ),
    HistoricalClaim(
        id="claim-roman-boundary-maximal",
        claim_type="supports_boundary",
        subject_id="layer-roman-empire-trajanic-east",
        subject_kind="civilization_layer",
        object_id="roman-empire",
        object_kind="civilization",
        confidence="medium",
        review_status="needs_review",
        notes="Maximal Roman frontier reading includes Trajanic eastern campaign reach and should be treated as a disputed campaign-moment interpretation rather than a final imperial border.",
        valid_from_year=114,
        valid_to_year=117,
        source_record_ids=["roman-cambridge", "event-trajan-east"],
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
        id="claim-han-boundary-core",
        claim_type="supports_boundary",
        subject_id="layer-han-dynasty-core",
        subject_kind="civilization_layer",
        object_id="han-dynasty",
        object_kind="civilization",
        confidence="medium_high",
        review_status="seeded",
        notes="The Han core layer is a placeholder administrative footprint rather than a fully reviewed frontier reconstruction.",
        valid_from_year=-202,
        valid_to_year=220,
        source_record_ids=["han-cambridge"],
    ),
    HistoricalClaim(
        id="claim-han-western-regions-influence",
        claim_type="supports_influence_zone",
        subject_id="layer-han-dynasty-western-regions",
        subject_kind="civilization_layer",
        object_id="han-dynasty",
        object_kind="civilization",
        confidence="medium",
        review_status="needs_review",
        notes="Western Regions activity is modeled as corridor influence and military reach, not as equivalent to direct administrative rule.",
        valid_from_year=91,
        valid_to_year=123,
        source_record_ids=["han-cambridge", "event-han-western-regions"],
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


def _layer_specs_for_civilization(civilization: Civilization) -> list[dict[str, object]]:
    if civilization.id in LAYER_VARIANTS:
        return LAYER_VARIANTS[civilization.id]

    layer_name, layer_type = DEFAULT_LAYER_CONFIG.get(
        civilization.id,
        ("Operational seed layer", "source_reported_extent"),
    )
    return [
        {
            "id": f"layer-{civilization.id}",
            "name": layer_name,
            "layer_type": layer_type,
            "variant_group": f"{civilization.id}-default-reading",
            "interpretation_label": "Seed operational reading",
            "interpretation_kind": "boundary_variant",
            "display_order": 0,
            "is_primary": True,
            "geometry": civilization.polygon,
            "confidence": civilization.confidence,
            "review_status": civilization.review_status,
            "source_note": civilization.source_notes,
        }
    ]


def _build_layers() -> list[CivilizationLayer]:
    layers: list[CivilizationLayer] = []

    for civilization in WORLD_117.civilizations:
        for spec in _layer_specs_for_civilization(civilization):
            layer_id = str(spec["id"])
            geometry = spec.get("geometry", civilization.polygon)
            layers.append(
                CivilizationLayer(
                    id=layer_id,
                    civilization_id=civilization.id,
                    name=str(spec["name"]),
                    layer_type=str(spec["layer_type"]),
                    variant_group=str(spec.get("variant_group") or ""),
                    interpretation_label=str(spec.get("interpretation_label") or ""),
                    interpretation_kind=str(spec.get("interpretation_kind") or ""),
                    is_primary=bool(spec.get("is_primary", False)),
                    display_order=int(spec.get("display_order", 0)),
                    valid_from_year=int(spec.get("valid_from_year", civilization.start_year)),
                    valid_to_year=int(spec.get("valid_to_year", civilization.end_year)),
                    geometry_json=_polygon_to_geojson(geometry),
                    geometry_placeholder=civilization.extent_note,
                    is_placeholder=True,
                    confidence=str(spec.get("confidence", civilization.confidence)),
                    review_status=str(spec.get("review_status", civilization.review_status)),
                    source_note=str(spec.get("source_note", civilization.source_notes)),
                    created_at=SEED_CREATED_AT,
                    updated_at=SEED_UPDATED_AT,
                    source_record_ids=SOURCE_RECORD_IDS_BY_FEATURE[civilization.id],
                    claim_ids=CLAIM_IDS_BY_SUBJECT[layer_id],
                )
            )

    return layers


CIVILIZATION_LAYERS = _build_layers()
SOURCE_ARTIFACTS = _build_source_artifacts()


def _build_relationships() -> list[HistoricalRelationship]:
    return [
        HistoricalRelationship(
            id=str(item["id"]),
            relationship_type=str(item["relationship_type"]),
            subject_id=str(item["subject_id"]),
            subject_kind=str(item["subject_kind"]),
            target_id=str(item["target_id"]),
            target_kind=str(item["target_kind"]),
            label=str(item["label"]),
            summary=str(item["summary"]),
            valid_from_year=int(item["valid_from_year"]),
            valid_to_year=int(item["valid_to_year"]),
            confidence=str(item["confidence"]),
            review_status=str(item["review_status"]),
            source_note=str(item["source_note"]),
            source_record_ids=list(item["source_record_ids"]),
            claim_ids=list(item["claim_ids"]),
        )
        for item in RELATIONSHIP_SEEDS
    ]


HISTORICAL_RELATIONSHIPS = _build_relationships()


def _build_review_assignments() -> list[ReviewAssignment]:
    assignments: list[ReviewAssignment] = []

    for claim in HISTORICAL_CLAIMS:
        if claim.review_status == "reviewed":
            continue
        assignments.append(
            ReviewAssignment(
                id=f"review-assignment-{claim.id}",
                entity_type="historical_claim",
                entity_id=claim.id,
                current_review_status=claim.review_status,
                target_review_status="reviewed",
                assigned_reviewer="atlas-editorial",
                assigned_by="rico",
                priority="high" if claim.review_status == "needs_review" else "medium",
                due_at=SEED_REVIEW_DUE_AT,
                notes=f"Resolve claim interpretation and provenance sufficiency for {claim.id}.",
                created_at=SEED_UPDATED_AT,
            )
        )

    for layer in CIVILIZATION_LAYERS:
        if layer.review_status == "reviewed":
            continue
        assignments.append(
            ReviewAssignment(
                id=f"review-assignment-{layer.id}",
                entity_type="civilization_layer",
                entity_id=layer.id,
                current_review_status=layer.review_status,
                target_review_status="reviewed",
                assigned_reviewer="atlas-geometry-review",
                assigned_by="rico",
                priority="high" if layer.interpretation_kind == "boundary_variant" else "medium",
                due_at=SEED_REVIEW_DUE_AT,
                notes=f"Review geometry interpretation, confidence, and variant semantics for {layer.name}.",
                created_at=SEED_UPDATED_AT,
            )
        )

    for event in HISTORICAL_EVENTS:
        if event.review_status == "reviewed":
            continue
        assignments.append(
            ReviewAssignment(
                id=f"review-assignment-{event.id}",
                entity_type="historical_event",
                entity_id=event.id,
                current_review_status=event.review_status,
                target_review_status="reviewed",
                assigned_reviewer="atlas-timeline-review",
                assigned_by="rico",
                priority="medium",
                due_at=SEED_REVIEW_DUE_AT,
                notes=f"Confirm event framing, display date, and historical impact language for {event.label}.",
                created_at=SEED_UPDATED_AT,
            )
        )

    return assignments


REVIEW_ASSIGNMENTS = _build_review_assignments()


REVIEW_DECISIONS: list[ReviewDecision] = [
    ReviewDecision(
        id="review-decision-roman-existence",
        assignment_id="bootstrap-reviewed-roman-existence",
        entity_type="historical_claim",
        entity_id="claim-roman-existence",
        decision_type="approve",
        previous_review_status="seeded",
        new_review_status="reviewed",
        reviewer="atlas-editorial",
        rationale="Roman existence claim is a stable bootstrap fact with adequate seeded reference support.",
        created_at=SEED_UPDATED_AT,
    ),
    ReviewDecision(
        id="review-decision-han-existence",
        assignment_id="bootstrap-reviewed-han-existence",
        entity_type="historical_claim",
        entity_id="claim-han-existence",
        decision_type="approve",
        previous_review_status="seeded",
        new_review_status="reviewed",
        reviewer="atlas-editorial",
        rationale="Han existence claim is a stable bootstrap fact with adequate seeded reference support.",
        created_at=SEED_UPDATED_AT,
    ),
]


REVISION_RECORDS: list[RevisionRecord] = [
    RevisionRecord(
        id="revision-roman-layer-core-seed",
        entity_type="civilization_layer",
        entity_id="layer-roman-empire-core",
        revision_kind="geometry_variant_seed",
        summary="Seeded conservative Roman provincial-core geometry artifact.",
        diff_excerpt="Created a primary conservative provincial-core geometry distinct from the maximal Trajanic campaign reading.",
        actor="rico",
        artifact_id="artifact-layer-layer-roman-empire-core",
        review_decision_id=None,
        created_at=SEED_UPDATED_AT,
    ),
    RevisionRecord(
        id="revision-roman-existence-review",
        entity_type="historical_claim",
        entity_id="claim-roman-existence",
        revision_kind="review_decision",
        summary="Reviewed Roman existence claim.",
        diff_excerpt="Moved review status from seeded to reviewed with editorial approval rationale.",
        actor="atlas-editorial",
        artifact_id="artifact-source-roman-cambridge",
        review_decision_id="review-decision-roman-existence",
        created_at=SEED_UPDATED_AT,
    ),
]


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
        layers=[
            layer
            for layer in CIVILIZATION_LAYERS
            if is_active(layer.valid_from_year, layer.valid_to_year, year)
        ],
        relationships=[
            relationship
            for relationship in HISTORICAL_RELATIONSHIPS
            if is_active(relationship.valid_from_year, relationship.valid_to_year, year)
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
