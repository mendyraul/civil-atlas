"""Normalize saved SPARQL JSON bindings; dates and statements are mandatory."""

import json
import re
from hashlib import sha256
from app.ingestion.pleiades import NormalizedSnapshot
from app.schemas import HistoricalEvent, PersonRecord, OfficeTenure, CapitalRole


def dated_year(binding):
    value = binding.get("value", "")
    match = re.fullmatch(r"([+-]?\d{4,})-\d{2}-\d{2}T00:00:00Z", value)
    if not match:
        raise ValueError("unsupported or missing Wikidata timestamp")
    return int(match[1])


class WikidataAdapter:
    namespace = "wikidata"
    version = "1"
    label = "Wikidata saved SPARQL enrichment"
    license = "CC0-1.0"
    source_type = "knowledge_graph"

    def __init__(self, mapping):
        self.mapping = mapping

    def entity_ids_for(self, external_id):
        key = sha256(external_id.encode()).hexdigest()[:24]
        return [
            (kind, f"wikidata-{key}") for kind in ("offices", "capital_roles", "events")
        ]

    def normalize(self, raw, ids, dataset_version, retrieved_at):
        data = json.loads(raw)
        rows = data.get("results", {}).get("bindings")
        if not isinstance(rows, list):
            raise ValueError("expected saved SPARQL JSON results.bindings")
        datasets = {
            kind: []
            for kind in (
                "sources",
                "source_records",
                "people",
                "offices",
                "capital_roles",
                "events",
            )
        }
        source_id = f"wikidata-source-{dataset_version}"
        datasets["sources"].append(
            dict(
                id=source_id,
                source_name=self.label,
                source_type=self.source_type,
                url="https://www.wikidata.org/",
                citation=f"Wikidata SPARQL snapshot {dataset_version}, CC0.",
                license=self.license,
                dataset_version=dataset_version,
                reliability_tier="unreviewed",
                review_status="needs_review",
                retrieved_at=retrieved_at,
                created_at=retrieved_at,
                updated_at=retrieved_at,
                mapping=self.mapping,
            )
        )
        omissions = []
        seen = set()
        people = {}

        def val(row, key):
            return row.get(key, {}).get("value", "")

        def qid(value):
            if not re.fullmatch(r"https?://www.wikidata.org/entity/Q[0-9]+", value):
                raise ValueError("expected Wikidata entity URI")
            return value.rsplit("/", 1)[-1]

        for row in rows:
            statement = val(row, "statement")
            if ids and statement not in ids:
                continue
            if not re.fullmatch(
                r"https?://www.wikidata.org/entity/statement/[A-Za-z0-9$-]+", statement
            ):
                raise ValueError("each binding requires a Wikidata statement URI")
            if statement in seen:
                raise ValueError(
                    "ambiguous duplicate statement rows; retain qualifiers in separate assertions"
                )
            seen.add(statement)
            identifier = "wikidata-" + sha256(statement.encode()).hexdigest()[:24]
            record_id = identifier + "-record"
            raw_notes = json.dumps(row, sort_keys=True)
            record = dict(
                id=record_id,
                feature_id=identifier,
                feature_kind=val(row, "kind"),
                feature_label=val(row, "valueLabel"),
                title="Wikidata statement " + statement.rsplit("/", 1)[-1],
                citation=statement,
                link=statement,
                source_namespace=self.namespace,
                confidence="low",
                review_status="needs_review",
                notes=raw_notes,
            )
            datasets["source_records"].append(record)
            try:
                civ = self.mapping.get("civilizations", {}).get(
                    qid(val(row, "civilization"))
                )
                if not civ:
                    raise ValueError("civilization has no checked crosswalk")
                start, end = (
                    dated_year(row.get("start", {})),
                    dated_year(row.get("end", {})),
                )
                if start > end:
                    raise ValueError("reversed qualifier dates")
                if any(
                    int(val(row, key) or 0) < 9
                    for key in ("startPrecision", "endPrecision")
                ):
                    raise ValueError("date precision must be year or finer")
                common = dict(
                    id=identifier,
                    civilization_id=civ,
                    start_year=start,
                    end_year=end,
                    review_status="needs_review",
                    source_record_ids=[record_id],
                    source_id=source_id,
                    statement=statement,
                    qualifiers=row,
                )
                kind = val(row, "kind")
                value = qid(val(row, "value"))
                label = val(row, "valueLabel")
                if not label:
                    raise ValueError("valueLabel is required")
                if kind == "leader":
                    pid = "wikidata-person-" + value
                    people[pid] = PersonRecord(
                        id=pid,
                        name=label,
                        wikidata_id=value,
                        review_status="needs_review",
                        source_record_ids=sorted(
                            set(
                                people.get(pid, {}).get("source_record_ids", [])
                                + [record_id]
                            )
                        ),
                    ).model_dump(mode="json")
                    datasets["offices"].append(
                        OfficeTenure(
                            **common,
                            person_id=pid,
                            office=val(row, "property") or "head of state",
                        ).model_dump(mode="json")
                    )
                elif kind == "capital":
                    place = self.mapping.get("places", {}).get(value)
                    if not place:
                        raise ValueError("capital place has no checked crosswalk")
                    datasets["capital_roles"].append(
                        CapitalRole(**common, place_id=place).model_dump(mode="json")
                    )
                elif kind == "event":
                    place = (
                        self.mapping.get("places", {}).get(qid(val(row, "place")))
                        if val(row, "place")
                        else None
                    )
                    if val(row, "place") and not place:
                        raise ValueError("event place has no checked crosswalk")
                    event = HistoricalEvent(
                        id=identifier,
                        slug=identifier,
                        label=label,
                        event_type="source_reported",
                        start_year=start,
                        end_year=end,
                        display_date=f"{start}–{end}",
                        summary="Wikidata statement; review pending.",
                        impact="Not assessed",
                        civilization_ids=[civ],
                        place_ids=[place] if place else [],
                        confidence="low",
                        review_status="needs_review",
                        evidence=[],
                    ).model_dump(mode="json")
                    event.update(
                        source_record_ids=[record_id],
                        statement=statement,
                        qualifiers=row,
                        source_id=source_id,
                    )
                    datasets["events"].append(event)
                else:
                    raise ValueError("kind must be leader, capital or event")
                record.update(valid_from_year=start, valid_to_year=end)
            except (ValueError, TypeError, KeyError) as error:
                omissions.append({"id": statement, "reason": str(error)})
        datasets["people"] = list(people.values())
        omissions.extend(
            {"id": missing, "reason": "statement missing from snapshot"}
            for missing in sorted(set(ids) - seen)
        )
        return NormalizedSnapshot(
            datasets, omissions, selected_ids=sorted(seen | set(ids))
        )
