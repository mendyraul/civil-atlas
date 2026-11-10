"""Real export/load between fresh migrated databases, including public behavior."""

from contextlib import contextmanager
import os
from pathlib import Path
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from app import data_release
from app.core.config import settings
from app.main import app
from app.services.repository import AtlasRepository
from tests.release_fixture import dataset


@pytest.fixture
def release_databases():
    url = make_url(settings.database_url)
    admin = create_engine(url, isolation_level="AUTOCOMMIT")
    try:
        connection = admin.connect()
    except Exception as error:
        admin.dispose()
        if os.environ.get("CI"):
            pytest.fail(f"PostgreSQL required for release acceptance: {error}")
        pytest.skip(f"PostgreSQL unavailable: {error}")
    databases = []
    engines = []
    try:
        for suffix in ("source", "target"):
            name = "atlas_release_" + uuid.uuid4().hex[:16] + "_" + suffix
            connection.exec_driver_sql(f'CREATE DATABASE "{name}"')
            databases.append(name)
            engine = create_engine(url.set(database=name))
            engines.append(engine)
            with engine.begin() as session:
                for filename in (
                    "001_init.sql",
                    "002_repository_integrity.sql",
                    "003_publication_state.sql",
                    "004_postgis_and_external_ids.sql",
                    "006_wikidata_projections.sql",
                ):
                    session.exec_driver_sql(
                        (Path(__file__).parents[2] / "db/init" / filename).read_text()
                    )
        yield engines
    finally:
        for engine in engines:
            engine.dispose()
        for name in databases:
            connection.exec_driver_sql(f'DROP DATABASE "{name}" WITH (FORCE)')
        connection.close()
        admin.dispose()


def scope_for(engine):
    @contextmanager
    def scope():
        with Session(engine) as session:
            with session.begin():
                yield session

    return scope


def test_export_load_preserves_public_atlas_context_and_curated_dependencies(
    release_databases, tmp_path, monkeypatch
):
    from app.api import routes
    from app.services import atlas, enrichment, research
    from app.services.episodes import public_episodes

    source, target = map(scope_for, release_databases)
    records = dataset()
    with source() as session:
        repo = AtlasRepository(session)
        for item in records:
            repo.upsert(
                item["entity_type"],
                item["external_id"],
                item["payload"],
                "test:source",
                published=True,
            )
        repo.upsert(
            "artifacts",
            "private-artifact",
            {"id": "private-artifact", "secret_access_key": "not-a-real-secret"},
            "test:source",
        )
        order = {
            "people": -2,
            "offices": -1,
            "civilizations": 0,
            "places": 1,
            "nodes": 2,
            "layers": 3,
            "edges": 4,
            "routes": 5,
        }
        for item in sorted(records, key=lambda r: order.get(r["entity_type"], 99)):
            repo.upsert_knowledge_projection(item["entity_type"], item["payload"])
            if item["entity_type"] in order:
                repo.upsert_spatial_projection(item["entity_type"], item["payload"])

    def snapshots(scope):
        for module in (routes, atlas, enrichment, research):
            monkeypatch.setattr(module, "session_scope", scope)
        client = TestClient(app)
        paths = [
            "/api/v1/world/117",
            "/api/v1/sources",
            "/api/v1/places?year=117",
            "/api/v1/events",
            "/api/v1/civilizations/roman-empire/enrichment?year=117",
            "/api/entities",
        ]
        result = {}
        for path in paths:
            response = client.get(path)
            assert response.status_code == 200, response.text
            result[path] = response.json()
        with scope() as session:
            result["episodes"] = [
                p.model_dump(mode="json")
                for p in public_episodes(AtlasRepository(session))
            ]
        return result

    before = snapshots(source)
    assert len(before["/api/v1/world/117"]["physical_features"]) == 1
    assert (
        before["/api/v1/civilizations/roman-empire/enrichment?year=117"]["leaders"][0][
            "label"
        ]
        == "Synthetic leader"
    )
    assert len(before["episodes"]) == 1
    path = tmp_path / "release.zip"
    monkeypatch.setattr(data_release, "session_scope", source)
    manifest = data_release.export_release("2026.11", path)
    exported, _ = data_release.read_archive(path.read_bytes())
    assert len(exported) == len(records)
    assert all(item["entity_type"] != "artifacts" for item in exported)
    assert b"not-a-real-secret" not in data_release.encode(exported)
    monkeypatch.setattr(data_release, "session_scope", target)
    assert data_release.load_release(path, dry_run=True) == manifest
    data_release.load_release(path)
    after = snapshots(target)
    assert after == before
    with target() as session:
        repo = AtlasRepository(session)
        assert repo.data_version()["public_entity_count"] == len(records)
        assert (
            session.execute(
                text(
                    "SELECT ST_Length(geom) FROM civilization_edges WHERE id='release-road'"
                )
            ).scalar_one()
            > 0
        )
        assert (
            session.execute(text("SELECT count(*) FROM office_tenures")).scalar_one()
            == 1
        )
        repo.update_review_status(
            "sources", "release-origin", "needs_review", "test:withdraw"
        )
    with target() as session:
        assert public_episodes(AtlasRepository(session)) == []
    assert enrichment.civilization_context("roman-empire", 117)["leaders"] == []
