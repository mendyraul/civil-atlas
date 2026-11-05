import json
import pytest
from app.ingestion.wikidata import WikidataAdapter


def row(**changes):
    values = dict(
        kind="leader",
        civilization="http://www.wikidata.org/entity/Q2277",
        value="http://www.wikidata.org/entity/Q1425",
        valueLabel="Trajan",
        statement="http://www.wikidata.org/entity/statement/Q2277-test",
        start="+0098-01-01T00:00:00Z",
        end="+0117-01-01T00:00:00Z",
        startPrecision="9",
        endPrecision="9",
    )
    values.update(changes)
    return {k: {"type": "literal", "value": v} for k, v in values.items()}


def result(rows):
    return WikidataAdapter({"civilizations": {"Q2277": "roman-empire"}}).normalize(
        json.dumps({"results": {"bindings": rows}}).encode(),
        [],
        "test-v1",
        "2026-11-05T15:00:00Z",
    )


def test_saved_statements_preserve_tenure_and_qualifiers():
    value = result([row()])
    tenure = value.datasets["offices"][0]
    assert (tenure["start_year"], tenure["end_year"]) == (98, 117)
    assert tenure["qualifiers"] == row()
    assert value.datasets["people"][0]["name"] == "Trajan"
    assert tenure["review_status"] == "needs_review"


@pytest.mark.parametrize(
    "changes",
    [
        {"startPrecision": "8"},
        {"start": ""},
        {"end": "+0090-01-01T00:00:00Z"},
        {"civilization": "http://www.wikidata.org/entity/Q99999"},
        {"kind": "capital"},
    ],
)
def test_uncertain_dates_or_unmapped_references_remain_omissions(changes):
    value = result([row(**changes)])
    assert value.omissions and value.datasets["source_records"]
    assert not value.datasets["offices"] and not value.datasets["capital_roles"]


def test_public_context_requires_reviewed_person_tenure_and_sources(
    database, tmp_path, monkeypatch
):
    from app.ingestion.pipeline import prepare_import, import_bundle
    from app.services.repository import AtlasRepository
    from app.services import enrichment

    monkeypatch.setattr(enrichment, "session_scope", database)
    path = tmp_path / "sparql.json"
    path.write_text(json.dumps({"results": {"bindings": [row()]}}))
    bundle = prepare_import(
        WikidataAdapter({"civilizations": {"Q2277": "roman-empire"}}),
        path,
        [],
        "test-v1",
        "2026-11-05T15:00:00Z",
    )
    import_bundle(bundle, tmp_path / "archive", "test:wd")
    assert enrichment.civilization_context("roman-empire", 117)["leaders"] == []
    with database() as session:
        from sqlalchemy import text

        assert (
            session.execute(text("SELECT count(*) FROM office_tenures")).scalar_one()
            >= 1
        )
        repo = AtlasRepository(session)
        for kind in ("people", "offices"):
            for record in bundle.manifest["datasets"][kind]:
                repo.update_review_status(kind, record["id"], "reviewed", "test:review")
    assert enrichment.civilization_context("roman-empire", 117)["leaders"] == []
    with database() as session:
        repo = AtlasRepository(session)
        for kind in ("sources", "source_records"):
            for record in bundle.manifest["datasets"][kind]:
                repo.update_review_status(kind, record["id"], "reviewed", "test:review")
    assert (
        enrichment.civilization_context("roman-empire", 117)["leaders"][0]["label"]
        == "Trajan"
    )
    assert enrichment.civilization_context("roman-empire", 118)["leaders"] == []


from tests.test_pleiades import database  # noqa: E402,F401


