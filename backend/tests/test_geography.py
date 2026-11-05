import json
import pytest
from app.ingestion.geography import AWMCAdapter, ItinereAdapter


def mapping(license="ODbL-1.0", **features):
    return {
        "license": license,
        "citation": "Synthetic fixture citation",
        "source_url": "https://example.org/release",
        "features": features,
    }


def raw(shape="LineString"):
    return json.dumps(
        {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "id": "1",
                    "properties": {"name": "Synthetic line"},
                    "geometry": {"type": shape, "coordinates": [[0, 0], [1, 1]]},
                }
            ],
        }
    ).encode()


def test_undated_physical_features_remain_explicitly_undated():
    result = AWMCAdapter(mapping()).normalize(raw(), [], "v1", "2026-11-05T15:00:00Z")
    feature = result.datasets["physical_features"][0]
    assert feature["start_year"] is feature["end_year"] is None
    assert feature["geometry"]["coordinates"] == [[0, 0], [1, 1]]
    assert feature["review_status"] == "needs_review"
    assert result.datasets["sources"][0]["mapping"] == mapping()


def test_roads_require_dated_endpoint_mapping_and_retain_source_on_omission():
    result = ItinereAdapter(mapping("CC-BY-4.0")).normalize(
        raw(), [], "v1", "2026-11-05T15:00:00Z"
    )
    assert not result.datasets["routes"] and len(result.datasets["source_records"]) == 1
    assert "dates" in result.omissions[0]["reason"]
    linked = mapping(
        "CC-BY-4.0",
        **{
            "1": {
                "start_year": 100,
                "end_year": 200,
                "date_citation": "Synthetic date evidence",
                "source_node_id": "rome",
                "target_node_id": "ostia",
                "civilization_ids": ["roman-empire"],
            }
        },
    )
    result = ItinereAdapter(linked).normalize(raw(), [], "v1", "2026-11-05T15:00:00Z")
    route = result.datasets["routes"][0]
    assert route["path"] == [[0, 0], [1, 1]]
    assert route["source_node_id"] == "rome" and route["date_citation"]
    assert "estimated_travel_days_min" not in route


def test_uncleared_release_is_rejected():
    with pytest.raises(ValueError, match="license"):
        AWMCAdapter(mapping("CC-BY-NC-4.0"))


def test_physical_import_publication_and_replay(database, tmp_path):
    from app.ingestion.pipeline import prepare_import, import_bundle
    from app.services.repository import AtlasRepository
    from app.services.atlas import get_world

    path = tmp_path / "awmc.json"
    path.write_bytes(raw())
    bundle = prepare_import(
        AWMCAdapter(mapping()), path, [], "awmc-test-v1", "2026-11-05T15:00:00Z"
    )
    import_bundle(bundle, tmp_path / "archive", "test:awmc")
    assert get_world(117).physical_features == []
    with database() as session:
        AtlasRepository(session).update_review_status(
            "physical_features", "awmc-1", "reviewed", "test:review"
        )
    assert get_world(117).physical_features[0].id == "awmc-1"
    assert (
        import_bundle(bundle, tmp_path / "archive", "test:awmc")["status"]
        == "duplicate"
    )
    assert get_world(117).physical_features[0].start_year is None


from tests.test_pleiades import database  # noqa: E402,F401


def test_road_import_projects_source_path_and_rejects_unknown_endpoints(
    database, tmp_path
):
    from app.ingestion.pipeline import prepare_import, import_bundle
    from sqlalchemy import text

    path = tmp_path / "roads.json"
    path.write_bytes(raw())
    linked = mapping(
        "CC-BY-4.0",
        **{
            "1": {
                "start_year": 100,
                "end_year": 200,
                "date_citation": "Synthetic test evidence",
                "source_node_id": "roma",
                "target_node_id": "alexandria",
                "civilization_ids": ["roman-empire"],
            }
        },
    )
    bundle = prepare_import(
        ItinereAdapter(linked), path, [], "road-test-v1", "2026-11-05T15:00:00Z"
    )
    import_bundle(bundle, tmp_path / "archive", "test:roads")
    with database() as session:
        assert json.loads(
            session.execute(
                text(
                    "SELECT ST_AsGeoJSON(geom) FROM civilization_edges WHERE id='itinere-1'"
                )
            ).scalar_one()
        )["coordinates"] == [[0, 0], [1, 1]]
    linked["features"]["1"]["target_node_id"] = "unknown-node"
    changed = prepare_import(
        ItinereAdapter(linked), path, [], "road-test-v2", "2026-11-05T15:00:00Z"
    )
    with pytest.raises(ValueError, match="unknown node"):
        import_bundle(changed, tmp_path / "archive", "test:roads")


def test_itinere_static_release_projection_elevation_and_identifiers():
    from pathlib import Path

    snapshot = Path(__file__).parent / "fixtures/itinere/roads-v1.3.geojson"
    mapping_data = mapping(
        "CC-BY-4.0",
        **{
            "1874": {
                "source_node_id": "fixture-start",
                "target_node_id": "fixture-end",
                "start_year": 50,
                "end_year": 250,
                "date_citation": "Source Lower_Date/Upper_Date estimates; uncertainties retained in source properties.",
            }
        },
    )
    normalized = ItinereAdapter(mapping_data).normalize(
        snapshot.read_bytes(), [], "actual-v1.3", "2026-11-05T21:42:00Z"
    )
    assert len(normalized.datasets["routes"]) == 1
    route = normalized.datasets["routes"][0]
    assert route["id"] == "itinere-1874"
    assert route["label"] == "Kaine-Mons Porphyrites"
    assert route["path"][0] == pytest.approx(
        [33.34423352666381, 27.21022157378383], abs=1e-10
    )
    source = next(
        f
        for f in json.loads(snapshot.read_bytes())["features"]
        if f["properties"]["InLine_FID"] == 1874
    )
    assert len(route["path"]) == len(source["geometry"]["coordinates"][0])
    assert route["source_properties"] == source["properties"]
    assert source["geometry"]["coordinates"][0][0][2] == 396.32950574152346
    record = next(
        r
        for r in normalized.datasets["source_records"]
        if r["feature_id"] == route["id"]
    )
    assert "EPSG:3395" in record["notes"] and "elevation" in record["notes"]
    assert "0" in {o["id"] for o in normalized.omissions}


def test_awmc_actual_crs84_geometry_and_source_fields_are_preserved():
    from pathlib import Path

    snapshot = Path(__file__).parent / "fixtures/awmc/shoreline.geojson"
    original = json.loads(snapshot.read_bytes())
    normalized = AWMCAdapter(mapping()).normalize(
        snapshot.read_bytes(), [], "actual-shoreline", "2026-11-05T21:42:00Z"
    )
    assert normalized.omissions == []
    assert [r["id"] for r in normalized.datasets["physical_features"]] == [
        "awmc-1",
        "awmc-2",
    ]
    for feature, record in zip(
        original["features"], normalized.datasets["physical_features"]
    ):
        assert record["geometry"] == feature["geometry"]
        assert record["source_properties"] == feature["properties"]
        assert record["start_year"] is record["end_year"] is None


def test_projected_geometry_requires_explicit_supported_crs():
    data = json.loads(raw())
    data["crs"] = {"type": "name", "properties": {"name": "EPSG:99999"}}
    with pytest.raises(ValueError, match="unsupported source CRS"):
        AWMCAdapter(mapping()).normalize(
            json.dumps(data).encode(), [], "v1", "2026-11-05T15:00:00Z"
        )
