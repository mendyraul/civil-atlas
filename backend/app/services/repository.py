from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session


class AtlasRepository:
    """Database-backed repository for validated, externally identified atlas documents."""

    def __init__(self, session: Session):
        self.session = session

    def list(self, entity_type: str) -> list[dict[str, Any]]:
        rows = self.session.execute(
            text("SELECT payload FROM atlas_entities WHERE entity_type=:type ORDER BY external_id"),
            {"type": entity_type},
        )
        return [dict(row.payload) for row in rows]

    def get(self, entity_type: str, external_id: str) -> dict[str, Any] | None:
        row = self.session.execute(
            text("SELECT payload FROM atlas_entities WHERE entity_type=:type AND external_id=:id"),
            {"type": entity_type, "id": external_id},
        ).first()
        return dict(row.payload) if row else None

    def data_version(self) -> dict[str, Any]:
        row = self.session.execute(text("""
            SELECT count(*) AS entity_count, max(updated_at) AS updated_at,
                   coalesce(max(revision_number), 0) AS revision
            FROM atlas_entities
        """)).one()
        return {
            "version": f"db-r{row.revision}",
            "revision": row.revision,
            "entity_count": row.entity_count,
            "updated_at": row.updated_at,
        }

    def upsert(self, entity_type: str, external_id: str, payload: dict[str, Any], actor: str) -> str:
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
        digest = sha256(canonical.encode()).hexdigest()
        existing = self.session.execute(text("""
            SELECT id, content_hash, revision_number FROM atlas_entities
            WHERE entity_type=:type AND external_id=:external_id FOR UPDATE
        """), {"type": entity_type, "external_id": external_id}).mappings().first()
        now = datetime.now(timezone.utc)
        if existing and existing["content_hash"] == digest:
            return "duplicate"
        if existing:
            revision = existing["revision_number"] + 1
            self.session.execute(text("""
                UPDATE atlas_entities SET payload=CAST(:payload AS jsonb), content_hash=:hash,
                  revision_number=:revision, updated_at=:now WHERE id=:id
            """), {"payload": json.dumps(payload), "hash": digest, "revision": revision,
                    "now": now, "id": existing["id"]})
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
              (id, entity_type, external_id, payload, content_hash, revision_number, created_at, updated_at)
            VALUES (:id, :type, :external_id, CAST(:payload AS jsonb), :hash, 1, :now, :now)
        """), {"id": internal_id, "type": entity_type, "external_id": external_id,
                "payload": json.dumps(payload), "hash": digest, "now": now})
        return "created"
