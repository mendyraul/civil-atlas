"""Saved Overpass boundary adapter. No network calls or automatic publication."""

import json
import gzip
import re
import calendar
from pathlib import Path

from shapely.geometry import shape
from shapely.validation import explain_validity

from app.ingestion.pleiades import NormalizedSnapshot
from app.schemas import (
    CivilizationLayer,
    HistoricalClaim,
    Source,
    SourceRecord,
    EvidenceLink,
)


DEFAULT_CROSSWALK = (
    Path(__file__).resolve().parents[2] / "data/imports/crosswalks/ohm-world117.json"
)


def parsed_date(value):
    match = (
        re.fullmatch(r"(-?\d{1,6})(?:-(\d{2})(?:-(\d{2}))?)?", value)
        if isinstance(value, str)
        else None
    )
    if not match:
        raise ValueError("explicit start_date and end_date required")
    iso_year = int(match[1])
    month = int(match[2]) if match[2] else None
    day = int(match[3]) if match[3] else None
    if month is not None and not 1 <= month <= 12:
        raise ValueError("invalid source date month")
    if day is not None and not 1 <= day <= calendar.monthrange(iso_year, month)[1]:
        raise ValueError("invalid source date day")
    return iso_year, month, day


def historical_year(iso_year):
    # OHM's proleptic Gregorian year 0000 is 1 BCE; atlas BCE years are negative.
    return iso_year if iso_year > 0 else iso_year - 1


def date_interval(start_value, end_value):
    start = parsed_date(start_value)
    end = parsed_date(end_value)
    lower = (start[0], start[1] or 1, start[2] or 1)
    upper = (
        end[0],
        end[1] or 12,
        end[2] or calendar.monthrange(end[0], end[1] or 12)[1],
    )
    if lower > upper:
        raise ValueError("reversed date interval")
    end_year = end[0] - (1 if end[1:] == (1, 1) else 0)
    return historical_year(start[0]), historical_year(end_year)


def rings(members, role):
    segments = []
    for member in members:
        if (member.get("role") or "outer") != role:
            continue
        if member.get("type") != "way" or not member.get("geometry"):
            raise ValueError("incomplete or nested relation member")
        segments.append([[point["lon"], point["lat"]] for point in member["geometry"]])
    result = [segment for segment in segments if segment[0] == segment[-1]]
    segments = [segment for segment in segments if segment[0] != segment[-1]]
    while segments:
        ring = segments.pop(0)
        while ring[0] != ring[-1]:
            matches = [
                (i, reverse)
                for i, segment in enumerate(segments)
                for reverse in (False, True)
                if (segment[-1] if reverse else segment[0]) == ring[-1]
            ]
            if len(matches) != 1:
                raise ValueError("incomplete or ambiguous boundary rings")
            index, reverse = matches[0]
            segment = segments.pop(index)
            ring.extend((segment[::-1] if reverse else segment)[1:])
        if len(ring) < 4:
            raise ValueError("boundary ring requires three vertices")
        result.append(ring)
    return result


def contains(ring, point):
    x, y = point
    inside = False
    for a, b in zip(ring, ring[1:]):
        if (a[1] > y) != (b[1] > y) and x < (b[0] - a[0]) * (y - a[1]) / (
            b[1] - a[1]
        ) + a[0]:
            inside = not inside
    return inside


def geometry(members):
    members = [
        m
        for m in members
        if not (m.get("type") == "node" and m.get("role") in {"admin_centre", "label"})
    ]
    if any((m.get("role") or "outer") not in {"outer", "inner"} for m in members):
        raise ValueError("unsupported relation member role")
    polygons = [[outer] for outer in rings(members, "outer")]
    if not polygons:
        raise ValueError("no complete outer boundary")
    for hole in rings(members, "inner"):
        parents = [
            p for p in polygons if all(contains(p[0], point) for point in hole[:-1])
        ]
        if len(parents) != 1:
            raise ValueError("hole has no unique containing outer boundary")
        parents[0].append(hole)
    result = {"type": "MultiPolygon", "coordinates": polygons}
    if not shape(result).is_valid:
        raise ValueError(
            "invalid boundary topology: " + explain_validity(shape(result))
        )
    return result


