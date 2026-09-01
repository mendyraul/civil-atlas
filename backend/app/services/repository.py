from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

PUBLIC_ENTITY_TYPES = {
    "civilizations",
    "layers",
    "nodes",
    "routes",
    "places",
    "civilization_places",
    "edges",
    "sources",
    "source_records",
    "eras",
    "events",
    "relationships",
    "claims",
    "evidence",
    "knowledge_entities",
    "knowledge_claims",
    "knowledge_relationships",
}


class AtlasRepository:
    """Database-backed repository for validated, externally identified atlas documents."""

    def __init__(self, session: Session):
        self.session = session

    def list(self, entity_type: str, *, published_only: bool = True) -> list[dict[str, Any]]:
        rows = self.session.execute(
            text("""
                SELECT payload FROM atlas_entities
                WHERE entity_type=:type AND (:published_only = FALSE OR published = TRUE)
                ORDER BY external_id
            """),
            {"type": entity_type, "published_only": published_only},
        )
        return [dict(row.payload) for row in rows]

    def get(
        self, entity_type: str, external_id: str, *, published_only: bool = True
    ) -> dict[str, Any] | None:
        row = self.session.execute(
            text("""
                SELECT payload FROM atlas_entities
                WHERE entity_type=:type AND external_id=:id
                  AND (:published_only = FALSE OR published = TRUE)
            """),
            {"type": entity_type, "id": external_id, "published_only": published_only},
        ).first()
        return dict(row.payload) if row else None

    def search(self, entity_types: tuple[str, ...]) -> list[dict[str, Any]]:
        """Return public documents for the catalog search endpoint."""
        if not entity_types:
            return []
        rows = self.session.execute(
            text("""
                SELECT entity_type, payload FROM atlas_entities
                WHERE entity_type = ANY(:entity_types) AND published = TRUE
                ORDER BY external_id
            """),
            {"entity_types": list(entity_types)},
        )
        return [{"entity_type": row.entity_type, **dict(row.payload)} for row in rows]

    def data_version(self) -> dict[str, Any]:
        row = self.session.execute(text("""
            SELECT count(*) AS entity_count,
                   count(*) FILTER (WHERE published = TRUE) AS public_entity_count,
                   max(updated_at) AS updated_at,
                   coalesce(max(revision_number), 0) AS revision
            FROM atlas_entities
        """)).one()
        return {
            "version": f"db-r{row.revision}",
            "revision": row.revision,
            "entity_count": row.entity_count,
            "public_entity_count": row.public_entity_count,
            "updated_at": row.updated_at,
        }

    def upsert(
        self,
        entity_type: str,
        external_id: str,
        payload: dict[str, Any],
        actor: str,
        *,
        published: bool = False,
    ) -> str:
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
        digest = sha256(canonical.encode()).hexdigest()
        existing = self.session.execute(text("""
            SELECT id, content_hash, published, revision_number FROM atlas_entities
            WHERE entity_type=:type AND external_id=:external_id FOR UPDATE
        """), {"type": entity_type, "external_id": external_id}).mappings().first()
        now = datetime.now(timezone.utc)
        if existing and existing["content_hash"] == digest and existing["published"] == published:
            return "duplicate"
        if existing:
            revision = existing["revision_number"] + 1
            self.session.execute(text("""
                UPDATE atlas_entities SET payload=CAST(:payload AS jsonb), content_hash=:hash,
                  published=:published, revision_number=:revision, updated_at=:now WHERE id=:id
            """), {"payload": json.dumps(payload), "hash": digest, "revision": revision,
                    "published": published, "now": now, "id": existing["id"]})
            self.session.execute(text("""
                INSERT INTO revision_records
                  (id, external_id, entity_type, entity_id, revision_kind, summary,
                   diff_excerpt, actor, created_at)
                VALUES (:id, :id, :type, :entity_id, 'import_update', :summary,
                        :excerpt, :actor, :now)
            """), {"id": f"revision:{entity_type}:{external_id}:{revision}", "type": entity_type,
                    "entity_id": existing["id"], "summary": f"Updated {external_id} from import",
                    "excerpt": canonical[:1000], "actor": actor, "now": now})
            return "updated"
        internal_id = f"entity:{entity_type}:{external_id}"
        self.session.execute(text("""
            INSERT INTO atlas_entities
              (id, entity_type, external_id, payload, content_hash, published,
               revision_number, created_at, updated_at)
            VALUES (:id, :type, :external_id, CAST(:payload AS jsonb), :hash, :published,
                    1, :now, :now)
        """), {"id": internal_id, "type": entity_type, "external_id": external_id,
                "payload": json.dumps(payload), "hash": digest, "published": published, "now": now})
        return "created"

    def update_review_status(
        self,
        entity_type: str,
        external_id: str,
        review_status: str,
        actor: str,
    ) -> dict[str, Any]:
        """Update a public entity status while retaining its import lineage."""
        row = self.session.execute(text("""
            SELECT id, payload, published, revision_number
            FROM atlas_entities
            WHERE entity_type=:type AND external_id=:external_id
            FOR UPDATE
        """), {"type": entity_type, "external_id": external_id}).mappings().first()
        if not row:
            raise KeyError(f"{entity_type}/{external_id} was not found")

        payload = dict(row["payload"])
        previous_status = payload.get("review_status")
        payload["review_status"] = review_status
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
        digest = sha256(canonical.encode()).hexdigest()
        revision = row["revision_number"] + 1
        published = review_status in {"reviewed", "seeded"} and entity_type in PUBLIC_ENTITY_TYPES
        now = datetime.now(timezone.utc)
        self.session.execute(text("""
            UPDATE atlas_entities
            SET payload=CAST(:payload AS jsonb), content_hash=:hash,
                published=:published, revision_number=:revision, updated_at=:now
            WHERE id=:id
        """), {"payload": json.dumps(payload), "hash": digest, "published": published,
                "revision": revision, "now": now, "id": row["id"]})
        self.session.execute(text("""
            INSERT INTO revision_records
              (id, external_id, entity_type, entity_id, revision_kind, summary,
               diff_excerpt, actor, created_at)
            VALUES (:id, :id, :type, :entity_id, 'review_status', :summary,
                    :excerpt, :actor, :now)
        """), {"id": f"revision:{entity_type}:{external_id}:{revision}",
                "type": entity_type, "entity_id": row["id"],
                "summary": f"Changed {external_id} review status from {previous_status} to {review_status}",
                "excerpt": canonical[:1000], "actor": actor, "now": now})
        return payload
