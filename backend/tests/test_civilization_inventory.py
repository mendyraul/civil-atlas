import json
from pathlib import Path

from app.ingestion.cliopatria import CliopatriaAdapter, load_crosswalk
from app.seed import catalog
from app.seed.import_world117 import import_fixture
from app.services.repository import AtlasRepository
from tests.test_pleiades import database  # noqa: F401

ROOT = Path(__file__).parents[1]
INVENTORY = json.loads(
    (ROOT / "data/imports/crosswalks/cliopatria-117-inventory.json").read_text()
)


def test_inventory_accounts_for_every_omission_without_mapping_unresolved_identities():
    rows = INVENTORY["omissions"]
    assert len(rows) == len({r["wikidata"] for r in rows}) == 28
    mapping = load_crosswalk()
    assert sum(r["status"] == "added_pending_review" for r in rows) == 21
    for row in rows:
        assert row["reason"]
        if row["status"] == "unresolved":
            assert row["wikidata"] not in mapping
        else:
            assert mapping[row["wikidata"]]["cliopatria_name"] == row["name"]


def test_added_geometry_dates_and_cited_existence_are_preserved():
    raw = (ROOT / "tests/fixtures/cliopatria/expanded-117.geojson").read_bytes()
    features = json.loads(raw)["features"]
    ids = [f["properties"]["Wikidata"] for f in features]
    result = CliopatriaAdapter(117).normalize(
        raw, ids, "inventory-test", "2026-11-05T15:00:00Z"
    )
    seed_layers = {r.id: r for r in catalog.DATASETS["layers"]}
    claims = {r.id: r for r in catalog.DATASETS["claims"]}
    civilizations = {r.id: r for r in catalog.DATASETS["civilizations"]}
    for layer in result.datasets["layers"]:
        assert (
            seed_layers[layer["id"]].model_dump(mode="json")["geometry_json"]
            == layer["geometry_json"]
        )
        civ = civilizations[layer["civilization_id"]]
        assert civ.review_status == "needs_review"
        assert civ.capital == "Not established"
        claim = claims[f"claim-{civ.id}-source-existence"]
        assert claim.source_id and claim.citation_locator and claim.source_record_ids
        assert claim.review_status == "needs_review"
        assert (civ.start_year, civ.end_year) == (
            layer["valid_from_year"],
            layer["valid_to_year"],
        )


def test_expanded_seed_remains_private_and_replay_is_idempotent(database, monkeypatch):  # noqa: F811
    from app.seed import import_world117

    monkeypatch.setattr(import_world117, "session_scope", database)
    import_fixture(publish=True)
    replay = import_fixture(publish=True)
    assert replay["created"] == replay["updated"] == 0
    with database() as session:
        repo = AtlasRepository(session)
        for row in INVENTORY["omissions"]:
            if row["status"] == "added_pending_review":
                assert repo.get("civilizations", row["civilization_id"]) is None
                assert repo.get(
                    "civilizations", row["civilization_id"], published_only=False
                )


def test_seed_receipt_preserves_later_review_decisions(database, monkeypatch):
    from app.seed import import_world117

    monkeypatch.setattr(import_world117, "session_scope", database)
    import_fixture(publish=True)
    with database() as session:
        repo = AtlasRepository(session)
        repo.update_review_status("civilizations", "funan", "reviewed", "test:reviewer")
    replay = import_fixture(publish=True)
    assert replay["status"] == "duplicate"
    with database() as session:
        assert (
            AtlasRepository(session).get("civilizations", "funan")["review_status"]
            == "reviewed"
        )
