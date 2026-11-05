from io import BytesIO
import zipfile
import pytest
from sqlalchemy import text
from app import data_release
from app.data_release import build_archive, read_archive, load_release
from tests.test_pleiades import database  # noqa: F401


def record():
    return {
        "entity_type": "places",
        "external_id": "release-test-place",
        "payload": dict(
            id="release-test-place",
            slug="release-test-place",
            canonical_name="Release fixture",
            latitude=1,
            longitude=2,
            start_year=100,
            end_year=200,
            place_type="city",
            confidence_level="low",
            review_status="reviewed",
            created_at="2026-11-05T15:00:00Z",
            updated_at="2026-11-05T15:00:00Z",
        ),
    }


def test_release_roundtrip_and_licenses():
    raw, manifest = build_archive([record()], "2026.11")
    records, result = read_archive(raw)
    assert records[0]["payload"]["canonical_name"] == "Release fixture"
    assert result == manifest and result["counts"] == {"places": 1}
    with zipfile.ZipFile(BytesIO(raw)) as archive:
        assert {"ATTRIBUTION.md", "DATA_LICENSE.md"} <= set(archive.namelist())


def test_corruption_schema_and_private_types_fail():
    raw, _ = build_archive([record()], "2026.11")
    with zipfile.ZipFile(BytesIO(raw)) as archive:
        files = {name: archive.read(name) for name in archive.namelist()}
    files["records.json"] = b"[]"
    output = BytesIO()
    with zipfile.ZipFile(output, "w") as archive:
        for name, value in files.items():
            archive.writestr(name, value)
    with pytest.raises(ValueError, match="checksum"):
        read_archive(output.getvalue())
    with pytest.raises(ValueError, match="unsupported public"):
        build_archive(
            [{"entity_type": "import_jobs", "external_id": "x", "payload": {}}],
            "2026.11",
        )
    with pytest.raises(ValueError, match="duplicate"):
        build_archive([record(), record()], "2026.11")


def test_missing_public_dependency_fails_before_writing():
    item = record()
    item["payload"]["source_record_ids"] = ["private-source"]
    # Place's public schema does not expose source_record_ids; use a sourced person instead.
    item = {
        "entity_type": "people",
        "external_id": "person-x",
        "payload": {
            "id": "person-x",
            "name": "Test",
            "wikidata_id": "Q1",
            "review_status": "reviewed",
            "source_record_ids": ["private-source"],
        },
    }
    with pytest.raises(ValueError, match="missing public dependency"):
        build_archive([item], "2026.11")


def test_load_is_transactional_and_requires_empty_database(
    database, tmp_path, monkeypatch
):
    monkeypatch.setattr(data_release, "session_scope", database)
    raw, _ = build_archive([record()], "2026.11")
    path = tmp_path / "release.zip"
    path.write_bytes(raw)
    with pytest.raises(ValueError, match="empty"):
        load_release(path)
    with database() as session:
        session.execute(text("DELETE FROM revision_records"))
        session.execute(text("DELETE FROM atlas_entities"))
    assert load_release(path, dry_run=True)["counts"] == {"places": 1}
    with database() as session:
        assert (
            session.execute(text("SELECT count(*) FROM atlas_entities")).scalar_one()
            == 0
        )
    load_release(path)
    with database() as session:
        assert (
            session.execute(
                text("SELECT count(*) FROM atlas_entities WHERE published")
            ).scalar_one()
            == 1
        )
        assert (
            session.execute(
                text("SELECT ST_X(geom) FROM places WHERE id='release-test-place'")
            ).scalar_one()
            == 2
        )
    with pytest.raises(ValueError, match="empty"):
        load_release(path)


def test_projection_failure_rolls_back_all_loaded_records(
    database, tmp_path, monkeypatch
):
    from app.services.repository import AtlasRepository

    monkeypatch.setattr(data_release, "session_scope", database)
    with database() as session:
        session.execute(text("DELETE FROM revision_records"))
        session.execute(text("DELETE FROM atlas_entities"))
    raw, _ = build_archive([record()], "2026.11")
    path = tmp_path / "release.zip"
    path.write_bytes(raw)

    def fail(*args):
        raise ValueError("synthetic projection failure")

    monkeypatch.setattr(AtlasRepository, "upsert_spatial_projection", fail)
    with pytest.raises(ValueError, match="projection failure"):
        load_release(path)
    with database() as session:
        assert (
            session.execute(text("SELECT count(*) FROM atlas_entities")).scalar_one()
            == 0
        )


def test_release_omits_operational_metadata_from_public_payloads():
    value = record()
    value["payload"].update(
        secret_access_key="not-a-real-secret",
        storage_provider="local",
        artifact_dir="/private/example",
    )
    raw, _ = build_archive([value], "2026.11")
    records, _ = read_archive(raw)
    assert "secret_access_key" not in records[0]["payload"]
    assert "artifact_dir" not in records[0]["payload"]