def test_real_saved_sparql_statement_maps_canonical_rome_and_emperor_office(
    database, tmp_path
):
    from pathlib import Path

    root = Path(__file__).parents[1]
    mapping = json.loads(
        (root / "data/imports/crosswalks/wikidata-world117.json").read_bytes()
    )
    raw = (
        Path(__file__).parent / "fixtures/wikidata/trajan-tenure.sparql.json"
    ).read_bytes()
    value = WikidataAdapter(mapping).normalize(
        raw, [], "trajan-real", "2026-11-05T22:00:00Z"
    )
    assert value.omissions == []
    tenure = value.datasets["offices"][0]
    assert tenure["civilization_id"] == "roman-empire"
    assert tenure["office_wikidata_id"] == "Q842606"
    assert tenure["office"] == "Roman emperor"
    assert (tenure["start_year"], tenure["end_year"]) == (98, 117)
    assert tenure["qualifiers"] == json.loads(raw)["results"]["bindings"][0]
    assert value.datasets["people"][0]["name"] == "Trajan"
    from app.ingestion.pipeline import prepare_import, import_bundle
    from sqlalchemy import text
    from app.services.repository import AtlasRepository

    snapshot = Path(__file__).parent / "fixtures/wikidata/trajan-tenure.sparql.json"
    bundle = prepare_import(
        WikidataAdapter(mapping), snapshot, [], "trajan-real", "2026-11-05T21:54:46Z"
    )
    import_bundle(bundle, tmp_path / "archive", "test:real-wikidata")
    with database() as session:
        office = session.execute(
            text("""SELECT e.canonical_name,o.office_category
            FROM office_tenures t JOIN offices o ON t.office_entity_id=o.entity_id
            JOIN entities e ON e.id=o.entity_id WHERE t.id=:id"""),
            {"id": tenure["id"]},
        ).one()
        assert (
            office.canonical_name == "Roman emperor"
            and office.office_category == "position_held"
        )
        assert AtlasRepository(session).get("offices", tenure["id"]) is None
    assert all(
        record["review_status"] == "needs_review"
        for records in value.datasets.values()
        for record in records
    )


def test_sparql_bce_years_use_rdf_numbering_and_validate_calendar_dates():
    from app.ingestion.wikidata import dated_year

    assert dated_year({"value": "0000-01-01T00:00:00Z"}) == -1
    assert dated_year({"value": "-0043-03-15T12:30:00Z"}) == -44
    for value in [
        "0117-13-01T00:00:00Z",
        "0117-02-30T00:00:00Z",
        "0117-01-01T24:00:00Z",
    ]:
        with pytest.raises(ValueError):
            dated_year({"value": value})


@pytest.mark.parametrize(
    "kind,collection", [("capital", "capital_roles"), ("event", "events")]
)
def test_capitals_and_events_keep_place_dates_and_source_assertions(kind, collection):
    binding = row(
        kind=kind,
        value="http://www.wikidata.org/entity/Q220",
        valueLabel="Synthetic place/event",
        place="http://www.wikidata.org/entity/Q220",
        start="+0117-01-01T00:00:00Z",
        end="+0117-01-01T00:00:00Z",
    )
    value = WikidataAdapter(
        {"civilizations": {"Q2277": "roman-empire"}, "places": {"Q220": "roma"}}
    ).normalize(
        json.dumps({"results": {"bindings": [binding]}}).encode(),
        [],
        "synthetic-place-v1",
        "2026-11-05T21:00:00Z",
    )
    assert value.omissions == []
    record = value.datasets[collection][0]
    assert (
        record["place_id"] == "roma"
        if kind == "capital"
        else record["place_ids"] == ["roma"]
    )
    assert (record["start_year"], record["end_year"]) == (117, 117)
    assert (
        record["statement"] == binding["statement"]["value"]
        and record["source_record_ids"]
    )
    assert record["review_status"] == "needs_review"


def test_dated_capital_context_requires_civilization_and_place_lifetimes(
    database, monkeypatch
):
    from app.services import enrichment
    from app.services.repository import AtlasRepository
    from tests.release_fixture import dataset

    monkeypatch.setattr(enrichment, "session_scope", database)
    records = dataset()
    with database() as session:
        repo = AtlasRepository(session)
        for item in records:
            repo.upsert(
                item["entity_type"],
                item["external_id"],
                item["payload"],
                "test:context",
                published=True,
            )
    assert (
        enrichment.civilization_context("roman-empire", 117)["capitals"][0]["label"]
        == "Synthetic capital"
    )
    with database() as session:
        repo = AtlasRepository(session)
        place = repo.get("places", "release-a")
        place["end_year"] = 116
        repo.upsert("places", "release-a", place, "test:context", published=True)
    assert enrichment.civilization_context("roman-empire", 117)["capitals"] == []
    assert enrichment.civilization_context("roman-empire", 117)["leaders"]
    with database() as session:
        repo = AtlasRepository(session)
        civilization = repo.get("civilizations", "roman-empire")
        civilization["end_year"] = 116
        repo.upsert(
            "civilizations",
            "roman-empire",
            civilization,
            "test:context",
            published=True,
        )
    assert enrichment.civilization_context("roman-empire", 117) == {
        "leaders": [],
        "capitals": [],
    }
