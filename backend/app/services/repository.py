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
        preserve_published: bool = False,
    ) -> str:
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
        digest = sha256(canonical.encode()).hexdigest()
        existing = self.session.execute(text("""
            SELECT id, content_hash, published, revision_number FROM atlas_entities
            WHERE entity_type=:type AND external_id=:external_id FOR UPDATE
        """), {"type": entity_type, "external_id": external_id}).mappings().first()
        now = datetime.now(timezone.utc)
        desired_published = bool(existing["published"]) if existing and preserve_published else published
        if existing and existing["content_hash"] == digest and existing["published"] == desired_published:
            return "duplicate"
        if existing:
            revision = existing["revision_number"] + 1
            self.session.execute(text("""
                UPDATE atlas_entities SET payload=CAST(:payload AS jsonb), content_hash=:hash,
                  published=:published, revision_number=:revision, updated_at=:now WHERE id=:id
            """), {"payload": json.dumps(payload), "hash": digest, "revision": revision,
                    "published": desired_published, "now": now, "id": existing["id"]})
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

    def upsert_spatial_projection(self, entity_type: str, record: dict[str, Any]) -> None:
        """Project map records into typed PostGIS tables for spatial queries.

        ``atlas_entities`` remains the canonical publication-gated document
        store. These tables are a deterministic query projection, rebuilt by
        the same versioned import, so spatial SQL does not have to parse JSONB
        for every request.
        """
        if entity_type == "civilizations":
            self.session.execute(text("""
                INSERT INTO civilizations
                  (id, slug, name, type, start_year, end_year, description,
                   display_color, confidence_level, review_status, created_at, updated_at)
                VALUES (:id, :slug, :name, :type, :start_year, :end_year, :description,
                        :display_color, :confidence_level, :review_status,
                        coalesce(CAST(:created_at AS timestamptz), now()),
                        coalesce(CAST(:updated_at AS timestamptz), now()))
                ON CONFLICT (id) DO UPDATE SET
                  slug=excluded.slug, name=excluded.name, type=excluded.type,
                  start_year=excluded.start_year, end_year=excluded.end_year,
                  description=excluded.description, display_color=excluded.display_color,
                  confidence_level=excluded.confidence_level, review_status=excluded.review_status,
                  updated_at=excluded.updated_at
            """), {
                "id": str(record["id"]), "slug": str(record.get("slug", record["id"])),
                "name": str(record.get("display_name", record.get("label", record["id"]))),
                "type": str(record.get("civilization_type", "unknown")),
                "start_year": int(record["start_year"]), "end_year": int(record["end_year"]),
                "description": str(record.get("summary", "")),
                "display_color": str(record.get("color", "#64748b")),
                "confidence_level": str(record.get("confidence", "medium")),
                "review_status": str(record.get("review_status", "needs_review")),
                "created_at": record.get("created_at"), "updated_at": record.get("updated_at"),
            })
        elif entity_type == "layers":
            geometry = json.dumps(record["geometry_json"])
            self.session.execute(text("""
                INSERT INTO civilization_layers
                  (id, civilization_id, name, layer_type, variant_group,
                   interpretation_label, interpretation_kind, is_primary, display_order,
                   valid_from_year, valid_to_year, geometry_json, geom, geometry_placeholder,
                   is_placeholder, confidence_level, review_status, source_note,
                   created_at, updated_at)
                VALUES (:id, :civilization_id, :name, :layer_type, :variant_group,
                        :interpretation_label, :interpretation_kind, :is_primary, :display_order,
                        :valid_from_year, :valid_to_year, CAST(:geometry_json AS jsonb),
                        ST_SetSRID(ST_GeomFromGeoJSON(:geometry_json), 4326), :geometry_placeholder,
                        :is_placeholder, :confidence_level, :review_status, :source_note,
                        coalesce(CAST(:created_at AS timestamptz), now()),
                        coalesce(CAST(:updated_at AS timestamptz), now()))
                ON CONFLICT (id) DO UPDATE SET
                  civilization_id=excluded.civilization_id, name=excluded.name,
                  layer_type=excluded.layer_type, variant_group=excluded.variant_group,
                  interpretation_label=excluded.interpretation_label,
                  interpretation_kind=excluded.interpretation_kind,
                  is_primary=excluded.is_primary, display_order=excluded.display_order,
                  valid_from_year=excluded.valid_from_year, valid_to_year=excluded.valid_to_year,
                  geometry_json=excluded.geometry_json, geom=excluded.geom,
                  geometry_placeholder=excluded.geometry_placeholder,
                  is_placeholder=excluded.is_placeholder, confidence_level=excluded.confidence_level,
                  review_status=excluded.review_status, source_note=excluded.source_note,
                  updated_at=excluded.updated_at
            """), {
                "id": str(record["id"]), "civilization_id": str(record["civilization_id"]),
                "name": str(record["name"]), "layer_type": str(record["layer_type"]),
                "variant_group": record.get("variant_group"),
                "interpretation_label": record.get("interpretation_label"),
                "interpretation_kind": record.get("interpretation_kind"),
                "is_primary": bool(record.get("is_primary", False)),
                "display_order": int(record.get("display_order", 0)),
                "valid_from_year": int(record["valid_from_year"]),
                "valid_to_year": int(record["valid_to_year"]), "geometry_json": geometry,
                "geometry_placeholder": record.get("geometry_placeholder"),
                "is_placeholder": bool(record.get("is_placeholder", False)),
                "confidence_level": str(record.get("confidence", "medium")),
                "review_status": str(record.get("review_status", "needs_review")),
                "source_note": str(record.get("source_note", "")),
                "created_at": record.get("created_at"), "updated_at": record.get("updated_at"),
            })
        elif entity_type == "nodes":
            longitude, latitude = record["coordinates"]
            self.session.execute(text("""
                INSERT INTO places
                  (id, slug, canonical_name, modern_name, latitude, longitude, geom,
                   start_year, end_year, place_type, confidence_level, review_status,
                   created_at, updated_at)
                VALUES (:id, :slug, :canonical_name, :modern_name, :latitude, :longitude,
                        ST_SetSRID(ST_MakePoint(:longitude, :latitude), 4326),
                        :start_year, :end_year, :place_type, :confidence_level, :review_status,
                        coalesce(CAST(:created_at AS timestamptz), now()),
                        coalesce(CAST(:updated_at AS timestamptz), now()))
                ON CONFLICT (id) DO UPDATE SET
                  slug=excluded.slug, canonical_name=excluded.canonical_name,
                  modern_name=excluded.modern_name, latitude=excluded.latitude,
                  longitude=excluded.longitude, geom=excluded.geom, start_year=excluded.start_year,
                  end_year=excluded.end_year, place_type=excluded.place_type,
                  confidence_level=excluded.confidence_level, review_status=excluded.review_status,
                  updated_at=excluded.updated_at
            """), {
                "id": str(record["id"]), "slug": str(record.get("slug", record["id"])),
                "canonical_name": str(record.get("name", record.get("label", record["id"]))),
                "modern_name": record.get("modern_name"), "latitude": float(latitude),
                "longitude": float(longitude), "start_year": int(record["start_year"]),
                "end_year": int(record["end_year"]),
                "place_type": str(record.get("place_type", record.get("node_kind", "place"))),
                "confidence_level": str(record.get("confidence", "medium")),
                "review_status": str(record.get("review_status", "needs_review")),
                "created_at": record.get("created_at"), "updated_at": record.get("updated_at"),
            })
        elif entity_type in {"edges", "routes"}:
            civilization_id = record.get("civilization_id")
            if entity_type == "routes":
                civilization_ids = record.get("civilization_ids") or []
                civilization_id = civilization_ids[0] if civilization_ids else None
            if not civilization_id:
                return
            source_place_id = record.get("source_place_id", record.get("source_node_id"))
            target_place_id = record.get("target_place_id", record.get("target_node_id"))
            path = record.get("path")
            path_json = json.dumps({"type": "LineString", "coordinates": path}) if path and len(path) >= 2 else None
            self.session.execute(text("""
                INSERT INTO civilization_edges
                  (id, civilization_id, source_place_id, target_place_id,
                   valid_from_year, valid_to_year, edge_type, estimated_travel_days_min,
                   estimated_travel_days_max, confidence_level, review_status, source_note,
                   path_geojson, geom)
                VALUES (:id, :civilization_id, :source_place_id, :target_place_id,
                        :valid_from_year, :valid_to_year, :edge_type, :estimated_travel_days_min,
                        :estimated_travel_days_max, :confidence_level, :review_status, :source_note,
                        CAST(:path_geojson AS jsonb),
                        CASE WHEN :path_geojson IS NULL THEN NULL
                             ELSE ST_SetSRID(ST_GeomFromGeoJSON(:path_geojson), 4326) END)
                ON CONFLICT (id) DO UPDATE SET
                  civilization_id=excluded.civilization_id, source_place_id=excluded.source_place_id,
                  target_place_id=excluded.target_place_id, valid_from_year=excluded.valid_from_year,
                  valid_to_year=excluded.valid_to_year, edge_type=excluded.edge_type,
                  estimated_travel_days_min=excluded.estimated_travel_days_min,
                  estimated_travel_days_max=excluded.estimated_travel_days_max,
                  confidence_level=excluded.confidence_level, review_status=excluded.review_status,
                  source_note=excluded.source_note,
                  path_geojson=coalesce(excluded.path_geojson, civilization_edges.path_geojson),
                  geom=coalesce(excluded.geom, civilization_edges.geom)
            """), {
                "id": str(record["id"]), "civilization_id": str(civilization_id),
                "source_place_id": str(source_place_id), "target_place_id": str(target_place_id),
                "valid_from_year": int(
                    record["valid_from_year"] if "valid_from_year" in record else record["start_year"]
                ),
                "valid_to_year": int(
                    record["valid_to_year"] if "valid_to_year" in record else record["end_year"]
                ),
                "edge_type": str(record["edge_type"]),
                "estimated_travel_days_min": record.get("estimated_travel_days_min"),
                "estimated_travel_days_max": record.get("estimated_travel_days_max"),
                "confidence_level": str(record.get("confidence_level", record.get("confidence", "medium"))),
                "review_status": str(record.get("review_status", "needs_review")),
                "source_note": str(record.get("source_note", "")), "path_geojson": path_json,
            })

    def spatial_layers(self, year: int) -> dict[str, Any]:
        """Return the public, time-active layer projection as GeoJSON."""
        rows = self.session.execute(text("""
            SELECT l.id, l.civilization_id, l.name, l.layer_type, l.variant_group,
                   l.interpretation_label, l.interpretation_kind, l.is_primary,
                   l.display_order, l.valid_from_year, l.valid_to_year,
                   l.confidence_level, l.review_status, l.source_note,
                   ST_AsGeoJSON(l.geom) AS geometry
            FROM civilization_layers AS l
            JOIN atlas_entities AS a
              ON a.entity_type = 'layers' AND a.external_id = l.id AND a.published = TRUE
            WHERE l.valid_from_year <= :year AND l.valid_to_year >= :year
            ORDER BY l.display_order, l.id
        """), {"year": year}).mappings()
        features = []
        for row in rows:
            geometry = json.loads(row["geometry"]) if row["geometry"] else None
            properties = {key: row[key] for key in (
                "id", "civilization_id", "name", "layer_type", "variant_group",
                "interpretation_label", "interpretation_kind", "is_primary", "display_order",
                "valid_from_year", "valid_to_year", "confidence_level", "review_status", "source_note"
            )}
            features.append({"type": "Feature", "id": row["id"], "geometry": geometry, "properties": properties})
        return {"type": "FeatureCollection", "year": year, "features": features}

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
