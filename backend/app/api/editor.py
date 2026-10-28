"""Opt-in private browser editor. All mutations use the existing review-action service."""

from hmac import compare_digest
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from pydantic import BaseModel, ConfigDict, Field, StrictBool

from app.api.routes import _apply_review_action, _review_entity_type
from app.core.config import settings
from app.db.session import session_scope
from app.schemas import GeoJSONGeometry, ReviewActionRequest
from app.services.editor_session import (
    COOKIE,
    TTL,
    enabled,
    issue_session,
    read_session,
    require_editor,
    same_origin,
)
from app.services.repository import AtlasRepository
from app.services.review_context import (
    bulk_approval_reason,
    review_detail,
    review_version,
)

router = APIRouter(prefix="/editor", include_in_schema=False)
STATIC = Path(__file__).resolve().parents[1] / "editor_static"


class Login(BaseModel):
    model_config = ConfigDict(extra="forbid")
    key: str = Field(min_length=1, max_length=4096)
    reviewer: str = Field(min_length=1, max_length=100)


class VersionedRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")
    assignment_id: str = Field(min_length=1, max_length=200)
    expected_version: str = Field(pattern=r"^[a-f0-9]{64}$")


class Decision(VersionedRecord):
    decision_type: Literal["approve", "reject", "dispute", "request_changes"]
    rationale: str = Field(min_length=1, max_length=4000)
    confirmed: StrictBool


class BulkDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")
    records: list[VersionedRecord] = Field(min_length=1, max_length=20)
    rationale: str = Field(min_length=1, max_length=4000)
    confirmed: StrictBool


def get_target(repository, identifier, lock=False):
    assignment = repository.get(
        "review_assignments", identifier, published_only=False, for_update=lock
    )
    if not assignment:
        raise HTTPException(404, "Review assignment not found")
    kind = _review_entity_type(assignment["entity_type"])
    target = repository.get(
        kind, assignment["entity_id"], published_only=False, for_update=lock
    )
    if not target:
        raise HTTPException(404, "Review target not found")
    return assignment, target, kind


@router.get("/login")
def login_page():
    enabled()
    return FileResponse(STATIC / "login.html")


@router.post("/session")
def login(request: Request, payload: Login):
    enabled()
    same_origin(request)
    if (
        not compare_digest(payload.key.encode(), settings.editorial_api_key.encode())
        or not payload.reviewer.strip()
    ):
        raise HTTPException(401, "Invalid editorial key or reviewer label")
    token, data = issue_session(payload.reviewer.strip())
    response = JSONResponse({"reviewer": data["reviewer"], "csrf": data["csrf"]})
    response.set_cookie(
        COOKIE,
        token,
        max_age=TTL,
        httponly=True,
        samesite="strict",
        secure=request.url.scheme == "https"
        or settings.app_env in {"staging", "production"},
        path="/editor",
    )
    return response


@router.get("/api/session")
def session(data=Depends(require_editor)):
    return {
        "reviewer": data["reviewer"],
        "csrf": data["csrf"],
        "expires": data["expires"],
    }


@router.post("/logout")
def logout(data=Depends(require_editor)):
    response = JSONResponse({"signed_out": True})
    response.delete_cookie(COOKIE, path="/editor")
    return response


@router.get("/static/{asset}")
def assets(asset: str):
    enabled()
    if asset not in {"editor.css", "editor.js"}:
        raise HTTPException(404, "Not found")
    return FileResponse(STATIC / asset)


@router.get("")
@router.get("/reviews/{assignment_id}")
def editor_page(request: Request, assignment_id: str | None = None):
    try:
        read_session(request)
    except HTTPException as error:
        if error.status_code == 401:
            return RedirectResponse("/editor/login", status_code=303)
        raise
    return FileResponse(STATIC / "editor.html")


