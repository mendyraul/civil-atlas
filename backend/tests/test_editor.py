from copy import deepcopy
import json
from pathlib import Path

from fastapi.testclient import TestClient
import pytest

from app.api import editor
from app.core.config import settings
from app.main import app
from app.schemas import ReviewActionRequest
from app.seed import catalog
from app.services.editor_session import COOKIE
from app.services.repository import AtlasRepository
from tests.test_pleiades import database  # noqa: F401

SECRET = "synthetic-editor-test-key"
ORIGIN = {"origin": "http://testserver"}


@pytest.fixture
def editorial(database, monkeypatch):  # noqa: F811
    monkeypatch.setattr(settings, "editor_ui_enabled", True)
    monkeypatch.setattr(settings, "editorial_api_key", SECRET)
    monkeypatch.setattr(editor, "session_scope", database)
    fixture = json.loads(
        (
            Path(__file__).parents[2]
            / "frontend/acceptance/fixtures/boundary-readings.json"
        ).read_text()
    )
    primary = deepcopy(fixture["world"]["layers"][0])
    primary.update(
        id="editor-primary",
        name="Editor primary boundary",
        review_status="reviewed",
        source_record_ids=[],
    )
    proposed = deepcopy(primary)
    proposed.update(
        id="editor-proposed",
        name="Editor proposed boundary",
        is_primary=False,
        review_status="needs_review",
        source_record_ids=["editor-citation-a"],
    )
    assignments = {}
    with database() as session:
        repo = AtlasRepository(session)
        for layer, published in ((primary, True), (proposed, False)):
            repo.upsert(
                "layers", layer["id"], layer, "test:fixture", published=published
            )
            repo.upsert_spatial_projection("layers", layer)
        records = []
        for suffix in ("a", "b", "low"):
            source = deepcopy(catalog.SOURCE_RECORDS[0].model_dump(mode="json"))
            source.update(
                id=f"editor-citation-{suffix}",
                title=f"Editor citation {suffix}",
                feature_id="editor-proposed",
                citation="Synthetic integration evidence; not historical data.",
                confidence="low" if suffix == "low" else "high",
                review_status="needs_review",
                link="javascript:alert(1)",
            )
            records.append(source)
            repo.upsert("source_records", source["id"], source, "test:fixture")
        for kind, target in [
            ("layers", proposed),
            *[("source_records", r) for r in records],
        ]:
            assignment = deepcopy(catalog.REVIEW_ASSIGNMENTS[0].model_dump(mode="json"))
            assignment.update(
                id=f"assignment-{target['id']}",
                entity_type=kind,
                entity_id=target["id"],
                current_review_status="needs_review",
                target_review_status="reviewed",
                priority="low",
                notes="Synthetic review fixture",
            )
            repo.upsert(
                "review_assignments", assignment["id"], assignment, "test:fixture"
            )
            assignments[target["id"]] = assignment["id"]
    return database, assignments


def login(client):
    response = client.post(
        "/editor/session",
        json={"key": SECRET, "reviewer": "test:reviewer"},
        headers=ORIGIN,
    )
    assert response.status_code == 200, response.text
    return {**ORIGIN, "x-csrf-token": response.json()["csrf"]}


def context(client, assignment):
    response = client.get(f"/editor/api/reviews/{assignment}")
    assert response.status_code == 200, response.text
    return response.json()


def decide(client, headers, record, decision="approve", **extra):
    return client.post(
        "/editor/api/review-actions",
        headers=headers,
        json={
            "assignment_id": record["assignment"]["id"],
            "expected_version": record["version"],
            "decision_type": decision,
            "rationale": "Verified the synthetic record and citation.",
            "confirmed": True,
            **extra,
        },
    )


def test_editor_is_opt_in_and_never_bypasses_key_in_development(monkeypatch):
    client = TestClient(app)
    monkeypatch.setattr(settings, "editor_ui_enabled", False)
    assert client.get("/editor", follow_redirects=False).status_code == 404
    assert client.get("/editor/login").status_code == 404
    monkeypatch.setattr(settings, "editor_ui_enabled", True)
    monkeypatch.setattr(settings, "editorial_api_key", None)
    assert client.get("/editor").status_code == 503


def test_private_pages_and_metadata_require_session(editorial):
    client = TestClient(app)
    assert client.get("/editor", follow_redirects=False).status_code == 303
    for path in (
        "/editor/api/queue",
        "/editor/api/reviews/assignment-editor-proposed",
        "/editor/api/session",
    ):
        response = client.get(path)
        assert response.status_code == 401
        assert "Editor proposed boundary" not in response.text
        assert response.headers["cache-control"] == "no-store"
    assert client.get("/api/v1/review-assignments").status_code == 401


