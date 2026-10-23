"""Read-only historical research. Every spatial projection is publication gated."""
from hashlib import sha256
import json
from urllib.parse import urlencode

from sqlalchemy import text
from app.db.session import session_scope
from app.schemas.toolkit import ResearchQuery
from app.services.repository import AtlasRepository

LIMITATION = "Results describe Civil Atlas coverage, not all historical activity. Boundaries are source interpretations; an empty result is not evidence of historical absence."


def atlas_link(query: ResearchQuery) -> str:
    params = {"y": query.year}
    if query.feature_id:
        params["sel"] = query.feature_id
    if query.camera:
        params.update(lng=query.camera.center[0], lat=query.camera.center[1], z=query.camera.zoom, bearing=query.camera.bearing, pitch=query.camera.pitch)
    return "/atlas?" + urlencode(params)


def public_sources(repository, feature):
    ids = set(feature.get("source_record_ids", [])) | {e["id"] for e in feature.get("evidence", [])}
    return [s for s in repository.list("source_records") if s["id"] in ids or s.get("feature_id") == feature["id"]]


def area_expression(query, repository):
    area = query.area
    if area.layer_id:
        layer = repository.get("layers", area.layer_id)
        if not layer or not layer["valid_from_year"] <= query.year <= layer["valid_to_year"]:
            raise ValueError("Historical boundary is unavailable at this date")
        if layer.get("is_placeholder") or layer.get("geometry_placeholder") or layer["review_status"] != "reviewed":
            raise ValueError("Area selection requires a reviewed, sourced boundary")
        return "ST_SetSRID(ST_GeomFromGeoJSON(:area_geometry),4326)", {"area_geometry": json.dumps(layer["geometry_json"])}
    if area.center:
        return "ST_SetSRID(ST_MakePoint(:longitude,:latitude),4326)", {"longitude": area.center[0], "latitude": area.center[1], "radius": area.radius_km * 1000}
    west, south, east, north = area.bbox
    expression = "ST_MakeEnvelope(:west,:south,:east,:north,4326)" if west < east else "ST_Union(ST_MakeEnvelope(:west,:south,180,:north,4326),ST_MakeEnvelope(-180,:south,:east,:north,4326))"
    return expression, dict(west=west, south=south, east=east, north=north)


CANDIDATES = """
SELECT a.entity_type, a.payload,
 CASE a.entity_type
 WHEN 'layers' THEN l.geom
 WHEN 'nodes' THEN p.geom
 WHEN 'routes' THEN e.geom
 WHEN 'events' THEN coalesce(ST_SetSRID(ST_GeomFromGeoJSON(nullif(a.payload->'geographic_scope','null'::jsonb)),4326),(SELECT ST_Collect(ep.geom) FROM places ep
   JOIN atlas_entities en ON en.entity_type='nodes' AND en.external_id=ep.id AND en.published=TRUE
   WHERE ep.id IN (SELECT jsonb_array_elements_text(coalesce(a.payload->'place_ids','[]'::jsonb)))
     AND ep.start_year<=:year AND ep.end_year>=:year))
 END AS geom
FROM atlas_entities a
LEFT JOIN civilization_layers l ON a.entity_type='layers' AND l.id=a.external_id
LEFT JOIN places p ON a.entity_type='nodes' AND p.id=a.external_id
LEFT JOIN civilization_edges e ON a.entity_type='routes' AND e.id=a.external_id
WHERE a.published=TRUE AND a.entity_type=ANY(:kinds)
 AND coalesce((a.payload->>'start_year')::int,(a.payload->>'valid_from_year')::int,-600)<=:year
 AND coalesce((a.payload->>'end_year')::int,(a.payload->>'valid_to_year')::int,1800)>=:year
"""


def execute_query(query: ResearchQuery):
    with session_scope() as session:
        repository = AtlasRepository(session)
        version_rows = session.execute(text("SELECT entity_type,external_id,content_hash FROM atlas_entities WHERE published=TRUE ORDER BY entity_type,external_id")).all()
        version = sha256(str(version_rows).encode()).hexdigest()[:16]
        result = {"operation": query.operation, "year": query.year, "items": [], "total": 0, "page": query.page, "page_size": query.page_size, "data_version": version, "limitations": [LIMITATION], "unlocated_count": 0}
        if query.operation == "atlas_link":
            result["items"] = [{"url": atlas_link(query)}]
        elif query.operation == "episodes":
            from app.services.episodes import public_episodes
            result["items"] = [pack.model_dump(mode="json") for pack in public_episodes(repository)]
        elif query.operation == "sources_for_feature":
            feature = next((repository.get(kind, query.feature_id) for kind in ("layers", "nodes", "routes", "events", "civilizations") if repository.get(kind, query.feature_id)), None)
            if not feature:
                raise ValueError("Published feature not found")
            result["items"] = public_sources(repository, feature)
        elif query.operation == "compare_boundaries":
            for layer_id, year in [(query.left_layer_id, query.year), (query.right_layer_id, query.right_year if query.right_year is not None else query.year)]:
                layer = repository.get("layers", layer_id)
                if not layer or not layer["valid_from_year"] <= year <= layer["valid_to_year"]:
                    raise ValueError("Comparison boundary is unavailable at the requested date")
                result["items"].append({"kind": "layers", "year": year, "record": layer, "sources": public_sources(repository, layer), "url": atlas_link(ResearchQuery(operation="atlas_link", year=year, feature_id=layer["civilization_id"]))})
        else:
            area, params = area_expression(query, repository)
            params.update(year=query.year, kinds=["events"] if query.operation == "events_in_area" else query.kinds)
            predicate = f"ST_DWithin(c.geom::geography,({area})::geography,:radius)" if query.area.center else f"ST_Intersects(c.geom,{area})"
            rows = session.execute(text(f"WITH c AS ({CANDIDATES}) SELECT entity_type,payload FROM c WHERE geom IS NOT NULL AND ST_IsValid(geom) AND {predicate} ORDER BY entity_type,payload->>'id'"), params).mappings().all()
            result["unlocated_count"] = session.execute(text(f"WITH c AS ({CANDIDATES}) SELECT count(*) FROM c WHERE geom IS NULL OR NOT ST_IsValid(geom)"), params).scalar_one()
            for row in rows:
                record = dict(row["payload"])
                result["items"].append({"kind": row["entity_type"], "record": record, "sources": public_sources(repository, record), "url": atlas_link(ResearchQuery(operation="atlas_link", year=query.year, feature_id=record.get("civilization_id", record["id"])))})
        result["total"] = len(result["items"])
        start = (query.page - 1) * query.page_size
        result["items"] = result["items"][start:start + query.page_size]
        result["summary"] = f"{result['total']} matching records in Civil Atlas for {query.year}."
        return result
