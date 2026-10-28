"""Private review context shared by the editor and review-action concurrency checks."""

from hashlib import sha256
import json


def review_version(assignment, target):
    return sha256(
        json.dumps(
            [assignment, target], sort_keys=True, separators=(",", ":"), default=str
        ).encode()
    ).hexdigest()


def bulk_approval_reason(assignment, target):
    """Metadata-only batches: no geography or low-confidence historical claims."""
    if assignment.get("entity_type") not in ("source_record", "source_records"):
        return "Geometry and historical entities require individual review."
    if assignment.get("priority") != "low" or target.get("confidence") != "high":
        return "Bulk review requires low priority and high confidence."
    if (
        assignment.get("current_review_status") != "needs_review"
        or target.get("review_status") != "needs_review"
    ):
        return "Only records awaiting review are eligible."
    if target.get("import_review_blocked"):
        return "The source no longer supports this record."
    if not str(target.get("citation") or "").strip():
        return "A citation is required."
    return None


def source_records_for(repository, kind, target):
    identifiers = set(target.get("source_record_ids") or [])
    if kind == "source_records":
        return [target]
    return [
        record
        for record in repository.list("source_records", published_only=False)
        if record["id"] in identifiers
    ]


def review_detail(repository, assignment, target, kind):
    records = source_records_for(repository, kind, target)
    ids = {target["id"], *(r["id"] for r in records)}
    evidence = [
        e
        for e in repository.list("evidence", published_only=False)
        if e.get("entity_id") in ids
    ]
    source_ids = {e.get("source_id") for e in evidence}
    sources = [
        s
        for s in repository.list("sources", published_only=False)
        if s["id"] in source_ids
    ]
    primaries = []
    if kind == "layers":
        for layer in repository.list("layers"):
            if layer["id"] == target["id"] or not layer.get("is_primary"):
                continue
            if layer.get("civilization_id") != target.get(
                "civilization_id"
            ) or layer.get("layer_type") != target.get("layer_type"):
                continue
            if (
                layer["valid_from_year"] <= target["valid_to_year"]
                and layer["valid_to_year"] >= target["valid_from_year"]
            ):
                primaries.append(layer)
    history = [
        d
        for d in repository.list("review_decisions", published_only=False)
        if d.get("assignment_id") == assignment["id"]
    ]
    return {
        "assignment": assignment,
        "target": target,
        "kind": kind,
        "version": review_version(assignment, target),
        "source_records": records,
        "sources": sources,
        "evidence": evidence,
        "primary_layers": sorted(primaries, key=lambda p: p["id"]),
        "primary_source_records": {
            p["id"]: source_records_for(repository, "layers", p) for p in primaries
        },
        "history": sorted(history, key=lambda d: d.get("created_at", "")),
        "bulk_ineligible_reason": bulk_approval_reason(assignment, target),
    }