def test_login_cookie_csrf_expiry_rotation_and_logout(editorial, monkeypatch):
    client = TestClient(app)
    assert (
        client.post(
            "/editor/session", headers=ORIGIN, json={"key": "bad", "reviewer": "test"}
        ).status_code
        == 401
    )
    assert (
        client.post(
            "/editor/session", json={"key": SECRET, "reviewer": "test"}
        ).status_code
        == 403
    )
    headers = login(client)
    assert SECRET not in client.cookies.get(COOKIE)
    assert client.get("/editor/api/session").json()["reviewer"] == "test:reviewer"
    assert (
        client.get("/api/v1/review-assignments").status_code == 401
    )  # editorial cookie is scoped to /editor
    response = client.get("/editor")
    assert "frame-ancestors 'none'" in response.headers["content-security-policy"]
    assert SECRET not in response.text
    assert (
        client.post(
            "/editor/logout",
            headers={**headers, "origin": "https://evil.example"},
            json={},
        ).status_code
        == 403
    )
    assert client.post("/editor/logout", headers=ORIGIN, json={}).status_code == 403
    assert client.post("/editor/logout", headers=headers, json={}).status_code == 200
    assert client.get("/editor/api/queue").status_code == 401
    login(client)
    monkeypatch.setattr(settings, "editorial_api_key", "rotated-test-key")
    assert client.get("/editor/api/queue").status_code == 401


def test_queue_filters_confidence_sources_and_pagination(editorial):
    client = TestClient(app)
    login(client)
    queue = client.get(
        "/editor/api/queue",
        params={
            "q": "Editor",
            "kind": "source_records",
            "confidence": "high",
            "source": "Synthetic",
            "page_size": 1,
        },
    ).json()
    assert queue["total"] == 2 and queue["has_more"]
    assert queue["rows"][0]["bulk_ineligible_reason"] is None
    page2 = client.get(
        "/editor/api/queue?q=Editor&kind=source_records&confidence=high&page_size=1&page=2"
    ).json()
    assert page2["rows"][0]["assignment"]["id"] != queue["rows"][0]["assignment"]["id"]
    assert client.get("/editor/api/queue?page=0").status_code == 422


def test_detail_citations_and_published_primary_are_private(editorial):
    _, assignments = editorial
    client = TestClient(app)
    login(client)
    record = context(client, assignments["editor-proposed"])
    assert record["target"]["id"] == "editor-proposed"
    assert record["source_records"][0]["id"] == "editor-citation-a"
    assert any(layer["id"] == "editor-primary" for layer in record["primary_layers"])
    assert all(layer["id"] != "editor-proposed" for layer in record["primary_layers"])
    assert record["bulk_ineligible_reason"]
    assert "editor-proposed" not in client.get("/api/v1/world/117").text


def test_decisions_publish_audit_dispute_and_reject(editorial):
    _, assignments = editorial
    client = TestClient(app)
    headers = login(client)
    record = context(client, assignments["editor-proposed"])
    assert decide(client, headers, record, confirmed=False).status_code == 400
    assert decide(client, headers, record, rationale="   ").status_code == 400
    approved = decide(client, headers, record)
    assert approved.status_code == 200, approved.text
    assert approved.json()["reviewer"] == "test:reviewer"
    assert "editor-proposed" in client.get("/api/v1/world/117").text
    assert (
        decide(client, headers, record).status_code == 409
    )  # cannot replay stale decisions
    record = context(client, assignments["editor-proposed"])
    disputed = decide(client, headers, record, "dispute")
    assert (
        disputed.status_code == 200
        and disputed.json()["new_review_status"] == "disputed"
    )
    assert "editor-proposed" not in client.get("/api/v1/world/117").text
    record = context(client, assignments["editor-proposed"])
    assert decide(client, headers, record, "reject").status_code == 200
    history = context(client, assignments["editor-proposed"])["history"]
    assert [d["decision_type"] for d in history] == ["approve", "dispute", "reject"]


def test_canonical_api_supports_dispute_and_version_checks(editorial):
    _, assignments = editorial
    client = TestClient(app)
    login(client)
    record = context(client, assignments["editor-proposed"])
    payload = {
        "assignment_id": record["assignment"]["id"],
        "expected_version": record["version"],
        "decision_type": "dispute",
        "rationale": "Conflicting source dates.",
        "reviewer": "test:api",
    }
    response = client.post(
        "/api/v1/review-actions", headers={"X-Editorial-Key": SECRET}, json=payload
    )
    assert (
        response.status_code == 200
        and response.json()["new_review_status"] == "disputed"
    )
    assert (
        client.post(
            "/api/v1/review-actions", headers={"X-Editorial-Key": SECRET}, json=payload
        ).status_code
        == 409
    )
    with pytest.raises(ValueError):
        ReviewActionRequest(**{**payload, "rationale": "   "})


