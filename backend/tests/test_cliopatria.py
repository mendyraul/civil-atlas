import io
import json
from pathlib import Path
import subprocess
import sys
import zipfile

from fastapi.testclient import TestClient
import pytest

from app.api import routes
from app.ingestion.cliopatria import LICENSE, CliopatriaAdapter, load_crosswalk
from app.ingestion.licenses import check_license, resolve_license
from app.ingestion.pipeline import import_bundle, prepare_import
from app.ingestion.pleiades import PleiadesAdapter
from app.main import app
from app.schemas import CivilizationLayer
from app.services.repository import AtlasRepository
from tests.test_pleiades import database  # noqa: F401  (shared PostgreSQL fixture)

FIXTURE = Path(__file__).parent / "fixtures/cliopatria/sample-117.geojson"
MANIFEST = Path(__file__).parents[1] / "data/imports/world117/v1/manifest.json"
RETRIEVED = "2026-10-22T20:46:00Z"
MAPPED = ["Q139377", "Q241790", "Q5257"]


def prepare(ids=None, year=117, version="cliopatria-test-v1", snapshot=FIXTURE):
    return prepare_import(CliopatriaAdapter(year), snapshot, ids or [], version, RETRIEVED)


def test_selects_rows_active_in_year_as_review_only_boundary_variants():
    manifest = prepare().manifest
    datasets = manifest["datasets"]
    layers = {layer["civilization_id"]: layer for layer in datasets["layers"]}
    assert set(layers) == {"aksumite-kingdom", "kingdom-of-kush", "satavahana-dynasty"}
    satavahana = layers["satavahana-dynasty"]
    assert (satavahana["valid_from_year"], satavahana["valid_to_year"]) == (106, 126)
    assert satavahana["id"] == "cliopatria-satavahana-dynasty-106ce-126ce"
    assert satavahana["variant_group"] == "satavahana-dynasty-default-reading"
    assert satavahana["interpretation_kind"] == "boundary_variant"
    assert satavahana["is_primary"] is False and satavahana["is_placeholder"] is False
    assert layers["kingdom-of-kush"]["id"] == "cliopatria-kingdom-of-kush-630bce-337ce"
    for kind, records in datasets.items():
        for record in records:
            assert record["review_status"] == "needs_review", (kind, record["id"])
    assert manifest["selected_ids"] == sorted(load_crosswalk())


def test_records_link_layer_claim_evidence_and_cc_by_source():
    datasets = prepare(["Q241790"]).manifest["datasets"]
    (source,), (record,), (claim,), (layer,), (evidence,) = (
        datasets[k] for k in ("sources", "source_records", "claims", "layers", "evidence"))
    assert source["license"] == LICENSE
    assert source["external_id"] == "cliopatria_polities_only_v021"
    assert "10.1038/s41597-025-04516-9" in source["citation"]
    assert layer["claim_ids"] == [claim["id"]] and layer["source_record_ids"] == [record["id"]]
    assert claim["subject_id"] == layer["id"] and claim["object_id"] == "kingdom-of-kush"
    assert claim["source_id"] == evidence["source_id"] == source["id"]
    assert record["feature_id"] == evidence["entity_id"] == layer["id"]
    original = next(f for f in json.loads(FIXTURE.read_bytes())["features"]
                    if f["properties"]["Wikidata"] == "Q241790")
    assert layer["geometry_json"] == original["geometry"]


def test_omissions_report_inactive_and_unmapped_polities():
    omissions = {o["id"]: o["reason"] for o in prepare().manifest["omissions"]}
    assert omissions["Q12544"] == "no Cliopatria row active in 117"
    assert "Funan: no Civil Atlas civilization mapped" in omissions["Q867782"]
    # Explicit selections do not list every unmapped polity.
    assert prepare(["Q5257"]).manifest["omissions"] == []
    assert prepare(["Q5257"], year=100).manifest["datasets"]["layers"][0]["valid_to_year"] == 105


def test_geometry_matches_seed_layer_contract():
    seed = json.loads(MANIFEST.read_bytes())["datasets"]
    civilizations = {c["id"] for c in seed["civilizations"]}
    groups = {l["variant_group"] for l in seed["layers"]}
    for entry in load_crosswalk().values():
        assert entry["civilization_id"] in civilizations
        assert entry["variant_group"] in groups
    for layer in prepare().manifest["datasets"]["layers"]:
        CivilizationLayer.model_validate(layer)


def test_release_zip_is_accepted(tmp_path):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("cliopatria.geojson", FIXTURE.read_bytes())
    snapshot = tmp_path / "cliopatria.geojson.zip"
    snapshot.write_bytes(buffer.getvalue())
    zipped = prepare(snapshot=snapshot).manifest
    plain = prepare().manifest
    assert zipped["datasets"] == plain["datasets"]
    assert zipped["raw_sha256"] != plain["raw_sha256"]


@pytest.mark.parametrize("ids,data,match", [
    (["Q1", "Q1"], None, "must not repeat"),
    (["423025"], None, "Wikidata IDs"),
    (["Q867782"], None, "no Civil Atlas civilization mapped"),
    ([], b"broken", "Cliopatria GeoJSON"),
    ([], b'{"type":"FeatureCollection","features":[]}', "release label"),
    ([], b"PK\x03\x04broken", "valid zip"),
])
def test_invalid_input_rejected(ids, data, match):
    with pytest.raises(ValueError, match=match):
        CliopatriaAdapter(117).normalize(data or FIXTURE.read_bytes(), ids, "v1", RETRIEVED)


