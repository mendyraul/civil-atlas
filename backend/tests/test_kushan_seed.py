import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.ingestion.cliopatria import CliopatriaAdapter, load_crosswalk
from app.ingestion.pipeline import prepare_import
from app.main import app
from app.seed import catalog
from app.seed.import_world117 import import_fixture
from app.seed import import_world117
from app.services.repository import AtlasRepository
from tests.test_pleiades import database  # noqa: F401

ROOT = Path(__file__).parents[2]
FIXTURE = Path(__file__).parent / "fixtures/cliopatria/kushan-117.geojson"


def test_kushan_seed_has_cited_claim_and_matching_demo_identity():
    civilization = next(c for c in catalog.DATASETS["civilizations"] if c.id == "kushan-empire")
    assert (civilization.start_year, civilization.end_year, civilization.capital) == (30, 375, "Purushapura")
    assert civilization.review_status == "needs_review"
    claim = next(c for c in catalog.DATASETS["claims"] if c.id == "claim-kushan-existence")
    assert claim.source_id and claim.citation_locator
    assert (claim.valid_from_year, claim.valid_to_year) == (117, 126)
    assert claim.review_status == "needs_review"
    assert import_fixture(dry_run=True)["dataset_version"] == "1.1.0"


def test_kushan_crosswalk_preserves_the_bundled_source_geometry():
    mapping = load_crosswalk()["Q25979"]
    assert mapping == {"civilization_id": "kushan-empire", "variant_group": "kushan-empire-source-readings", "cliopatria_name": "Kushan Empire"}
    result = prepare_import(CliopatriaAdapter(117), FIXTURE, ["Q25979"], "kushan-fixture-v1", "2026-10-27T12:00:00Z")
    assert result.manifest["omissions"] == []
    layer = result.manifest["datasets"]["layers"][0]
    original = next(l for l in json.loads((ROOT / "frontend/data/history/century-100.json").read_text())["layers"]
                    if l["id"] == layer["id"])
    assert layer["geometry_json"] == original["geometryJson"]
    assert layer["review_status"] == "needs_review" and not layer["is_primary"]
    assert layer["variant_group"] == mapping["variant_group"]


def test_kushan_is_not_public_before_editorial_review(database):  # noqa: F811
    with database() as session:
        repository = AtlasRepository(session)
        record = repository.get("civilizations", "kushan-empire", published_only=False)
        assert record is not None
        assert repository.get("civilizations", "kushan-empire", published_only=True) is None
        assert repository.get("layers", "cliopatria-kushan-empire-117ce-126ce", published_only=True) is None
    public = TestClient(app).get("/api/v1/civilizations")
    assert public.status_code == 200
    assert all(c["id"] != "kushan-empire" for c in public.json())


def test_repeated_seed_publish_is_idempotent_and_keeps_kushan_private(database, monkeypatch):  # noqa: F811
    monkeypatch.setattr(import_world117, 'session_scope', database)
    import_fixture(publish=True, actor='test:seed-replay')
    replay = import_fixture(publish=True, actor='test:seed-replay')
    assert replay['created'] == replay['updated'] == 0
    with database() as session:
        repo = AtlasRepository(session)
        assert repo.get('civilizations', 'roman-empire') is not None
        for kind, identifier in [('civilizations', 'kushan-empire'), ('claims', 'claim-kushan-existence'),
                                 ('layers', 'cliopatria-kushan-empire-117ce-126ce')]:
            assert repo.get(kind, identifier, published_only=False)['review_status'] == 'needs_review'
            assert repo.get(kind, identifier) is None