def test_bulk_is_atomic_confirmed_and_metadata_only(editorial):
    _, assignments = editorial
    client = TestClient(app)
    headers = login(client)
    records = [
        context(client, assignments[name])
        for name in ("editor-citation-a", "editor-citation-low")
    ]

    def payload(records):
        return {
            "records": [
                {
                    "assignment_id": r["assignment"]["id"],
                    "expected_version": r["version"],
                }
                for r in records
            ],
            "rationale": "Checked each citation against the synthetic evidence.",
            "confirmed": True,
        }

    response = client.post(
        "/editor/api/review-actions/bulk", headers=headers, json=payload(records)
    )
    assert response.status_code == 409
    assert (
        context(client, assignments["editor-citation-a"])["target"]["review_status"]
        == "needs_review"
    )
    geometry = context(client, assignments["editor-proposed"])
    assert (
        client.post(
            "/editor/api/review-actions/bulk", headers=headers, json=payload([geometry])
        ).status_code
        == 409
    )
    records = [
        context(client, assignments[name])
        for name in ("editor-citation-a", "editor-citation-b")
    ]
    invalid = {**payload(records), "confirmed": False}
    assert (
        client.post(
            "/editor/api/review-actions/bulk", headers=headers, json=invalid
        ).status_code
        == 400
    )
    assert (
        client.post(
            "/editor/api/review-actions/bulk",
            headers=headers,
            json=payload([records[0], records[0]]),
        ).status_code
        == 400
    )
    response = client.post(
        "/editor/api/review-actions/bulk", headers=headers, json=payload(records)
    )
    assert response.status_code == 200, response.text
    assert len(response.json()["decisions"]) == 2
    assert (
        client.post(
            "/editor/api/review-actions/bulk", headers=headers, json=payload(records)
        ).status_code
        == 409
    )


def test_blocked_source_and_placeholder_cannot_be_approved(editorial):
    scope, assignments = editorial
    with scope() as session:
        repo = AtlasRepository(session)
        target = repo.get("source_records", "editor-citation-a", published_only=False)
        target["import_review_blocked"] = "Source withdrew the record"
        repo.upsert("source_records", target["id"], target, "test:blocked")
        layer = repo.get("layers", "editor-proposed", published_only=False)
        layer["is_placeholder"] = True
        repo.upsert("layers", layer["id"], layer, "test:placeholder")
    client = TestClient(app)
    headers = login(client)
    for name in ("editor-citation-a", "editor-proposed"):
        record = context(client, assignments[name])
        assert decide(client, headers, record).status_code == 409
        assert record["target"]["review_status"] == "needs_review"


def test_strict_fields_prevent_actor_spoofing_and_missing_revision(editorial):
    _, assignments = editorial
    client = TestClient(app)
    headers = login(client)
    record = context(client, assignments["editor-proposed"])
    assert decide(client, headers, record, reviewer="spoofed").status_code == 422
    assert decide(client, headers, record, expected_version="").status_code == 422
    assert decide(client, headers, record, confirmed="true").status_code == 422


def test_expired_session_cannot_read_private_records(editorial, monkeypatch):
    from types import SimpleNamespace
    from app.services import editor_session

    client = TestClient(app)
    login(client)
    future = editor_session.time.time() + editor_session.TTL + 1
    monkeypatch.setattr(editor_session, "time", SimpleNamespace(time=lambda: future))
    assert client.get("/editor/api/queue").status_code == 401


def test_bulk_failure_after_first_decision_rolls_back_publication(
    editorial, monkeypatch
):
    from fastapi import HTTPException

    _, assignments = editorial
    client = TestClient(app)
    headers = login(client)
    records = [
        context(client, assignments[name])
        for name in ("editor-citation-a", "editor-citation-b")
    ]
    original = editor._apply_review_action
    calls = []

    def fail_second(payload, repo):
        calls.append(payload.assignment_id)
        if len(calls) == 2:
            raise HTTPException(409, "Controlled second-record conflict")
        return original(payload, repo)

    monkeypatch.setattr(editor, "_apply_review_action", fail_second)
    response = client.post(
        "/editor/api/review-actions/bulk",
        headers=headers,
        json={
            "records": [
                {
                    "assignment_id": r["assignment"]["id"],
                    "expected_version": r["version"],
                }
                for r in records
            ],
            "confirmed": True,
            "rationale": "Verify rollback of all selected records.",
        },
    )
    assert response.status_code == 409
    first = context(client, assignments["editor-citation-a"])
    assert first["target"]["review_status"] == "needs_review"
    assert first["history"] == []


def test_public_frontend_cors_does_not_authorize_editor_reads(editorial):
    client = TestClient(app)
    login(client)
    for path in (
        "/editor/api/session",
        "/editor/api/queue",
        "/editor/api/reviews/assignment-editor-proposed",
    ):
        response = client.get(path, headers={"origin": "http://localhost:3000"})
        assert response.status_code == 403
        assert "Editor proposed boundary" not in response.text
        assert SECRET not in response.text
    assert client.get("/editor/api/queue", headers=ORIGIN).status_code == 200
