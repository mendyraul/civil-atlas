"""Local GeoJSON adapters with explicit, archived mapping sidecars."""

import json
import math
from functools import lru_cache

from pyproj import Transformer
from pyproj.exceptions import ProjError

from app.ingestion.pleiades import NormalizedSnapshot
from app.schemas import AtlasRoute, PhysicalFeature, Source, SourceRecord


GEOMETRY_DEPTH = {
    "LineString": 1,
    "MultiLineString": 2,
    "Polygon": 2,
    "MultiPolygon": 3,
}
CRS_NAMES = {
    "EPSG:4326": "OGC:CRS84",
    "urn:ogc:def:crs:EPSG::4326": "OGC:CRS84",
    "OGC:CRS84": "OGC:CRS84",
    "urn:ogc:def:crs:OGC:1.3:CRS84": "OGC:CRS84",
    "EPSG:3395": "EPSG:3395",
    "urn:ogc:def:crs:EPSG::3395": "EPSG:3395",
    "EPSG:3857": "EPSG:3857",
    "urn:ogc:def:crs:EPSG::3857": "EPSG:3857",
}


def coordinate_tree(value, depth, convert):
    if depth == 0:
        if (
            not isinstance(value, (list, tuple))
            or len(value) not in (2, 3)
            or any(type(v) not in (int, float) or not math.isfinite(v) for v in value)
        ):
            raise ValueError("coordinates require two or three finite numbers")
        return convert(value)
    if not isinstance(value, list) or not value:
        raise ValueError("empty or malformed coordinate array")
    return [coordinate_tree(item, depth - 1, convert) for item in value]


def validate_geometry(value):
    if not isinstance(value, dict) or value.get("type") not in GEOMETRY_DEPTH:
        raise ValueError("unsupported physical geometry")

    def point(value):
        if len(value) != 2 or not (-180 <= value[0] <= 180 and -90 <= value[1] <= 90):
            raise ValueError("invalid longitude/latitude")
        return value

    coordinates = coordinate_tree(
        value.get("coordinates"), GEOMETRY_DEPTH[value["type"]], point
    )
    kind = value["type"]
    if kind == "LineString":
        lines = [coordinates]
    elif kind == "MultiPolygon":
        lines = [ring for polygon in coordinates for ring in polygon]
    else:
        lines = coordinates
    for line in lines:
        if len(line) < 2 or (
            kind in {"Polygon", "MultiPolygon"}
            and (len(line) < 4 or line[0] != line[-1])
        ):
            raise ValueError("incomplete line or ring")
    return value


@lru_cache(maxsize=4)
def coordinate_transformer(source_crs):
    return Transformer.from_crs(source_crs, "OGC:CRS84", always_xy=True)


def normalize_geometry(value, source_crs):
    if not isinstance(value, dict) or value.get("type") not in GEOMETRY_DEPTH:
        raise ValueError("unsupported physical geometry")
    transformer = coordinate_transformer(source_crs)

    def point(value):
        # Preserve the original 3D/projected geometry in the exact raw archive;
        # the atlas displays horizontal coordinates only, without simplification.
        try:
            x, y = transformer.transform(value[0], value[1], errcheck=True)
        except ProjError as error:
            raise ValueError(
                "source coordinates cannot be transformed to longitude/latitude"
            ) from error
        return [x, y]

    geometry = {
        "type": value["type"],
        "coordinates": coordinate_tree(
            value.get("coordinates"), GEOMETRY_DEPTH[value["type"]], point
        ),
    }
    return validate_geometry(geometry)