class OHMAdapter:
    namespace = "ohm"
    version = "2"
    label = "OpenHistoricalMap boundaries"
    license = "https://creativecommons.org/publicdomain/zero/1.0/"
    source_type = "historical_gis"

    def __init__(self, selected_year, crosswalk=None):
        self.year = selected_year
        self.crosswalk = (
            crosswalk
            if crosswalk is not None
            else json.loads(DEFAULT_CROSSWALK.read_text())
        )
        if not isinstance(self.crosswalk, dict) or any(
            not re.fullmatch(r"Q[0-9]+|relation/[0-9]+", key)
            or not isinstance(value, dict)
            or not all(
                isinstance(value.get(field), str) and value[field].strip()
                for field in ("civilization_id", "variant_group")
            )
            for key, value in self.crosswalk.items()
        ):
            raise ValueError(
                "OHM crosswalk requires QID/relation keys and civilization/variant-group mappings"
            )

    def entity_ids_for(self, external_id):
        return [("layers", f"ohm-relation-{external_id}")]

    def normalize(self, raw, ids, dataset_version, retrieved_at):
        try:
            data = json.loads(
                gzip.decompress(raw) if raw.startswith(b"\x1f\x8b") else raw
            )
        except (ValueError, OSError, EOFError) as error:
            raise ValueError("expected saved Overpass JSON or gzip snapshot") from error
        if not isinstance(data, dict) or not isinstance(data.get("elements"), list):
            raise ValueError("expected saved Overpass JSON with elements")
        if len(ids) != len(set(ids)) or any(
            not re.fullmatch(r"\d+", value) for value in ids
        ):
            raise ValueError("select unique numeric relation IDs")
        datasets = {
            k: [] for k in ("sources", "source_records", "claims", "layers", "evidence")
        }
        omissions, seen = [], set()
        source_id = f"ohm-source-{dataset_version}"
        citation = (
            f"OpenHistoricalMap saved Overpass snapshot {dataset_version}, CC0 1.0."
        )
        datasets["sources"].append(
            {
                **Source(
                    id=source_id,
                    source_name=self.label,
                    source_type=self.source_type,
                    url="https://www.openhistoricalmap.org/",
                    citation=citation,
                    license=self.license,
                    dataset_version=dataset_version,
                    reliability_tier="unreviewed",
                    retrieved_at=retrieved_at,
                    created_at=retrieved_at,
                    updated_at=retrieved_at,
                ).model_dump(mode="json"),
                "review_status": "needs_review",
                "mapping": self.crosswalk,
            }
        )
        for relation in data["elements"]:
            if relation.get("type") != "relation":
                continue
            rid = str(relation["id"])
            if ids and rid not in ids:
                continue
            if rid in seen:
                raise ValueError(f"duplicate relation {rid}")
            seen.add(rid)
            tags = relation.get("tags", {})
            try:
                if "license" in tags:
                    raise ValueError(
                        "individual license override requires separate clearance"
                    )
                start, end = date_interval(tags.get("start_date"), tags.get("end_date"))
                if start > end:
                    raise ValueError("reversed date interval")
                if not start <= self.year <= end:
                    raise ValueError("relation inactive in selected year")
                qid = tags.get("wikidata")
                target = self.crosswalk.get(qid) or self.crosswalk.get(
                    f"relation/{rid}"
                )
                if not target:
                    raise ValueError("no checked civilization crosswalk")
                if (
                    target.get("expected_wikidata")
                    and qid != target["expected_wikidata"]
                ):
                    raise ValueError(
                        "relation Wikidata identity differs from the checked crosswalk"
                    )
                if (
                    target.get("expected_name")
                    and tags.get(target.get("name_tag", "name"))
                    != target["expected_name"]
                ):
                    raise ValueError("relation name differs from the checked crosswalk")
                shape = geometry(relation.get("members", []))
                layer_id, record_id, claim_id = (
                    f"ohm-relation-{rid}",
                    f"ohm-record-{rid}",
                    f"ohm-claim-{rid}",
                )
                link = f"https://www.openhistoricalmap.org/relation/{rid}"
                notes = (
                    "Source-reported boundary; review required. Source tags: "
                    + json.dumps(tags, sort_keys=True)
                )
                record = SourceRecord(
                    id=record_id,
                    feature_id=layer_id,
                    feature_kind="civilization_layer",
                    feature_label=tags.get("name", rid),
                    title=f"OHM relation {rid}",
                    citation=citation + " " + link,
                    link=link,
                    source_namespace=self.namespace,
                    confidence="low",
                    review_status="needs_review",
                    notes=notes,
                    valid_from_year=start,
                    valid_to_year=end,
                ).model_dump(mode="json")
                record["source_id"] = source_id
                claim = HistoricalClaim(
                    id=claim_id,
                    claim_type="supports_boundary",
                    predicate="territorial_extent",
                    subject_id=layer_id,
                    subject_kind="civilization_layer",
                    object_id=target["civilization_id"],
                    object_kind="civilization",
                    source_id=source_id,
                    citation_locator=link,
                    confidence_rationale=notes,
                    confidence="low",
                    review_status="needs_review",
                    notes=notes,
                    valid_from_year=start,
                    valid_to_year=end,
                    source_record_ids=[record_id],
                ).model_dump(mode="json")
                layer = CivilizationLayer(
                    id=layer_id,
                    civilization_id=target["civilization_id"],
                    name=tags.get("name", f"OHM relation {rid}"),
                    layer_type="source_reported_extent",
                    variant_group=target["variant_group"],
                    interpretation_kind="boundary_variant",
                    interpretation_label=f"OpenHistoricalMap relation {rid}",
                    is_primary=False,
                    display_order=20,
                    valid_from_year=start,
                    valid_to_year=end,
                    geometry_json=shape,
                    is_placeholder=False,
                    confidence="low",
                    review_status="needs_review",
                    source_note=notes,
                    created_at=retrieved_at,
                    updated_at=retrieved_at,
                    source_record_ids=[record_id],
                    claim_ids=[claim_id],
                ).model_dump(mode="json")
                evidence = {
                    **EvidenceLink(
                        id=f"ohm-evidence-{rid}",
                        source_id=source_id,
                        entity_type="civilization_layer",
                        entity_id=layer_id,
                        claim_type="supports_boundary",
                        confidence_level="low",
                        quote_or_note=notes,
                        created_at=retrieved_at,
                        updated_at=retrieved_at,
                    ).model_dump(mode="json"),
                    "review_status": "needs_review",
                }
                for kind, value in [
                    ("source_records", record),
                    ("claims", claim),
                    ("layers", layer),
                    ("evidence", evidence),
                ]:
                    datasets[kind].append(value)
            except (ValueError, KeyError, TypeError) as error:
                omissions.append({"id": rid, "reason": str(error)})
        for missing in sorted(set(ids) - seen):
            omissions.append(
                {"id": missing, "reason": "selected relation missing from snapshot"}
            )
        return NormalizedSnapshot(
            datasets, omissions, selected_ids=sorted(seen | set(ids))
        )
