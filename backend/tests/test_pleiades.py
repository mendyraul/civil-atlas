from contextlib import contextmanager
import gzip
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys

from fastapi.testclient import TestClient
import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api import routes
from app.db.session import engine
from app.ingestion import pipeline
from app.ingestion.pipeline import LocalArchive, import_bundle, prepare_import
from app.ingestion.pleiades import LICENSE, PleiadesAdapter
from app.main import app
from app.services import atlas
from app.services.repository import AtlasRepository

FIXTURE = Path(__file__).parent / "fixtures/pleiades/rome.json"
RETRIEVED = "2026-09-25T18:22:31Z"


def record(**overrides):
    # Synthetic dates exercise mapping; these are not historical fixture claims.
    value = json.loads(FIXTURE.read_bytes())
    value.update(start=-100, end=200)
    value.update(overrides)
    return value


def bundle(tmp_path, records=None, version="test-pilot-v1"):
    snapshot = tmp_path / "snapshot.json"
    snapshot.write_text(json.dumps(records if records is not None else [record()]))
    return prepare_import(PleiadesAdapter(), snapshot, ["423025"], version, RETRIEVED)


def test_real_sample_retains_provenance_without_inventing_dates(tmp_path):
    result = prepare_import(PleiadesAdapter(), FIXTURE, ["423025"], "rome-v1", RETRIEVED)
    assert result.raw == FIXTURE.read_bytes()
    assert result.manifest["raw_sha256"] == sha256(result.raw).hexdigest()
    assert result.manifest["datasets"]["places"] == []
    source = result.manifest["datasets"]["sources"][0]
    assert source["external_id"] == "423025"
    assert source["license"] == LICENSE
    assert source["retrieved_at"] == RETRIEVED
    assert "Contributors" in source["citation"]
    assert source["review_status"] == "needs_review"
    evidence = result.manifest["datasets"]["source_records"][0]
    assert evidence["confidence"] == "low"
    assert evidence["valid_from_year"] is None
    assert result.manifest["omissions"][0]["reason"] == "no explicit continuous valid date interval"


def test_places_preserve_dates_coordinates_and_source_links(tmp_path):
    result = bundle(tmp_path)
    datasets = result.manifest["datasets"]
    place = datasets["places"][0]
    assert (place["start_year"], place["end_year"]) == (-100, 200)
    assert (place["longitude"], place["latitude"]) == tuple(record()["reprPoint"])
    assert place["id"] == place["slug"] == "pleiades-423025"
    assert place["source_record_ids"] == [datasets["source_records"][0]["id"]]
    assert datasets["evidence"][0]["source_id"] == datasets["sources"][0]["id"]
    assert datasets["evidence"][0]["entity_id"] == place["id"]
    assert result.manifest["omissions"] == []


@pytest.mark.parametrize("overrides", [
    {"reprPoint": None}, {"reprPoint": [181, 0]}, {"reprPoint": [False, 1]},
    {"reprPoint": [0, float("nan")]}, {"start": None}, {"start": True},
    {"start": 201}, {"end": "200"}, {"review_state": "private"},
])
def test_uncertain_source_retained_without_place(tmp_path, overrides):
    result = bundle(tmp_path, [record(**overrides)])
    assert len(result.manifest["datasets"]["source_records"]) == 1
    assert not result.manifest["datasets"]["places"]
    assert result.manifest["omissions"]


def test_location_intervals_do_not_fill_gaps(tmp_path):
    value = json.loads(FIXTURE.read_bytes())
    value["locations"] = [
        {"start": -100, "end": -50, "review_state": "published"},
        {"start": 1, "end": 200, "review_state": "published"},
    ]
    assert not bundle(tmp_path, [value]).manifest["datasets"]["places"]
    value["locations"][1]["start"] = -49
    place = bundle(tmp_path, [value]).manifest["datasets"]["places"][0]
    assert (place["start_year"], place["end_year"]) == (-100, 200)


@pytest.mark.parametrize("data,ids,match", [
    (b"broken", ["423025"], "valid JSON"),
    (b"{}", ["423025"], "expected a Pleiades"),
    (b"[]", ["423025"], "missing from snapshot"),
    (json.dumps([record(), record()]).encode(), ["423025"], "duplicate external"),
    (json.dumps([record()]).encode(), ["423025", "423025"], "without duplicates"),
    (json.dumps([record()]).encode(), ["../423025"], "digits only"),
    (json.dumps([record(title="")]).encode(), ["423025"], "title is required"),
    (json.dumps([record(rights="")]).encode(), ["423025"], "rights statement"),
    (json.dumps([record(rights="All rights reserved")]).encode(), ["423025"], "unsupported license"),
    (json.dumps([record(uri="https://example.com")]).encode(), ["423025"], "canonical URI"),
])
def test_invalid_snapshot_rejected(data, ids, match):
    with pytest.raises(ValueError, match=match):
        PleiadesAdapter().normalize(data, ids, "v1", RETRIEVED)