def test_duplicate_active_rows_rejected():
    data = json.loads(FIXTURE.read_bytes())
    kush = next(f for f in data["features"] if f["properties"]["Wikidata"] == "Q241790")
    data["features"].append(kush)
    with pytest.raises(ValueError, match="more than one"):
        CliopatriaAdapter(117).normalize(json.dumps(data).encode(), [], "v1", RETRIEVED)


def test_reused_qid_cannot_attach_an_unrelated_polity():
    data = json.loads(FIXTURE.read_bytes())
    feature = next(f for f in data["features"] if f["properties"]["Wikidata"] == "Q241790")
    feature["properties"]["Name"] = "Unrelated synthetic polity"
    with pytest.raises(ValueError, match="source identity mismatch"):
        CliopatriaAdapter(117).normalize(json.dumps(data).encode(), ["Q241790"], "v1", RETRIEVED)


def test_explicit_legacy_crosswalk_without_source_name_remains_supported():
    crosswalk = {"Q241790": {"civilization_id": "kingdom-of-kush", "variant_group": "legacy-group"}}
    result = CliopatriaAdapter(117, crosswalk).normalize(FIXTURE.read_bytes(), ["Q241790"], "v1", RETRIEVED)
    assert result.datasets["layers"][0]["variant_group"] == "legacy-group"


@pytest.mark.parametrize("name", ["", " ", None, 12])
def test_invalid_expected_source_name_rejected(tmp_path, name):
    path = tmp_path / "crosswalk.json"
    path.write_text(json.dumps({"polities": [{"wikidata": "Q1", "civilization_id": "x", "variant_group": "x", "cliopatria_name": name}]}))
    with pytest.raises(ValueError, match="nonempty source name"):
        load_crosswalk(path)


def test_license_gate_accepts_open_and_refuses_non_commercial(tmp_path):
    assert resolve_license("CC-BY-4.0") == resolve_license("http://creativecommons.org/licenses/by/4.0/legalcode")
    assert check_license(PleiadesAdapter()).spdx == "CC-BY-3.0"
    assert check_license(CliopatriaAdapter(117)).spdx == "CC-BY-4.0"
    for refused in ("CC-BY-NC-SA-4.0", "https://creativecommons.org/licenses/by-sa/3.0/", "GPL-3.0", "unknown_seed"):
        with pytest.raises(ValueError, match="not cleared"):
            resolve_license(refused)

    class NonCommercial(CliopatriaAdapter):
        license = "https://creativecommons.org/licenses/by-nc-sa/4.0/"

    with pytest.raises(ValueError, match="not cleared"):
        prepare_import(NonCommercial(117), FIXTURE, [], "v1", RETRIEVED)


def test_cli_dry_run(tmp_path):
    command = [sys.executable, "-m", "app.ingestion.cli", "--source", "cliopatria",
               "--snapshot", str(FIXTURE), "--year", "117", "--dataset-version", "fixture-v1",
               "--retrieved-at", RETRIEVED, "--actor", "test:cli",
               "--artifact-dir", str(tmp_path / "archive"), "--dry-run"]
    result = subprocess.run(command, cwd=Path(__file__).parents[1], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    summary = json.loads(result.stdout)
    assert summary["status"] == "validated" and summary["counts"]["layers"] == 3
    assert not (tmp_path / "archive").exists()
    missing_year = [arg for arg in command if arg not in ("--year", "117")]
    result = subprocess.run(missing_year, cwd=Path(__file__).parents[1], capture_output=True, text=True)
    assert result.returncode == 2 and "--year is required" in result.stderr


def test_import_stays_private_until_layer_approved(database, tmp_path, monkeypatch):  # noqa: F811
    monkeypatch.setattr(routes.settings, "editorial_api_key", "cliopatria-test-key")
    client = TestClient(app)
    headers = {"X-Editorial-Key": "cliopatria-test-key"}
    layer_id = "cliopatria-kingdom-of-kush-630bce-337ce"

    def public_layer_ids():
        spatial = client.get("/api/v1/spatial/layers", params={"year": 117}).json()["features"]
        listed = client.get("/api/v1/civilization-layers").json()
        return {f["id"] for f in spatial}, {layer["id"] for layer in listed}

    with database() as session:
        if not AtlasRepository(session).get("civilizations", "kingdom-of-kush", published_only=False):
            pytest.skip("world117 seed not imported")
    assert import_bundle(prepare(["Q241790"]), tmp_path / "archive", "test:cliopatria")["status"] == "completed"
    assert all(layer_id not in ids for ids in public_layer_ids())
    queue = client.get("/api/v1/review-assignments", headers=headers).json()
    assert any(a["id"] == f"review-layers-{layer_id}" for a in queue)

    action = {"assignment_id": f"review-layers-{layer_id}", "decision_type": "approve",
              "reviewer": "test:reviewer", "rationale": "Fixture approved for integration test."}
    assert client.post("/api/v1/review-actions", headers=headers, json=action).status_code == 200
    assert all(layer_id in ids for ids in public_layer_ids())


def test_import_refuses_layers_for_unknown_civilizations(database, tmp_path):  # noqa: F811
    crosswalk = {"Q241790": {"civilization_id": "not-a-civilization", "variant_group": "x"}}
    bundle = prepare_import(CliopatriaAdapter(117, crosswalk), FIXTURE, [], "cliopatria-test-bad", RETRIEVED)
    with pytest.raises(ValueError, match="unknown civilization"):
        import_bundle(bundle, tmp_path / "archive", "test:cliopatria")
    with database() as session:
        assert AtlasRepository(session).get("import_jobs", bundle.job_id, published_only=False) is None
