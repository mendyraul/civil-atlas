"""Pure Pleiades JSON normalization; no network, filesystem, or database writes."""

from dataclasses import dataclass
import gzip
import json
import math
import re
from typing import Any, Protocol

from app.schemas import EvidenceLink, Place, Source, SourceRecord

LICENSE = "https://creativecommons.org/licenses/by/3.0/"
RATIONALE = (
    "Low confidence pending editorial review. Coordinates are the source's "
    "representative point, not a surveyed boundary. Dates describe explicit "
    "source intervals, not independently verified continuous occupation."
)


@dataclass
class NormalizedSnapshot:
    datasets: dict[str, list[dict[str, Any]]]
    omissions: list[dict[str, str]]


class SourceAdapter(Protocol):
    namespace: str
    version: str

    def normalize(
        self, raw: bytes, place_ids: list[str], dataset_version: str, retrieved_at: str
    ) -> NormalizedSnapshot: ...


def _dates(record: dict[str, Any]) -> tuple[int, int] | None:
    def interval(value: dict[str, Any]) -> tuple[int, int] | None:
        start, end = value.get("start"), value.get("end")
        if type(start) is int and type(end) is int and start <= end:
            return start, end
        return None

    if "start" in record or "end" in record:
        return interval(record)
    locations = record.get("locations", [])
    if not isinstance(locations, list):
        raise ValueError("locations must be an array")
    intervals = []
    for location in locations:
        if not isinstance(location, dict):
            raise ValueError("each location must be an object")
        if location.get("review_state") == "published":
            dates = interval(location)
            if dates is None:
                return None
            intervals.append(dates)
    if not intervals:
        return None
    intervals.sort()
    start, end = intervals[0]
    for next_start, next_end in intervals[1:]:
        if next_start > end + 1:
            return None  # A single Place interval cannot represent a gap honestly.
        end = max(end, next_end)
    return start, end


def _point(record: dict[str, Any]) -> tuple[float, float] | None:
    point = record.get("reprPoint")
    if not isinstance(point, list) or len(point) != 2:
        return None
    if any(type(v) not in (int, float) or not math.isfinite(v) for v in point):
        return None
    lon, lat = point
    return (lon, lat) if -180 <= lon <= 180 and -90 <= lat <= 90 else None