def test_comprehensive_gzip_dump_and_single_object_supported():
    adapter = PleiadesAdapter()
    single = adapter.normalize(json.dumps(record()).encode(), ["423025"], "v1", RETRIEVED)
    compressed = gzip.compress(json.dumps({"@graph": [record()]}).encode())
    assert adapter.normalize(compressed, ["423025"], "v1", RETRIEVED) == single


def test_dry_run_never_opens_database_or_writes_archive(tmp_path, monkeypatch):
    def forbidden():
        pytest.fail("dry run opened database")
    monkeypatch.setattr(pipeline, "session_scope", forbidden)
    prepared = bundle(tmp_path)
    before = sorted(tmp_path.rglob("*"))
    result = import_bundle(prepared, tmp_path / "archive", "test:operator", dry_run=True)
    assert result["status"] == "validated"
    assert sorted(tmp_path.rglob("*")) == before
    assert bundle(tmp_path).manifest_bytes == prepared.manifest_bytes


def test_invalid_metadata_rejected_before_writes(tmp_path):
    with pytest.raises(ValueError, match="timezone"):
        prepare_import(PleiadesAdapter(), FIXTURE, ["423025"], "v1", "2026-09-25")
    with pytest.raises(ValueError, match="version"):
        prepare_import(PleiadesAdapter(), FIXTURE, ["423025"], " ", RETRIEVED)
    with pytest.raises(ValueError, match="actor"):
        import_bundle(bundle(tmp_path), tmp_path / "archive", "", dry_run=True)


def test_archive_replay_and_corruption(tmp_path):
    archive = LocalArchive(tmp_path)
    raw = FIXTURE.read_bytes()
    key = archive.put("raw-sources", raw)
    path = tmp_path / "raw-sources" / key
    assert key == f"sha256/{sha256(raw).hexdigest()}"
    assert path.read_bytes() == raw
    stat = path.stat()
    assert archive.put("raw-sources", raw) == key
    assert path.stat().st_mtime_ns == stat.st_mtime_ns
    path.write_bytes(b"corruption")
    with pytest.raises(ValueError, match="integrity failure"):
        archive.put("raw-sources", raw)
    assert path.read_bytes() == b"corruption"
    assert len(list(path.parent.iterdir())) == 1


