import json
from pathlib import Path
from sqlalchemy import text
from app.seed.catalog import (
    DATASET_VERSION,
    EVIDENCE_LINKS,
    HISTORICAL_CLAIMS,
    MANIFEST_SHA256,
    REVIEW_ASSIGNMENTS,
    REVIEW_DECISIONS,
)
from app.seed.import_world117 import import_fixture
from app.services.atlas import get_world
from app.db.session import session_scope
FIXTURE=json.loads((Path(__file__).parent/'fixtures/schema_cases.json').read_text())
def test_temporal_queries_are_closed_and_support_bce():
    world=get_world(-500)
    assert world.year == -500
    for item in [*world.civilizations,*world.nodes,*world.routes]: assert item.start_year <= -500 <= item.end_year

def test_claims_have_provenance():
    linked={(link.entity_id, link.claim_type) for link in EVIDENCE_LINKS}
    assert HISTORICAL_CLAIMS
    assert all(any(link.entity_id == claim.id or link.entity_id == claim.subject_id for link in EVIDENCE_LINKS) for claim in HISTORICAL_CLAIMS)

def test_review_transitions_are_auditable():
    assignments={item.id:item for item in REVIEW_ASSIGNMENTS}
    assert REVIEW_DECISIONS
    for decision in REVIEW_DECISIONS:
        assignment=assignments[decision.assignment_id]
        assert decision.previous_review_status == assignment.current_review_status
        assert decision.new_review_status == assignment.target_review_status

def test_schema_fixture_covers_edge_cases():
    temporal=FIXTURE['temporal']; geometry=FIXTURE['geometry']
    assert any(x['valid_from_year'] < 0 for x in temporal)
    assert any(x.get('certainty') == 'circa' for x in temporal)
    assert len([x for x in temporal if x.get('variant_group') == 'frontier']) == 2
    assert {x['type'] for x in geometry} == {'Polygon','MultiPolygon'}
    assert len(next(x for x in geometry if x['id']=='polygon-hole')['coordinates']) == 2
    ring=next(x for x in geometry if x['id']=='antimeridian')['coordinates'][0]
    assert max(p[0] for p in ring)-min(p[0] for p in ring)>180


def test_versioned_manifest_is_repeatable_and_audited():
    dry_run = import_fixture(dry_run=True)
    assert dry_run["dataset_version"] == DATASET_VERSION
    assert dry_run["manifest_sha256"] == f"sha256:{MANIFEST_SHA256}"
    assert dry_run["records_discovered"] > 0
    first = import_fixture(actor="test:repeatability")
    second = import_fixture(actor="test:repeatability")
    assert first["created"] + first["updated"] + first["duplicate"] > 0
    assert second["duplicate"] == first["created"] + first["updated"] + first["duplicate"]
    with session_scope() as session:
        public_count = session.execute(
            text("SELECT count(*) FROM atlas_entities WHERE published = TRUE")
        ).scalar_one()
    assert public_count > 0