class PleiadesAdapter:
    namespace = "pleiades"
    version = "1"

    def normalize(
        self, raw: bytes, place_ids: list[str], dataset_version: str, retrieved_at: str
    ) -> NormalizedSnapshot:
        if not place_ids or len(set(place_ids)) != len(place_ids):
            raise ValueError("select at least one place ID without duplicates")
        if any(not re.fullmatch(r"[0-9]+", pid) for pid in place_ids):
            raise ValueError("Pleiades IDs must contain digits only")
        try:
            data = json.loads(gzip.decompress(raw) if raw.startswith(b"\x1f\x8b") else raw)
        except (ValueError, OSError, EOFError) as error:
            raise ValueError("snapshot must be valid JSON or gzip-compressed JSON") from error
        # Comprehensive dumps contain a @graph; place endpoints return one object.
        records = data.get("@graph") if isinstance(data, dict) and "@graph" in data else data
        if isinstance(records, dict) and "id" in records:
            records = [records]
        if not isinstance(records, list) or any(not isinstance(r, dict) for r in records):
            raise ValueError("expected a Pleiades place object, array, or @graph dump")
        selected = {}
        for record in records:
            pid = str(record.get("id", ""))
            if pid in place_ids:
                if pid in selected:
                    raise ValueError(f"duplicate external identifier: {pid}")
                selected[pid] = record
        missing = set(place_ids) - selected.keys()
        if missing:
            raise ValueError(f"selected IDs missing from snapshot: {', '.join(sorted(missing))}")

        datasets: dict[str, list[dict[str, Any]]] = {
            "sources": [], "source_records": [], "places": [], "evidence": [],
        }
        omissions = []
        for pid, record in sorted(selected.items()):
            title = record.get("title")
            if not isinstance(title, str) or not title.strip():
                raise ValueError(f"{pid}: title is required")
            rights = record.get("rights")
            if not isinstance(rights, str) or not rights.strip():
                raise ValueError(f"{pid}: source rights statement is required")
            if "Creative Commons Attribution 3.0" not in rights and LICENSE not in rights:
                raise ValueError(f"{pid}: unsupported license; review source rights before importing")
            uri = f"https://pleiades.stoa.org/places/{pid}"
            source_uri = record.get("uri", uri)
            if not isinstance(source_uri, str) or source_uri.replace("http://", "https://").rstrip("/") != uri:
                raise ValueError(f"{pid}: canonical URI does not match identifier")
            identifier = f"pleiades-{pid}"
            source_id = f"pleiades-source-{pid}"
            record_id = f"pleiades-record-{pid}"
            creators, contributors = record.get("creators", []), record.get("contributors", [])
            if not isinstance(creators, list) or not isinstance(contributors, list):
                raise ValueError(f"{pid}: creators and contributors must be arrays")
            names = sorted({p["name"] for p in creators + contributors
                            if isinstance(p, dict) and isinstance(p.get("name"), str) and p["name"]})
            citation = f"{'; '.join(names) or 'Pleiades contributors'}. {title}. Pleiades {pid}. {uri}. {rights}"
            dates, point = _dates(record), _point(record)
            reasons = []
            if record.get("review_state") != "published":
                reasons.append("source is not published")
            if dates is None:
                reasons.append("no explicit continuous valid date interval")
            if point is None:
                reasons.append("no valid representative coordinates")
            if reasons:
                omissions.append({"id": pid, "reason": "; ".join(reasons)})
            source = Source(
                id=source_id, source_name=f"Pleiades: {title}", source_type="gazetteer",
                external_id=pid, url=uri, citation=citation, license=LICENSE,
                dataset_version=dataset_version, reliability_tier="unreviewed",
                retrieved_at=retrieved_at, created_at=retrieved_at, updated_at=retrieved_at,
            ).model_dump(mode="json")
            source["review_status"] = "needs_review"
            datasets["sources"].append(source)
            source_record = SourceRecord(
                id=record_id, feature_id=identifier if not reasons else source_id,
                feature_kind="place" if not reasons else "source", feature_label=title,
                title=title, citation=citation, link=uri, source_namespace=self.namespace,
                confidence="low", review_status="needs_review",
                notes=RATIONALE + (" Place omitted: " + "; ".join(reasons) if reasons else ""),
                valid_from_year=dates[0] if dates else None,
                valid_to_year=dates[1] if dates else None,
            ).model_dump(mode="json")
            datasets["source_records"].append(source_record)
            if reasons:
                continue
            assert dates is not None and point is not None
            types = record.get("placeTypes", [])
            if not isinstance(types, list) or any(not isinstance(t, str) for t in types):
                raise ValueError(f"{pid}: placeTypes must be an array of strings")
            place = Place(
                id=identifier, slug=identifier, canonical_name=title,
                latitude=point[1], longitude=point[0], start_year=dates[0], end_year=dates[1],
                place_type=types[0] if len(types) == 1 else "place",
                confidence_level="low", review_status="needs_review",
                created_at=retrieved_at, updated_at=retrieved_at,
            ).model_dump(mode="json")
            place["source_record_ids"] = [record_id]
            datasets["places"].append(place)
            evidence = EvidenceLink(
                id=f"pleiades-evidence-{pid}", source_id=source_id, entity_type="place",
                entity_id=identifier, claim_type="location_and_time", confidence_level="low",
                quote_or_note=RATIONALE, created_at=retrieved_at, updated_at=retrieved_at,
            ).model_dump(mode="json")
            evidence["review_status"] = "needs_review"
            datasets["evidence"].append(evidence)
        return NormalizedSnapshot(datasets, omissions)