def test_cli_dry_run_and_validation_exit(tmp_path):
    command = [sys.executable, "-m", "app.ingestion.cli", "--snapshot", str(FIXTURE),
               "--place-id", "423025", "--dataset-version", "fixture-v1", "--retrieved-at", RETRIEVED,
               "--actor", "test:cli", "--artifact-dir", str(tmp_path / "archive"), "--dry-run"]
    result = subprocess.run(command, cwd=Path(__file__).parents[1], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["status"] == "validated"
    assert not (tmp_path / "archive").exists()
    result = subprocess.run(command + ["--place-id", "1"], cwd=Path(__file__).parents[1], capture_output=True, text=True)
    assert result.returncode == 1
    assert "missing from snapshot" in result.stderr


@pytest.fixture
def database(monkeypatch):
    try:
        connection = engine.connect()
    except Exception as error:
        if os.environ.get("CI"):
            pytest.fail(f"PostgreSQL required in CI: {error}")
        pytest.skip(f"PostgreSQL unavailable: {error}")
    transaction = connection.begin()

    @contextmanager
    def scope():
        with Session(bind=connection, join_transaction_mode="create_savepoint") as session:
            with session.begin():
                yield session

    for module in (pipeline, routes, atlas):
        monkeypatch.setattr(module, "session_scope", scope)
    try:
        yield scope
    finally:
        transaction.rollback()
        connection.close()


def test_import_review_replay_and_changed_snapshot(database, tmp_path, monkeypatch):
    monkeypatch.setattr(routes.settings, "editorial_api_key", "pilot-test-key")
    client = TestClient(app)
    headers = {"X-Editorial-Key": "pilot-test-key"}
    prepared = bundle(tmp_path)
    archive = tmp_path / "archive"
    assert import_bundle(prepared, archive, "test:pilot")["status"] == "completed"
    assert client.get("/api/places/pleiades-423025").status_code == 404
    assert client.get("/api/v1/review-assignments").status_code == 401
    queue = client.get("/api/v1/review-assignments", headers=headers)
    assert queue.status_code == 200
    assert any(a["id"] == "review-places-pleiades-423025" for a in queue.json())
    with database() as session:
        repo = AtlasRepository(session)
        for kind in ("sources", "source_records", "places", "evidence"):
            assert not any(str(r["id"]).startswith("pleiades-") for r in repo.list(kind))
        for artifact in repo.list("artifacts", published_only=False):
            if artifact["import_job_id"] == prepared.job_id:
                data = (archive / artifact["bucket"] / artifact["object_key"]).read_bytes()
                assert artifact["sha256"] == f"sha256:{sha256(data).hexdigest()}"
                assert artifact["byte_size"] == len(data)

    action = {"assignment_id": "review-places-pleiades-423025", "decision_type": "approve",
              "reviewer": "test:reviewer", "rationale": "Synthetic fixture reviewed for integration test."}
    assert client.post("/api/v1/review-actions", headers=headers, json=action).status_code == 200
    assert client.get("/api/places/pleiades-423025").status_code == 200
    with database() as session:
        before = AtlasRepository(session).data_version()
    assert import_bundle(prepared, archive, "test:another-actor")["status"] == "duplicate"
    with database() as session:
        assert AtlasRepository(session).data_version() == before
    assert client.get("/api/places/pleiades-423025").status_code == 200

    changed = bundle(tmp_path, [record(title="Revised test title")], version="test-pilot-v2")
    assert import_bundle(changed, archive, "test:pilot")["status"] == "completed"
    assert client.get("/api/places/pleiades-423025").status_code == 404
    assert import_bundle(prepared, archive, "test:pilot")["status"] == "duplicate"
    with database() as session:
        repo = AtlasRepository(session)
        current = repo.get("places", "pleiades-423025", published_only=False)
        assert current["canonical_name"] == "Revised test title"
        assert current["review_status"] == "needs_review"
        revisions = session.execute(text("SELECT count(*) FROM revision_records WHERE entity_id=:id"),
                                    {"id": "entity:places:pleiades-423025"}).scalar_one()
        assert revisions >= 2
        assignments = [a for a in repo.list("review_assignments", published_only=False)
                       if a["id"] == action["assignment_id"]]
        assert len(assignments) == 1
        assert assignments[0]["current_review_status"] == "needs_review"
    assert client.post("/api/v1/review-actions", headers=headers, json=action).status_code == 200
    missing_dates = json.loads(FIXTURE.read_bytes())
    lost = bundle(tmp_path, [missing_dates], version="test-pilot-v3")
    import_bundle(lost, archive, "test:pilot")
    assert client.get("/api/places/pleiades-423025").status_code == 404
    assert client.post("/api/v1/review-actions", headers=headers, json=action).status_code == 409
    recovered = bundle(tmp_path, version="test-pilot-v4")
    import_bundle(recovered, archive, "test:pilot")
    assert client.post("/api/v1/review-actions", headers=headers, json=action).status_code == 200


def test_import_transaction_rolls_back_and_retries(database, tmp_path, monkeypatch):
    prepared = bundle(tmp_path)
    original = AtlasRepository.upsert

    def fail_on_place(self, kind, *args, **kwargs):
        if kind == "places":
            raise RuntimeError("injected failure")
        return original(self, kind, *args, **kwargs)

    with monkeypatch.context() as patch:
        patch.setattr(AtlasRepository, "upsert", fail_on_place)
        with pytest.raises(RuntimeError, match="injected failure"):
            import_bundle(prepared, tmp_path / "archive", "test:pilot")
    with database() as session:
        repo = AtlasRepository(session)
        assert repo.get("import_jobs", prepared.job_id, published_only=False) is None
        assert repo.get("sources", "pleiades-source-423025", published_only=False) is None
        assert repo.get("artifacts", f"artifact-raw-{prepared.digest}", published_only=False) is None
    assert import_bundle(prepared, tmp_path / "archive", "test:pilot")["status"] == "completed"


def test_version_reuse_fails_without_changing_database_or_archive(database, tmp_path):
    prepared = bundle(tmp_path)
    archive = tmp_path / "archive"
    import_bundle(prepared, archive, "test:pilot")
    with database() as session:
        before = AtlasRepository(session).data_version()
    files = sorted(archive.rglob("*"))
    changed = bundle(tmp_path, [record(title="Different")])
    with pytest.raises(ValueError, match="version already used"):
        import_bundle(changed, archive, "test:pilot")
    with database() as session:
        assert AtlasRepository(session).data_version() == before
    assert sorted(archive.rglob("*")) == files
