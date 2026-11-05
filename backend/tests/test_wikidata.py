import json
import pytest
from app.ingestion.wikidata import WikidataAdapter


def row(**changes):
    values = dict(
        kind="leader",
        civilization="http://www.wikidata.org/entity/Q12544",
        value="http://www.wikidata.org/entity/Q1425",
        valueLabel="Trajan",
        statement="http://www.wikidata.org/entity/statement/Q12544-test",
        start="+0098-01-01T00:00:00Z",
        end="+0117-01-01T00:00:00Z",
        startPrecision="9",
        endPrecision="9",
    )
    values.update(changes)
    return {k: {"type": "literal", "value": v} for k, v in values.items()}


def result(rows):
    return WikidataAdapter({"civilizations": {"Q12544": "roman-empire"}}).normalize(
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
        WikidataAdapter({"civilizations": {"Q12544": "roman-empire"}}),
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
