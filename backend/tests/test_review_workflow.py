import pytest
from sqlalchemy import text

from app.api.routes import _apply_review_action
from app.db.session import engine, session_scope
from app.schemas import ReviewActionRequest
from app.services.repository import AtlasRepository


def test_editorial_review_action_is_auditable_and_reversible():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception as error:
        pytest.skip(f"PostgreSQL is not available: {error}")

    assignment_id = "review-assignment-layer-roman-empire-core"
    entity_id = "layer-roman-empire-core"
    with session_scope() as session:
        assignment = AtlasRepository(session).get(
            "review_assignments", assignment_id, published_only=False
        )
        target = AtlasRepository(session).get("layers", entity_id, published_only=False)
    if not assignment or not target:
        pytest.skip("The versioned fixture has not been imported")

    original_status = assignment["current_review_status"]
    decision = _apply_review_action(
        ReviewActionRequest(
            assignment_id=assignment_id,
            decision_type="approve",
            reviewer="test:editorial",
            rationale="Integration test approval.",
        )
    )
    assert decision.previous_review_status == original_status
    assert decision.new_review_status == "reviewed"
    published = _apply_review_action(
        ReviewActionRequest(
            assignment_id=assignment_id,
            decision_type="publish",
            reviewer="test:publisher",
            rationale="Integration test publication.",
        )
    )
    assert published.previous_review_status == "reviewed"
    assert published.new_review_status == "reviewed"
    changes_requested = _apply_review_action(
        ReviewActionRequest(
            assignment_id=assignment_id,
            decision_type="request_changes",
            reviewer="test:editorial",
            rationale="Integration test change request.",
        )
    )
    assert changes_requested.new_review_status == "needs_review"
    rejected = _apply_review_action(
        ReviewActionRequest(
            assignment_id=assignment_id,
            decision_type="reject",
            reviewer="test:editorial",
            rationale="Integration test rejection.",
        )
    )
    assert rejected.new_review_status == "rejected"

    with session_scope() as session:
        repository = AtlasRepository(session)
        reviewed = repository.get("layers", entity_id, published_only=False)
        updated_assignment = repository.get(
            "review_assignments", assignment_id, published_only=False
        )
        revision_count = session.execute(
            text("SELECT count(*) FROM revision_records WHERE entity_id=:id"),
            {"id": f"entity:layers:{entity_id}"},
        ).scalar_one()
        assert reviewed and reviewed["review_status"] == "reviewed"
        assert updated_assignment and updated_assignment["current_review_status"] == "reviewed"
        assert revision_count > 0

        # Keep the shared CI database deterministic for any later checks.
        repository.update_review_status("layers", entity_id, original_status, "test:cleanup")
        updated_assignment["current_review_status"] = original_status
        updated_assignment["target_review_status"] = assignment["target_review_status"]
        updated_assignment["notes"] = assignment["notes"]
        repository.upsert(
            "review_assignments", assignment_id, updated_assignment, "test:cleanup",
            published=False,
        )