class GeographyAdapter:
    version = "2"
    source_type = "historical_gis"
    default_id_field = "id"
    default_name_field = "name"

    def __init__(self, mapping):
        if not isinstance(mapping, dict):
            raise ValueError("mapping must be a JSON object")
        self.mapping = mapping
        if (
            mapping.get("license") != self.license
            or not mapping.get("source_url")
            or not mapping.get("citation")
        ):
            raise ValueError(
                "mapping must declare the release license, source_url and citation"
            )

    def entity_ids_for(self, external_id):
        return [(self.kind, f"{self.namespace}-{external_id}")]

    def normalize(self, raw, ids, dataset_version, retrieved_at):
        data = json.loads(raw)
        if (
            not isinstance(data, dict)
            or data.get("type") != "FeatureCollection"
            or not isinstance(data.get("features"), list)
        ):
            raise ValueError("expected saved GeoJSON FeatureCollection")
        crs = data.get("crs") or {}
        if not isinstance(crs, dict) or not isinstance(crs.get("properties", {}), dict):
            raise ValueError("snapshot CRS must declare a named coordinate system")
        declared = crs.get("properties", {}).get("name")
        configured = self.mapping.get("source_crs")
        if (
            declared
            and configured
            and CRS_NAMES.get(declared) != CRS_NAMES.get(configured)
        ):
            raise ValueError("mapping source_crs conflicts with the snapshot CRS")
        source_crs = CRS_NAMES.get(declared or configured or "OGC:CRS84")
        if source_crs is None:
            raise ValueError(
                "unsupported source CRS; expected CRS84, EPSG:4326, EPSG:3395 or EPSG:3857"
            )
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate selected IDs")
        datasets = {"sources": [], "source_records": [], self.kind: []}
        source_id = f"{self.namespace}-source-{dataset_version}"
        notes = "Source-reported data; editorial review required."
        citation, url = self.mapping["citation"], self.mapping["source_url"]
        # The mapping bytes are part of the normalized manifest hash and archived with it.
        source = Source(
            id=source_id,
            source_name=self.label,
            source_type=self.source_type,
            url=url,
            citation=citation,
            license=self.license,
            dataset_version=dataset_version,
            reliability_tier="unreviewed",
            retrieved_at=retrieved_at,
            created_at=retrieved_at,
            updated_at=retrieved_at,
        ).model_dump(mode="json")
        source.update(review_status="needs_review", mapping=self.mapping)
        datasets["sources"].append(source)
        seen, omissions = set(), []
        for feature in data["features"]:
            props = feature.get("properties") or {}
            external = str(
                feature.get(
                    "id",
                    props.get(self.mapping.get("id_field", self.default_id_field), ""),
                )
            )
            if ids and external not in ids:
                continue
            if not external or external in seen:
                raise ValueError("missing or duplicate feature identifier")
            seen.add(external)
            key = f"{self.namespace}-{external}"
            mapping = self.mapping.get("features", {}).get(external, {})
            record_id = f"{key}-record"
            rec = SourceRecord(
                id=record_id,
                feature_id=key,
                feature_kind=self.kind,
                feature_label=str(
                    props.get(
                        self.mapping.get("name_field", self.default_name_field),
                        external,
                    )
                ),
                title=f"{self.label}: {external}",
                citation=citation,
                link=url,
                source_namespace=self.namespace,
                confidence="low",
                review_status="needs_review",
                notes=notes
                + " Original properties: "
                + json.dumps(props, sort_keys=True),
            ).model_dump(mode="json")
            datasets["source_records"].append(rec)
            rec["notes"] += (
                f" Normalized horizontal geometry from {source_crs} to OGC:CRS84; original coordinates and elevation remain in the raw archive."
            )
            try:
                shape = normalize_geometry(feature.get("geometry"), source_crs)
                start, end = mapping.get("start_year"), mapping.get("end_year")
                if start is not None or end is not None:
                    if (
                        type(start) is not int
                        or type(end) is not int
                        or start > end
                        or not mapping.get("date_citation")
                    ):
                        raise ValueError(
                            "dated features require ordered integer years and date_citation"
                        )
                common = dict(
                    id=key,
                    label=str(
                        props.get(
                            self.mapping.get("name_field", self.default_name_field),
                            external,
                        )
                    ),
                    confidence="low",
                    review_status="needs_review",
                    source_record_ids=[record_id],
                    source_notes=citation + " " + notes,
                    source_properties=props,
                    source_id=source_id,
                    date_citation=mapping.get("date_citation"),
                )
                if self.kind == "routes":
                    if 9999 in (start, end):
                        raise ValueError(
                            "9999 is an unknown Itiner-e date sentinel, not a historical year"
                        )
                    if start is None:
                        raise ValueError(
                            "no source-supported route dates; retained as a source record"
                        )
                    if (
                        shape["type"] == "MultiLineString"
                        and len(shape["coordinates"]) == 1
                    ):
                        shape = {
                            "type": "LineString",
                            "coordinates": shape["coordinates"][0],
                        }
                    if shape["type"] != "LineString":
                        raise ValueError(
                            "routes require a single continuous LineString"
                        )
                    if not mapping.get("source_node_id") or not mapping.get(
                        "target_node_id"
                    ):
                        raise ValueError(
                            "route endpoints require an explicit existing-node crosswalk"
                        )
                    value = AtlasRoute(
                        **{
                            k: v
                            for k, v in common.items()
                            if k in AtlasRoute.model_fields
                        },
                        slug=key,
                        kind="route",
                        route_kind="road",
                        edge_type="road",
                        source_node_id=mapping["source_node_id"],
                        target_node_id=mapping["target_node_id"],
                        civilization_ids=mapping.get("civilization_ids", []),
                        start_year=start,
                        end_year=end,
                        summary="Source-reported Roman road segment.",
                        path=shape["coordinates"],
                        status_badges=["Needs review"],
                        evidence=[],
                    ).model_dump(mode="json")
                    value.update({k: v for k, v in common.items() if k not in value})
                else:
                    value = PhysicalFeature(
                        **common,
                        geometry=shape,
                        start_year=start,
                        end_year=end,
                        feature_type=mapping.get(
                            "feature_type",
                            self.mapping.get("feature_type", "physical_geography"),
                        ),
                    ).model_dump(mode="json")
                rec.update(valid_from_year=start, valid_to_year=end)
                if mapping.get("date_citation"):
                    rec["notes"] += " Date evidence: " + mapping["date_citation"]
                datasets[self.kind].append(value)
            except (ValueError, TypeError, KeyError) as error:
                omissions.append({"id": external, "reason": str(error)})
        omissions.extend(
            {"id": missing, "reason": "selected feature absent"}
            for missing in sorted(set(ids) - seen)
        )
        return NormalizedSnapshot(
            datasets, omissions, selected_ids=sorted(seen | set(ids))
        )


class ItinereAdapter(GeographyAdapter):
    default_id_field = "InLine_FID"
    default_name_field = "Name"
    namespace = "itinere"
    label = "Itiner-e Roman roads"
    license = "CC-BY-4.0"
    kind = "routes"


class AWMCAdapter(GeographyAdapter):
    default_id_field = "OBJECTID"
    default_name_field = "TITLE"
    namespace = "awmc"
    label = "Ancient World Mapping Center physical geography"
    license = "ODbL-1.0"
    kind = "physical_features"