@router.get("/api/queue")
def queue(
    q: str = "",
    status: str = "needs_review",
    kind: str = "",
    confidence: str = "",
    source: str = "",
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    data=Depends(require_editor),
):
    rows = []
    with session_scope() as session:
        repo = AtlasRepository(session)
        records = {
            r["id"]: r for r in repo.list("source_records", published_only=False)
        }
        for assignment in repo.list("review_assignments", published_only=False):
            entity_kind = _review_entity_type(assignment["entity_type"])
            target = repo.get(
                entity_kind, assignment["entity_id"], published_only=False
            )
            if target is None:
                continue
            citations = (
                [target]
                if entity_kind == "source_records"
                else [
                    records[i]
                    for i in target.get("source_record_ids", [])
                    if i in records
                ]
            )
            row = {
                "assignment": assignment,
                "kind": entity_kind,
                "title": target.get("name")
                or target.get("title")
                or target.get("label")
                or target["id"],
                "confidence": target.get("confidence")
                or target.get("confidence_level")
                or "unknown",
                "source_records": citations,
                "version": review_version(assignment, target),
                "bulk_ineligible_reason": bulk_approval_reason(assignment, target),
            }
            if status and assignment["current_review_status"] != status:
                continue
            if kind and entity_kind != kind:
                continue
            if confidence and row["confidence"] != confidence:
                continue
            if source and not any(
                source.casefold() in str(r).casefold() for r in citations
            ):
                continue
            if (
                q
                and q.casefold()
                not in (str(row["title"]) + " " + assignment["entity_id"]).casefold()
            ):
                continue
            rows.append(row)
    priorities = {"high": 0, "medium": 1, "low": 2}
    rows.sort(
        key=lambda r: (
            priorities.get(r["assignment"]["priority"], 3),
            r["assignment"]["created_at"],
            r["assignment"]["id"],
        )
    )
    offset = (page - 1) * page_size
    return {
        "rows": rows[offset : offset + page_size],
        "total": len(rows),
        "page": page,
        "page_size": page_size,
        "has_more": offset + page_size < len(rows),
    }


@router.get("/api/reviews/{assignment_id}")
def detail(assignment_id: str, data=Depends(require_editor)):
    with session_scope() as session:
        repo = AtlasRepository(session)
        assignment, target, kind = get_target(repo, assignment_id)
        return review_detail(repo, assignment, target, kind)


@router.post("/api/review-actions")
def decide(payload: Decision, data=Depends(require_editor)):
    if not payload.confirmed or not payload.rationale.strip():
        raise HTTPException(400, "Confirm the review decision before saving")
    with session_scope() as session:
        repo = AtlasRepository(session)
        assignment, target, kind = get_target(repo, payload.assignment_id, lock=True)
        if payload.decision_type == "approve" and kind == "layers":
            if target.get("is_placeholder") or target.get("geometry_placeholder"):
                raise HTTPException(
                    409,
                    "Placeholder boundaries require source replacement before approval",
                )
            try:
                GeoJSONGeometry.model_validate(target.get("geometry_json"))
            except ValueError:
                raise HTTPException(
                    409, "The proposed geometry is invalid; request changes"
                )
        request = ReviewActionRequest(
            **payload.model_dump(exclude={"confirmed"}), reviewer=data["reviewer"]
        )
        return _apply_review_action(request, repo)


@router.post("/api/review-actions/bulk")
def bulk_decide(payload: BulkDecision, data=Depends(require_editor)):
    if not payload.confirmed or not payload.rationale.strip():
        raise HTTPException(400, "A rationale and explicit confirmation are required")
    identifiers = [r.assignment_id for r in payload.records]
    if len(set(identifiers)) != len(identifiers):
        raise HTTPException(400, "Select each assignment only once")
    with session_scope() as session:
        repo = AtlasRepository(session)
        for record in sorted(payload.records, key=lambda r: r.assignment_id):
            assignment, target, _ = get_target(repo, record.assignment_id, lock=True)
            reason = bulk_approval_reason(assignment, target)
            if reason or record.expected_version != review_version(assignment, target):
                raise HTTPException(
                    409, reason or "A selected record changed. Reload the queue."
                )
        # One transaction: no partial publication if any record fails validation.
        return {
            "decisions": [
                _apply_review_action(
                    ReviewActionRequest(
                        assignment_id=r.assignment_id,
                        expected_version=r.expected_version,
                        decision_type="approve",
                        reviewer=data["reviewer"],
                        rationale=payload.rationale,
                    ),
                    repo,
                )
                for r in payload.records
            ]
        }
